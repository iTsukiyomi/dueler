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
from ..ai.npc_bridge import NPCTeamAI, reload_network
from ..ai import config as AI_CONFIG


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

            if winner is not None:
                loser = (
                    battle.trainer2 if winner is battle.trainer1
                    else battle.trainer1
                )
                is_w_human = winner.is_human() if hasattr(winner, "is_human") else False
                is_l_human = loser.is_human() if hasattr(loser, "is_human") else False

                if is_w_human and is_l_human:
                    try:
                        from ..services.player_service import PlayerService
                        svc = PlayerService()
                        w_elo, l_elo = await svc.record_match_result(
                            str(winner.id),
                            str(loser.id),
                            money_reward=100,
                        )
                        import discord as _dc
                        embed = _dc.Embed(
                            title="Match Recorded",
                            description=(
                                f"**{winner.name}** Elo: **{w_elo}** (+↑)  |  "
                                f"**{loser.name}** Elo: **{l_elo}** (−↓)\n"
                                f"**{winner.name}** earned ¥100."
                            ),
                            color=0xFFCB05,
                        )
                        await battle.channel.send(embed=embed)
                    except Exception as exc:
                        self.log.warning(
                            "Failed to update Elo/economy after match: %s", exc
                        )
                elif is_w_human and not is_l_human:
                    try:
                        from ..services.player_service import PlayerService
                        svc = PlayerService()
                        new_elo = await svc.record_npc_match_result(
                            str(winner.id),
                            winner.name,
                            won=True,
                            money_reward=100,
                        )
                        import discord as _dc
                        embed = _dc.Embed(
                            title="NPC Match Recorded",
                            description=(
                                f"**{winner.name}** won against the NPC!\n"
                                f"Elo: **{new_elo}** (No Change)\n"
                                f"**{winner.name}** earned ¥100."
                            ),
                            color=0xFFCB05,
                        )
                        await battle.channel.send(embed=embed)
                    except Exception as exc:
                        self.log.warning(
                            "Failed to update PvE economy after match: %s", exc
                        )
                elif not is_w_human and is_l_human:
                    try:
                        from ..services.player_service import PlayerService
                        svc = PlayerService()
                        new_elo = await svc.record_npc_match_result(
                            str(loser.id),
                            loser.name,
                            won=False,
                            money_reward=0,
                        )
                        import discord as _dc
                        embed = _dc.Embed(
                            title="NPC Match Recorded",
                            description=(
                                f"**{loser.name}** lost against the NPC!\n"
                                f"Elo: **{new_elo}** (No Change)"
                            ),
                            color=_dc.Color.red(),
                        )
                        await battle.channel.send(embed=embed)
                    except Exception as exc:
                        self.log.warning(
                            "Failed to update PvE economy after match: %s", exc
                        )

            return winner

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
        """Battle against the AlphaZero NPC with your team."""
        await self._start_npc_battle(ctx)

    @pokemonduel.command(name="randomnpc", aliases=["randomnpcbattle"])
    async def random_npc_battle(self, ctx):
        """Random battle against the AlphaZero NPC."""
        await self._start_random_npc_battle(ctx)

    @pokemonduel.command(name="npcvsnpc", aliases=["npcbattle"])
    async def npc_vs_npc_battle(self, ctx):
        """NPC vs NPC battle — watch the AlphaZero AI play itself."""
        await self._start_npc_vs_npc_battle(ctx)

    async def _start_npc_vs_npc_battle(self, ctx):
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        npc1_team_data = await asyncio.to_thread(
            # pyrefly: ignore [bad-argument-type]
            generate_npc_team, seed=int(ctx.message.id) if ctx.message else None)
        npc1_raw = convert_to_raw_data(npc1_team_data, "NPC Alpha")
        npc2_team_data = await asyncio.to_thread(
            # pyrefly: ignore [bad-argument-type]
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
        await ctx.send("🎮 Starting NPC vs NPC Battle!\n   Alpha vs Beta — watch the AlphaZero brain play itself.")
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

    async def _start_npc_battle(self, ctx):
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        from ..services.team_service import TeamService
        party_data = await TeamService().load_active_party(str(ctx.author.id))
        if not party_data:
            party_data = await self.config.member(ctx.author).party()
        if not party_data:
            await ctx.send(f"You haven't setup your party yet!\nSet one with `{ctx.prefix}party load <name>` or `{ctx.prefix}party add`.")
            return
        user_party = []
        try:
            for pdata in party_data:
                user_party.append(await create(ctx, pdata))
        except Exception as e:
            await channel.send(f"Error creating your pokemon: {e}")
            return
        npc_team_data = await asyncio.to_thread(
            # pyrefly: ignore [bad-argument-type]
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
        await ctx.send("Starting a battle against the AlphaZero NPC Challenger!")
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

    async def _start_random_npc_battle(self, ctx):
        from ..modes.randoms.random_team_gen import generate_two_teams, convert_team_to_raw_data
        from ..modes.npc.npc_team_gen import generate_npc_team, convert_to_raw_data
        if not ctx.author:
            await ctx.send("This command must be used in a server!")
            return
        channel = ctx.channel
        team1_data, _ = await asyncio.to_thread(
            # pyrefly: ignore [bad-argument-type]
            generate_two_teams, seed=int(ctx.message.id) if ctx.message else None)
        raw_party1 = convert_team_to_raw_data(team1_data, "Your Random Team")
        user_party = []
        try:
            for raw_data in raw_party1:
                user_party.append(await create(ctx, raw_data))
        except Exception as e:
            await channel.send(f"Error creating your Pokemon: {e}")
            return
        # pyrefly: ignore [bad-argument-type]
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
        await ctx.send("Starting a Random Battle against the AlphaZero NPC Challenger!")
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

    async def _start_random_duel(self, ctx, opponent: discord.Member, *, inverse_battle=False):
        from ..modes.randoms.random_team_gen import generate_two_teams, convert_team_to_raw_data
        if opponent.id == ctx.author.id:
            await ctx.send("You cannot duel yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot duel a bot!")
            return
        channel = ctx.channel
        # pyrefly: ignore [bad-argument-type]
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
        # pyrefly: ignore [missing-attribute]
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
        # pyrefly: ignore [missing-attribute]
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
        from ..services.team_service import TeamService
        team_svc = TeamService()
        trainers = []
        for player in (ctx.author, opponent):
            party_data = await team_svc.load_active_party(str(player.id))
            if not party_data:
                party_data = await self.config.member(player).party()
            if not party_data:
                await channel.send(f"{player} has not setup their party yet!\nSet one with `{ctx.prefix}party load <name>` or `{ctx.prefix}party add`.")
                return
            party = [await create(ctx, p) for p in party_data]
            trainers.append(MemberTrainer(player, party))
        battle = Battle(ctx, channel, *trainers, inverse_battle=inverse_battle)
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        await self.wrapped_run(battle)

    @commands.group("old_party")
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

    @party.command(name="list")
    # pyrefly: ignore [bad-function-definition]
    async def party_list(self, ctx, user: discord.Member = None):
        member = user or ctx.author
        from ..services.team_service import TeamService
        party = await TeamService().load_active_party(str(member.id))
        if not party:
            party = await self.config.member(member).party()
        if len(party) == 0:
            await ctx.send(f"You haven't setup your party yet!\nSet one with `{ctx.prefix}party load <name>` or `{ctx.prefix}party add`.")
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
                      # pyrefly: ignore [unsupported-operation]
                      await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]})]
            try:
                ab_id = ab_ids[ability_index]
            except IndexError:
                ab_id = ab_ids[0]
            ability = await find_one(ctx, "abilities", {"id": ab_id})
            # pyrefly: ignore [unsupported-operation]
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

    @commands.guild_only()
    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def pokemonduelset(self, ctx):
        await ctx.send_help()
        cfg = await self.config.guild(ctx.guild).all()
        msg = "Game contained to a thread: {useThreads}\n".format_map(cfg)
        await ctx.send(f"```py\n{msg}```")

    @pokemonduelset.command()
    # pyrefly: ignore [bad-function-definition]
    async def thread(self, ctx, value: bool = None):
        if value is None:
            v = await self.config.guild(ctx.guild).useThreads()
            await ctx.send("The game is currently run in a per-game thread." if v
                           else "The game is not currently run in a thread.")
        else:
            await self.config.guild(ctx.guild).useThreads.set(value)
            await ctx.send("The game will now be run in a per-game thread." if value
                           else "The game will not be run in a thread.")

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
        # pyrefly: ignore [unsupported-operation]
        stats = poke["stats"]
        e = discord.Embed(description=f"hp: `{stats[0]}` | atk: `{stats[1]}` | def: `{stats[2]}`\n"
                                       f"spatk: `{stats[3]}` | spdef: `{stats[4]}` | speed: `{stats[5]}`")
        e.set_image(url=f"attachment://{sprite.name}")
        e.set_footer(text=f"id: {poke_id}")
        await ctx.send(embed=e, file=discord.File(sprite))

    @pokemonduel.command(name="trainnpc", aliases=["trainai", "pretrain"])
    @commands.is_owner()
    async def train_npc_ai(self, ctx, battles: int = 200):
        """
        Run headless NPC vs NPC games to grow the live replay buffer
        and refresh the AI’s knowledge.

        For real long-running training, launch:
            python -m pokemonduel.ai.distributed --workers 8
        """
        if battles < 10:
            await ctx.send("Minimum 10 battles required.")
            return
        if battles > 5000:
            await ctx.send("Maximum 5000 battles to keep things responsive.")
            return
        await ctx.send(f"🎮 Starting headless training — {battles} battles. "
                       f"This runs in a background thread.")
        try:
            def _run():
                import importlib, sys
                here = Path(__file__).resolve().parent.parent.parent
                if str(here) not in sys.path:
                    sys.path.insert(0, str(here))
                from simulated_battle import run_battle  # type: ignore
                wins = [0, 0, 0]
                for _ in range(battles):
                    ws, _t, _a, _b = run_battle()
                    wins[ws] += 1
                return wins
            wins = await asyncio.to_thread(_run)
            await ctx.send(
                f"✅ Headless training complete!\n"
                f"• side1 wins: {wins[1]} ({wins[1]/max(1,sum(wins)):.1%})\n"
                f"• side2 wins: {wins[2]} ({wins[2]/max(1,sum(wins)):.1%})\n"
                f"• ties:       {wins[0]}\n"
                f"Run `python -m pokemonduel.ai.distributed` to start a real "
                f"multi-process AlphaZero training session."
            )
        except Exception as e:
            await ctx.send(f"❌ Training failed: {e}")
            self.log.exception("NPC training error")

    @pokemonduel.command(name="npcaireload", aliases=["reloadai"])
    @commands.is_owner()
    async def reload_ai(self, ctx):
        """Hot-reload the AlphaZero network from disk."""
        try:
            reload_network()
            await ctx.send("🔁 AlphaZero network reloaded from disk.")
        except Exception as e:
            await ctx.send(f"❌ Reload failed: {e}")
            self.log.exception("AI reload error")

    @pokemonduel.command(name="npcaistats", aliases=["aistats", "npstats"])
    async def show_npc_stats(self, ctx):
        """Show AlphaZero training progress (steps, ELO, buffer size)."""
        try:
            meta = {}
            if AI_CONFIG.META_PATH.exists():
                with open(AI_CONFIG.META_PATH, "r") as f:
                    meta = json.load(f)
            elo  = {}
            if AI_CONFIG.ELO_PATH.exists():
                with open(AI_CONFIG.ELO_PATH, "r") as f:
                    elo = json.load(f).get("ratings", {})
            params = meta.get("params", {})
            step   = meta.get("step", 0)
            txt = (
                "**AlphaZero AI**\n"
                f"```\n"
                f"steps   : {step:,}\n"
                f"params  : total={params.get('total',0):,}  trainable={params.get('trainable',0):,}\n"
                f"ELO     : latest={elo.get('latest',1200):.0f}  best={elo.get('best',1200):.0f}\n"
                f"checkpoint dir : {AI_CONFIG.CKPT_DIR}\n"
                f"best model     : {AI_CONFIG.BEST_MODEL.name} "
                f"({'present' if AI_CONFIG.BEST_MODEL.exists() else 'absent'})\n"
                f"```"
            )
            await ctx.send(txt)
        except Exception as e:
            await ctx.send(f"Could not load stats: {e}")
            self.log.exception("show stats error")
