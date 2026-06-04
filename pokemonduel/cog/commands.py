from pathlib import Path
import asyncio
import aiohttp
import json
import logging
import discord
from discord.ext import commands

from ..config import EnhancedConfigManager
from ..battle.battle import Battle
from ..ui import DuelAcceptView
from ..pokemon import DuelPokemon, create
from ..data_gen import generate_team_preview, find, find_one
from ..trainers import MemberTrainer
from ..trainers.npc_trainer import NPCTrainer
from ..ai import NPCTeamAI, reload_network


class TeambuilderReadException(Exception):
    """Generic exception raised when failing to parse a teambuilder export string."""
    pass


class PokemonDuel(commands.Cog):
    """Battle in a Pokemon Duel with another member of your server."""
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger('red.flamecogs.pokemonduel')
        self.games = {}
        self.config = EnhancedConfigManager.get_conf(self, identifier=145519400223506432)
        self.config.register_member(party=[])
        self.config.register_guild(useThreads=False)

    # ──────────────────────────────────────────────────────────────────
    #  Teambuilder parsing (unchanged)
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    async def party_from_teambuilder(ctx, teambuilder):
        teambuilder = teambuilder.strip()
        party = []
        for raw in teambuilder.split("\n\n"):
            raw = raw.strip()
            lines = raw.split("\n")
            nameraw = lines.pop(0)
            item = "None"
            if "@" in nameraw:
                nameraw, item = nameraw.split("@")
                item = item.strip().replace(" ", "-").lower()
            gender = "-m"
            if "(M)" in nameraw:
                nameraw = nameraw.replace("(M)", "")
                gender = "-m"
            elif "(F)" in nameraw:
                nameraw = nameraw.replace("(F)", "")
                gender = "-f"
            nick = "None"
            if "(" in nameraw:
                nick, nameraw = nameraw.split("(")
                nameraw = nameraw.strip()[:-1]
                nick = nick.strip()
            pokname = nameraw.strip().replace(" ", "-").capitalize()
            forms = await find_one(ctx, "forms", {"identifier": pokname.lower()})
            if forms is None:
                raise TeambuilderReadException(f"`{pokname}` is not a valid pokemon.")
            pfile = await find_one(ctx, "pfile", {"id": forms["base_id"]})
            if pfile is None:
                raise TeambuilderReadException(f"Could not find a `pfile` entry for `{pokname}`. Please report this bug.")
            gender_rate = pfile["gender_rate"]
            if gender_rate == 0:
                gender = "-m"
            elif gender_rate == 8:
                gender = "-f"
            elif gender_rate == -1:
                gender = "-x"
            hpiv = atkiv = defiv = spatkiv = spdefiv = speediv = 31
            hpev = atkev = defev = spatkev = spdefev = speedev = 0
            level = 100
            happiness = 255
            ability_index = 0
            shiny = False
            nature = "Hardy"
            moves = []
            for line in lines:
                line = line.strip()
                if line.startswith("IVs:"):
                    line = line[4:].strip()
                    for iv in line.split("/"):
                        amount, iv = iv.strip().split(" ")
                        amount = int(amount); iv = iv.lower()
                        if iv == "hp": hpiv = amount
                        elif iv == "atk": atkiv = amount
                        elif iv == "def": defiv = amount
                        elif iv == "spa": spatkiv = amount
                        elif iv == "spd": spdefiv = amount
                        elif iv == "spe": speediv = amount
                elif line.startswith("EVs:"):
                    line = line[4:].strip()
                    for ev in line.split("/"):
                        amount, ev = ev.strip().split(" ")
                        amount = int(amount); ev = ev.lower()
                        if ev == "hp": hpev = amount
                        elif ev == "atk": atkev = amount
                        elif ev == "def": defev = amount
                        elif ev == "spa": spatkev = amount
                        elif ev == "spd": spdefev = amount
                        elif ev == "spe": speedev = amount
                elif line.startswith("Shiny:") and "Yes" in line:
                    shiny = True
                elif line.startswith("Level:"):
                    level = int(line[6:].strip())
                elif line.startswith("Happiness:"):
                    happiness = int(line[10:].strip())
                elif line.endswith("Nature"):
                    nature = line[:-6].strip().capitalize()
                elif line.startswith("Ability:"):
                    ability = line[8:].strip().lower().replace(" ", "-")
                    ability_raw = await find_one(ctx, "abilities", {"identifier": ability})
                    if ability_raw is None:
                        raise TeambuilderReadException(f"`{pokname}` was given an ability `{ability}` which does not exist.")
                    ability_id = ability_raw["id"]
                    abilities = await find(ctx, "poke_abilities", {"pokemon_id": forms["pokemon_id"]})
                    abilities = [a["ability_id"] for a in abilities]
                    if ability_id not in abilities:
                        raise TeambuilderReadException(f"`{pokname}` can not have the ability `{ability}`.")
                    ability_index = abilities.index(ability_id)
                elif line.startswith("-"):
                    line = line[1:].split("/")[0].strip()
                    move = line.lower().replace(" ", "-")
                    if move.startswith("hidden-power"):
                        move = "hidden-power"
                    if await find_one(ctx, "moves", {"identifier": move}) is None:
                        raise TeambuilderReadException(f"`{pokname}` was given a move `{move}` which does not exist.")
                    moves.append(move)
                elif line.startswith("Hidden Power:") or line.startswith("Tera Type:"):
                    pass
                else:
                    raise TeambuilderReadException(f"Data line `{line[:200]}` is not properly formatted.")
            if len(moves) != 4:
                raise TeambuilderReadException(f"`{pokname}` was given {len(moves)} moves. It must have exactly 4 moves.")
            evsum = sum([hpev, atkev, defev, spatkev, spdefev, speedev])
            if evsum > 510:
                raise TeambuilderReadException(f"`{pokname}` was given {evsum} EV points. It must have no more than 510 EV points.")
            for s in [hpiv, atkiv, defiv, spatkiv, spdefiv, speediv]:
                if s > 31 or s < 0:
                    raise TeambuilderReadException(f"`{pokname}` was given an IV stat of {s}. IVs must be between 0 and 31.")
            for s in [hpev, atkev, defev, spatkev, spdefev, speedev]:
                if s > 252 or s < 0:
                    raise TeambuilderReadException(f"`{pokname}` was given an EV stat of {s}. EVs must be between 0 and 252.")
            if item != "None":
                item_raw = await find_one(ctx, "items", {"identifier": item})
                if item_raw is None:
                    raise TeambuilderReadException(f"`{pokname}` was given an item `{item}` which does not exist.")
                MEGA_STONES = (
                    "venusaurite","blastoisinite","alakazite","gengarite","kangaskhanite","pinsirite",
                    "gyaradosite","aerodactylite","ampharosite","scizorite","heracronite","houndoominite",
                    "tyranitarite","blazikenite","gardevoirite","mawilite","aggronite","medichamite",
                    "manectite","banettite","absolite","latiasite","latiosite","garchompite","lucarionite",
                    "abomasite","beedrillite","pidgeotite","slowbronite","steelixite","sceptilite",
                    "swampertite","sablenite","sharpedonite","cameruptite","altarianite","glalitite",
                    "salamencite","metagrossite","lopunnite","galladite","audinite","diancite",
                )
                if item in MEGA_STONES:
                    item = "mega-stone"
                elif item in ("charizardite-x", "mewtwonite-x"):
                    item = "mega-stone-x"
                elif item in ("charizardite-y", "mewtwonite-y"):
                    item = "mega-stone-y"
            if nature not in (
                "Hardy","Bold","Modest","Calm","Timid","Lonely","Docile","Mild","Gentle","Hasty","Adamant","Impish","Bashful",
                "Careful","Jolly","Naughty","Lax","Rash","Quirky","Naive","Brave","Relaxed","Quiet","Sassy","Serious",
            ):
                raise TeambuilderReadException(f"`{pokname}` was given a nature `{nature}` which does not exist.")
            if level > 100 or level < 1:
                raise TeambuilderReadException(f"`{pokname}` was given a level of {level}.")
            if happiness < 0:
                raise TeambuilderReadException(f"`{pokname}` was given a happiness of {happiness}.")
            pokemon = {
                'id': 0,
                'pokname': pokname,
                'hpiv': hpiv, 'atkiv': atkiv, 'defiv': defiv,
                'spatkiv': spatkiv, 'spdefiv': spdefiv, 'speediv': speediv,
                'hpev': hpev, 'atkev': atkev, 'defev': defev,
                'spatkev': spatkev, 'spdefev': spdefev, 'speedev': speedev,
                'moves': moves, 'hitem': item, 'nature': nature,
                'poknick': nick, 'pokelevel': level, 'happiness': happiness,
                'ability_index': ability_index, 'gender': gender,
                'shiny': shiny, 'radiant': False, 'skin': None,
            }
            party.append(pokemon)
        if len(party) < 1 or len(party) > 6:
            raise TeambuilderReadException(f"Your party has {len(party)} pokemon. It must have 1 to 6 pokemon.")
        return party

    # ──────────────────────────────────────────────────────────────────
    #  Battle runner
    # ──────────────────────────────────────────────────────────────────
    async def wrapped_run(self, battle):
        self.games[int(battle.ctx.message.id)] = battle
        try:
            winner = await battle.run()
        except (aiohttp.client_exceptions.ClientOSError, asyncio.TimeoutError):
            await battle.channel.send(
                "The bot encountered an unexpected network issue, "
                "and the duel could not continue. Please try again in a few moments."
            )
            return None
        except Exception as exc:
            msg = 'Error in PokemonDuel.\n'
            self.log.exception(msg)
            self.bot.dispatch('flamecogs_game_error', battle, exc)
            await battle.channel.send(f'error lmaoo.\n{exc}')
            return None
        else:
            if int(battle.ctx.message.id) in self.games:
                del self.games[int(battle.ctx.message.id)]
            return winner

    # ──────────────────────────────────────────────────────────────────
    #  Top-level command groups
    # ──────────────────────────────────────────────────────────────────
    @commands.group(aliases=["pokeduel", "duel"], invoke_without_command=True)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def pokemonduel(self, ctx, opponent: discord.Member):
        """Battle in a Pokemon Duel with another member of your server."""
        await self._start_duel(ctx, opponent)

    @pokemonduel.command()
    async def inverse(self, ctx, opponent: discord.Member):
        """Battle in an Inverse Duel with another member of your server."""
        await self._start_duel(ctx, opponent, inverse_battle=True)

    @pokemonduel.command(aliases=["random", "randombattle"])
    async def random_battle(self, ctx, opponent: discord.Member):
        """
        Battle in a Random Duel against another member.
        Both players get randomly generated teams.
        """
        await self._start_random_duel(ctx, opponent)

    @pokemonduel.command(name="npc")
    async def battle_npc(self, ctx):
        """Battle against the Foul-Play MCTS NPC with your team."""
        await self._start_npc_battle(ctx)

    @pokemonduel.command(name="randomnpc", aliases=["randomnpcbattle"])
    async def random_npc_battle(self, ctx):
        """Random battle against the Foul-Play MCTS NPC."""
        await self._start_random_npc_battle(ctx)

    @pokemonduel.command(name="npcvsnpc", aliases=["npcbattle"])
    async def npc_vs_npc_battle(self, ctx):
        """NPC vs NPC battle — watch the Foul-Play MCTS engine duel."""
        await self._start_npc_vs_npc_battle(ctx)

    # ──────────────────────────────────────────────────────────────────
    #  NPC vs NPC
    # ──────────────────────────────────────────────────────────────────
    async def _start_npc_vs_npc_battle(self, ctx):
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        npc1_team_data = await asyncio.to_thread(
            generate_npc_team, seed=int(ctx.message.id) if ctx.message else None)
        npc1_raw = convert_to_raw_data(npc1_team_data, "NPC Alpha")
        npc2_team_data = await asyncio.to_thread(
            generate_npc_team, seed=int(ctx.message.id) + 1000 if ctx.message else None)
        npc2_raw = convert_to_raw_data(npc2_team_data, "NPC Beta")

        npc1_party, npc2_party = [], []
        try:
            for raw_data in npc1_raw:
                npc1_party.append(await create(ctx, raw_data))
            for raw_data in npc2_raw:
                npc2_party.append(await create(ctx, raw_data))
        except Exception as e:
            await channel.send(f"Error creating NPC pokemon: {e}")
            return

        t1 = NPCTrainer("NPC Alpha", npc1_party)
        t2 = NPCTrainer("NPC Beta",  npc2_party)
        await ctx.send("🎮 Starting NPC vs NPC Battle!\n   Alpha vs Beta — Foul-Play MCTS engine duel.")
        battle = Battle(ctx, channel, t1, t2)
        ai1 = NPCTeamAI(t1, t2); ai2 = NPCTeamAI(t2, t1)
        ai1.set_battle(battle); ai2.set_battle(battle)
        t1.set_ai(ai1); t2.set_ai(ai2)
        t1.switch_poke(ai1.choose_lead())
        t2.switch_poke(ai2.choose_lead())
        t1.event.set(); t2.event.set()
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        winner = await self.wrapped_run(battle)
        if winner:
            if hasattr(t1, 'ai') and t1.ai: t1.ai.on_battle_end(winner == t1)
            if hasattr(t2, 'ai') and t2.ai: t2.ai.on_battle_end(winner == t2)

    # ──────────────────────────────────────────────────────────────────
    #  User vs NPC
    # ──────────────────────────────────────────────────────────────────
    async def _start_npc_battle(self, ctx):
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        party_data = await self.config.member(ctx.author).party()
        if not party_data:
            await ctx.send(f"You haven't setup your party yet!\nSet one with `{ctx.prefix}pokemonduel party set`.")
            return
        user_party = []
        try:
            for pdata in party_data:
                user_party.append(await create(ctx, pdata))
        except Exception as e:
            await channel.send(f"Error creating your pokemon: {e}")
            return
        npc_team_data = await asyncio.to_thread(
            generate_npc_team, seed=int(ctx.message.id) if ctx.message else None)
        npc_raw = convert_to_raw_data(npc_team_data, "NPC Team")
        npc_party = []
        try:
            for raw_data in npc_raw:
                npc_party.append(await create(ctx, raw_data))
        except Exception as e:
            await channel.send(f"Error creating NPC pokemon: {e}")
            return

        user_trainer = MemberTrainer(ctx.author, user_party)
        npc_trainer = NPCTrainer("NPC Challenger", npc_party)
        await ctx.send("Starting a battle against the Foul-Play MCTS NPC!")
        battle = Battle(ctx, channel, user_trainer, npc_trainer)
        ai = NPCTeamAI(npc_trainer, user_trainer)
        ai.set_battle(battle); npc_trainer.set_ai(ai)
        npc_trainer.switch_poke(ai.choose_lead())
        npc_trainer.event.set()
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        winner = await self.wrapped_run(battle)
        if winner and hasattr(npc_trainer, 'ai') and npc_trainer.ai:
            npc_trainer.ai.on_battle_end(winner == npc_trainer)

    # ──────────────────────────────────────────────────────────────────
    #  Random NPC
    # ──────────────────────────────────────────────────────────────────
    async def _start_random_npc_battle(self, ctx):
        from ..modes.randoms.random_team_gen import generate_two_teams, convert_team_to_raw_data
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        team1_data, _ = await asyncio.to_thread(
            generate_two_teams, seed=int(ctx.message.id) if ctx.message else None)
        raw_party1 = convert_team_to_raw_data(team1_data, "Your Random Team")
        user_party = []
        try:
            for raw_data in raw_party1:
                user_party.append(await create(ctx, raw_data))
        except Exception as e:
            await channel.send(f"Error creating your Pokemon: {e}")
            return
        npc_team_data = generate_npc_team(seed=None)
        npc_raw = convert_to_raw_data(npc_team_data, "NPC Team")
        npc_party = []
        try:
            for raw_data in npc_raw:
                npc_party.append(await create(ctx, raw_data))
        except Exception as e:
            await channel.send(f"Error creating NPC Pokemon: {e}")
            return
        user_trainer = MemberTrainer(ctx.author, user_party)
        npc_trainer  = NPCTrainer("NPC Challenger", npc_party)
        await ctx.send("Starting a Random Battle against the Foul-Play MCTS NPC!")
        battle = Battle(ctx, channel, user_trainer, npc_trainer)
        ai = NPCTeamAI(npc_trainer, user_trainer)
        ai.set_battle(battle); npc_trainer.set_ai(ai)
        npc_trainer.switch_poke(ai.choose_lead())
        npc_trainer.event.set()
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        winner = await self.wrapped_run(battle)
        if winner and hasattr(npc_trainer, 'ai') and npc_trainer.ai:
            npc_trainer.ai.on_battle_end(winner == npc_trainer)

    # ──────────────────────────────────────────────────────────────────
    #  Random duel between two members (unchanged)
    # ──────────────────────────────────────────────────────────────────
    async def _start_random_duel(self, ctx, opponent: discord.Member, *, inverse_battle=False):
        from ..modes.randoms.random_team_gen import generate_two_teams, convert_team_to_raw_data
        if opponent.id == ctx.author.id:
            await ctx.send("You cannot duel yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot duel a bot!")
            return
        channel = ctx.channel
        team1_data, team2_data = generate_two_teams(seed=int(ctx.message.id) if ctx.message else None)
        raw_party1 = convert_team_to_raw_data(team1_data, "Player Team")
        raw_party2 = convert_team_to_raw_data(team2_data, "Random Team")
        party1, party2 = [], []
        for raw_data in raw_party1:
            try:
                party1.append(await create(ctx, raw_data))
            except Exception as e:
                await channel.send(f"Error creating Pokemon: {e}")
                return
        for raw_data in raw_party2:
            try:
                party2.append(await create(ctx, raw_data))
            except Exception as e:
                await channel.send(f"Error creating Pokemon: {e}")
                return
        view = DuelAcceptView(ctx, opponent)
        initial_message = await ctx.send(
            f"{opponent.mention} You have been challenged to a Random Battle by {ctx.author.name}!\n",
            view=view)
        view.message = initial_message
        if (await self.config.guild(ctx.guild).useThreads()
                and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
                and ctx.channel.type is discord.ChannelType.text):
            try:
                channel = await initial_message.create_thread(
                    name='PokemonDuel',
                    reason='Automated thread for PokemonDuels.')
            except discord.HTTPException:
                pass
        await view.wait()
        if not view.confirm:
            return
        trainer1 = MemberTrainer(ctx.author, party1)
        trainer2 = MemberTrainer(opponent,   party2)
        await ctx.send("Starting a Random Battle!")
        battle = Battle(ctx, channel, trainer1, trainer2, inverse_battle=inverse_battle)
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        await self.wrapped_run(battle)

    # ──────────────────────────────────────────────────────────────────
    #  Two-member duel (unchanged)
    # ──────────────────────────────────────────────────────────────────
    async def _start_duel(self, ctx, opponent: discord.Member, *, inverse_battle=False):
        if opponent.id == ctx.author.id:
            await ctx.send("You cannot duel yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot duel a bot!")
            return
        view = DuelAcceptView(ctx, opponent)
        battle_type = "an inverse battle" if inverse_battle else "a duel"
        initial_message = await ctx.send(
            f"{opponent.mention} You have been challenged to {battle_type} by {ctx.author.name}!\n",
            view=view)
        view.message = initial_message
        channel = ctx.channel
        if (await self.config.guild(ctx.guild).useThreads()
                and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
                and ctx.channel.type is discord.ChannelType.text):
            try:
                channel = await initial_message.create_thread(
                    name='PokemonDuel',
                    reason='Automated thread for PokemonDuels.')
            except discord.HTTPException:
                pass
        await view.wait()
        if not view.confirm:
            return
        trainers = []
        for player in (ctx.author, opponent):
            party = await self.config.member(player).party()
            if not party:
                await channel.send(f"{player} has not setup their party yet!\nSet one with `{ctx.prefix}pokemonduel party set`.")
                return
            party = [await create(ctx, p) for p in party]
            trainers.append(MemberTrainer(player, party))
        battle = Battle(ctx, channel, *trainers, inverse_battle=inverse_battle)
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        await self.wrapped_run(battle)

    # ──────────────────────────────────────────────────────────────────
    #  Party management
    # ──────────────────────────────────────────────────────────────────
    @commands.group("party")
    async def party(self, ctx):
        """Manage your party of pokemon."""
        pass

    @party.command(name="set")
    async def party_set(self, ctx, *, pokemon_data):
        """Set your party of pokemon (Pokémon Showdown teambuilder format)."""
        try:
            party = await self.party_from_teambuilder(ctx, pokemon_data)
        except TeambuilderReadException as e:
            await ctx.send(f"Couldn't validate your team.\n{e}")
            return
        except Exception:
            await ctx.send("Couldn't properly parse your team. Make sure you follow the Showdown format.")
            self.log.exception("Failed to read a teambuilder team string.")
            return
        await self.config.member(ctx.author).party.set(party)
        embed = discord.Embed(title="Your new party")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await self.gen_party_embed(ctx, party, embed)
        await ctx.send(embed=embed)

    @party.command(name="pokecord", hidden=True)
    async def party_pokecord(self, ctx, *ids: int):
        """Create a party of pokemon imported from Pokecord."""
        pass

    @party.command(name="list", aliases=["view"])
    async def party_list(self, ctx, user: discord.Member = None):
        member = user or ctx.author
        party = await self.config.member(member).party()
        if len(party) == 0:
            await ctx.send(f"You haven't setup your party yet!\nSet one with `{ctx.prefix}pokemonduel party set`.")
            return
        embed = discord.Embed(title=f"{member.display_name}'s Party")
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.gen_party_embed(ctx, party, embed)
        await ctx.send(embed=embed)

    @staticmethod
    async def gen_party_embed(ctx, party, embed):
        for idx, pokemon in enumerate(party):
            pokname = pokemon["pokname"]; poknick = pokemon["poknick"]
            gender = pokemon["gender"]
            if gender == "-m": gender = "Male"
            elif gender == "-f": gender = "Female"
            elif gender == "-x": gender = "Genderless"
            moves = pokemon["moves"]
            moves = "|".join([f"`{x}`" for x in moves])
            ability_index = pokemon["ability_index"]
            form_info = await find_one(ctx, "forms", {"identifier": pokname.lower()})
            ab_ids = [record["ability_id"] for record in
                      await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]})]
            try:
                ab_id = ab_ids[ability_index]
            except IndexError:
                ab_id = ab_ids[0]
            ability = await find_one(ctx, "abilities", {"id": ab_id})
            ability = ability["identifier"]
            hitem = pokemon["hitem"]; nature = pokemon["nature"].lower()
            happiness = pokemon["happiness"]
            title = f"{gender} {pokname} "
            if poknick != "None":
                title += f"({poknick}) "
            desc = f"{moves}\nAbility `{ability}`"
            if hitem != "None":
                desc += f" | Holding `{hitem}`"
            desc += f"\nNature `{nature}` | Happiness `{happiness}`\n"
            desc += "`    `|` hp`|`atk`|`def`|`spa`|`spd`|`spe`\n"
            desc += (f"`IVs:`|`{pokemon['hpiv']:3d}`|`{pokemon['atkiv']:3d}`|`{pokemon['defiv']:3d}`|"
                     f"`{pokemon['spatkiv']:3d}`|`{pokemon['spdefiv']:3d}`|`{pokemon['speediv']:3d}`\n")
            desc += (f"`EVs:`|`{pokemon['hpev']:3d}`|`{pokemon['atkev']:3d}`|`{pokemon['defev']:3d}`|"
                     f"`{pokemon['spatkev']:3d}`|`{pokemon['spdefev']:3d}`|`{pokemon['speedev']:3d}`\n")
            embed.add_field(name=title, value=desc, inline=bool(idx % 2))

    # ──────────────────────────────────────────────────────────────────
    #  Server config
    # ──────────────────────────────────────────────────────────────────
    @commands.guild_only()
    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def pokemonduelset(self, ctx):
        await ctx.send_help()
        cfg = await self.config.guild(ctx.guild).all()
        msg = "Game contained to a thread: {useThreads}\n".format_map(cfg)
        await ctx.send(f"```py\n{msg}```")

    @pokemonduelset.command()
    async def thread(self, ctx, value: bool = None):
        if value is None:
            v = await self.config.guild(ctx.guild).useThreads()
            await ctx.send("The game is currently run in a per-game thread." if v
                           else "The game is not currently run in a thread.")
        else:
            await self.config.guild(ctx.guild).useThreads.set(value)
            await ctx.send("The game will now be run in a per-game thread." if value
                           else "The game will not be run in a thread.")

    # ──────────────────────────────────────────────────────────────────
    #  Sprite info
    # ──────────────────────────────────────────────────────────────────
    @commands.command(name="info", aliases=["sprite", "img"])
    async def info(self, ctx, name: str):
        poke = await find_one(ctx, "forms", {"identifier": name.lower()})
        if poke is None:
            return await ctx.send(f"no poke named `{name}`, maybe devs are lazy and didnt add.")
        poke_id = poke["pokemon_id"]
        sprite = Path(__file__).parent.parent / "data" / "img" / f"{poke_id}.png"
        if not sprite.exists():
            return await ctx.send(f"no sprite for ``{name}`` add it yourself bruv id is ``{poke_id}``")
        poke = await find_one(ctx, "pokemon_stats", {"pokemon_id": poke_id})
        stats = poke["stats"]
        e = discord.Embed(description=f"hp: `{stats[0]}` | atk: `{stats[1]}` | def: `{stats[2]}`\n"
                                       f"spatk: `{stats[3]}` | spdef: `{stats[4]}` | speed: `{stats[5]}`")
        e.set_image(url=f"attachment://{sprite.name}")
        e.set_footer(text=f"id: {poke_id}")
        await ctx.send(embed=e, file=discord.File(sprite))


    # ──────────────────────────────────────────────────────────────────
    #  Foul-Play MCTS NPC inspection
    # ──────────────────────────────────────────────────────────────────
    @pokemonduel.command(name="npcaireload", aliases=["reloadai"])
    @commands.is_owner()
    async def reload_ai(self, ctx):
        """No-op for the foul-play MCTS NPC (no weights to reload)."""
        reload_network()
        await ctx.send("ℹ️  Foul-Play MCTS NPC has no weights to reload — it uses poke-engine at runtime.")

    @pokemonduel.command(name="npcaistats", aliases=["aistats", "npstats"])
    async def show_npc_stats(self, ctx):
        """Show info about the Foul-Play MCTS NPC engine."""
        from ..ai.npc_bridge import MCTS_SEARCH_MS
        txt = (
            "**Foul-Play MCTS NPC**\n"
            f"```\n"
            f"engine    : poke-engine (Rust MCTS)\n"
            f"search_ms : {MCTS_SEARCH_MS} ms per turn\n"
            f"team gen  : random (random_team_gen)\n"
            f"no weights, no training loop\n"
            f"```"
        )
        await ctx.send(txt)
