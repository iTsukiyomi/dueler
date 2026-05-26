"""
pokemonduel.cog.teambuilder_cog
================================
Individual Pokémon customisation commands — select, learn, IV/EV,
nature, ability, item, and quick-info display.

All commands operate on a per-user "workspace" Pokémon that is loaded
by ;select and persisted back to the active team on save.

Commands:
    ;select <name_or_slot>
    ;learn <slot_1_to_4> <move_name>
    ;moveset
    ;iv <stat> <value>
    ;evs <stat> <value>
    ;nature <nature_name>
    ;ability [name | switch]
    ;item <item_name>
    ;qi  (quick info)
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..core.registry import MOVES, NATURES, ITEMS, ABILITIES, FORMS, POKE_ABILITIES, LEARNSETS
from ..services.team_service import TeamService
from ..services.player_service import PlayerService

log = logging.getLogger("dueler.cog.teambuilder")

_STAT_KEYS = {
    "hp": "hpev", "atk": "atkev", "def": "defev",
    "spa": "spatkev", "spd": "spdefev", "spe": "speedev",
}
_IV_KEYS = {
    "hp": "hpiv", "atk": "atkiv", "def": "defiv",
    "spa": "spatkiv", "spd": "spdefiv", "spe": "speediv",
}

_TYPE_ID_TO_NAME = {
    1: "Normal", 2: "Fighting", 3: "Flying", 4: "Poison", 5: "Ground",
    6: "Rock", 7: "Bug", 8: "Ghost", 9: "Steel", 10: "Fire",
    11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
    16: "Dragon", 17: "Dark", 18: "Fairy"
}


# -- Helpers -----------------------------------------------------------

def resolve_form_identifier(target_name: str) -> str | None:
    """Resolve a user-provided name to a canonical form identifier from FORMS."""
    norm = target_name.strip().lower()
    
    # 1. Exact match with hyphens/spaces
    for sep in ["-", " ", ""]:
        k = norm.replace(" ", sep)
        form = FORMS.get(k)
        if form is not None:
            return form["identifier"]
    
    # 2. Stripped exact match or prefix/substring match
    stripped_target = norm.replace("-", "").replace(" ", "").replace("_", "")
    best_match = None
    
    for entry in FORMS.all:
        iden = entry.get("identifier", "").lower()
        stripped_iden = iden.replace("-", "").replace(" ", "").replace("_", "")
        
        if stripped_iden == stripped_target:
            return entry["identifier"]
        
        if stripped_iden.startswith(stripped_target):
            best_match = entry["identifier"]
            
    if best_match:
        return best_match
        
    # Contains match
    for entry in FORMS.all:
        iden = entry.get("identifier", "").lower()
        stripped_iden = iden.replace("-", "").replace(" ", "").replace("_", "")
        if stripped_target in stripped_iden:
            return entry["identifier"]
            
    return None


def get_legal_moves(pokemon_name: str) -> set[str] | None:
    """Load the complete learnset move names (lowercase, kebab-case) for a Pokémon species/form."""
    key = pokemon_name.lower().replace("-", "").replace(" ", "").replace("_", "")
    record = LEARNSETS.get(key)
    if record is None and "-" in pokemon_name:
        base_name = pokemon_name.split("-")[0]
        base_key = base_name.lower().replace("-", "").replace(" ", "").replace("_", "")
        record = LEARNSETS.get(base_key)
        
    if record and "value" in record:
        moves_list = record["value"]
        return {m.lower().replace(" ", "-").replace("_", "-") for m in moves_list}
    return None



class MovesetView(discord.ui.View):
    """View class for moveset pagination."""
    
    def __init__(self, author_id: int, embed: discord.Embed, pages: list[str]) -> None:
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.embed = embed
        self.pages = pages
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.blurple)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu is not yours.", ephemeral=True)
            return
        self.current_page -= 1
        self._update_buttons()
        self.embed.description = self.pages[self.current_page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu is not yours.", ephemeral=True)
            return
        self.current_page += 1
        self._update_buttons()
        self.embed.description = self.pages[self.current_page]
        await interaction.response.edit_message(embed=self.embed, view=self)


class TeambuilderCog(commands.Cog, name="Teambuilder"):
    """Customise individual Pokémon — moves, EVs, IVs, nature, ability, item."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._team_svc = TeamService()
        self._player_svc = PlayerService()
        # Per-user workspace: {user_id: {"team_name": str, "slot_idx": int | None, "pokemon": dict}}
        self._workspace: dict[str, dict] = {}

    # -- Helpers -----------------------------------------------------------

    async def _load_workspace(self, ctx: commands.Context) -> dict | None:
        """Return the current workspace Pokémon, or None with an error message."""
        ws = self._workspace.get(str(ctx.author.id))
        if ws is None:
            await ctx.send(
                embed=discord.Embed(
                    title="No Pokémon Selected",
                    description="Use `;select <slot>` or `;select <name>` to pick a Pokémon.",
                    color=discord.Color.red(),
                )
            )
            return None
        return ws

    async def _save_workspace(self, ctx: commands.Context) -> None:
        """Persist workspace changes back to the active party in MongoDB if it is a slot selection."""
        ws = self._workspace.get(str(ctx.author.id))
        if ws is None or ws.get("slot_idx") is None:
            return

        party = await self._team_svc.load_active_party(str(ctx.author.id))
        if party is None:
            # Fallback to legacy config
            from ..config import EnhancedConfigManager
            class DummyPokemonDuelCog:
                pass
            DummyPokemonDuelCog.__class__.__name__ = "PokemonDuel"
            cfg = EnhancedConfigManager.get_conf(DummyPokemonDuelCog(), identifier=145519400223506432)
            party = await cfg.member(ctx.author).party()
            if not party:
                return

        if ws["slot_idx"] >= len(party):
            return

        party[ws["slot_idx"]] = ws["pokemon"]

        # Save to database under "__active__"
        await self._team_svc.save_active_party(str(ctx.author.id), party)

        # Double-write to legacy config
        from ..config import EnhancedConfigManager
        class DummyPokemonDuelCog:
            pass
        DummyPokemonDuelCog.__class__.__name__ = "PokemonDuel"
        cfg = EnhancedConfigManager.get_conf(DummyPokemonDuelCog(), identifier=145519400223506432)
        await cfg.member(ctx.author).party.set(party)

    # -- ;select -----------------------------------------------------------

    @commands.command(name="select")
    async def select(self, ctx: commands.Context, *, target: str):
        """
        Select a Pokémon to customise. Accepts slot (1-6) or a species name.

        Usage:
          ;select <slot_number>
          ;select <pokemon_name>
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        is_slot = False
        slot_num = -1
        try:
            val = int(target.strip())
            if 1 <= val <= 6:
                is_slot = True
                slot_num = val
        except ValueError:
            pass

        if is_slot:
            party = await self._team_svc.load_active_party(str(ctx.author.id))
            if party is None:
                await ctx.send(
                    embed=discord.Embed(
                        title="No Active Team",
                        description="Load a team first with `;party load <team_name>`.",
                        color=discord.Color.red(),
                    )
                )
                return

            if slot_num > len(party):
                await ctx.send(f"Your team only has {len(party)} Pokémon.")
                return

            idx = slot_num - 1
            pokemon = party[idx]
            profile = await self._player_svc.get_profile(str(ctx.author.id))
            team_name = profile.get("active_party_name", "?") if profile else "?"

            self._workspace[str(ctx.author.id)] = {
                "team_name": team_name,
                "slot_idx": idx,
                "pokemon": pokemon.copy(),
            }

            embed = discord.Embed(
                title=f"Selected: {pokemon.get('pokname', '?').replace('-', ' ').title()}",
                description=f"Slot {slot_num} of team **{team_name}**\n"
                            "Use `;learn`, `;iv`, `;evs`, `;nature`, `;ability`, `;item` to customise.\n"
                            "Use `;qi` to view full details.",
                color=discord.Color.teal(),
            )
            await ctx.send(embed=embed)
        else:
            # Resolve name from FORMS
            matched_identifier = resolve_form_identifier(target)
            if not matched_identifier:
                await ctx.send(f"Pokémon **{target}** not found in the forms database.")
                return

            import random
            ability_idx = 0
            form_info = FORMS.get(matched_identifier)
            if form_info:
                pokemon_id = form_info["pokemon_id"]
                records = POKE_ABILITIES.by_secondary(pokemon_id)
                if records:
                    ability_idx = random.randint(0, len(records) - 1)

            pokemon = {
                "id": 0,
                "pokname": matched_identifier,
                "poknick": "None",
                "hpiv": 31, "atkiv": 31, "defiv": 31,
                "spatkiv": 31, "spdefiv": 31, "speediv": 31,
                "hpev": 0, "atkev": 0, "defev": 0,
                "spatkev": 0, "spdefev": 0, "speedev": 0,
                "moves": ["tackle", "tackle", "tackle", "tackle"],
                "hitem": "",
                "nature": "Hardy",
                "pokelevel": 100,
                "happiness": 255,
                "ability_index": ability_idx,
                "gender": "",
                "shiny": False,
                "skin": None,
            }

            profile = await self._player_svc.get_profile(str(ctx.author.id))
            team_name = profile.get("active_party_name", "None") if profile else "None"

            self._workspace[str(ctx.author.id)] = {
                "team_name": team_name,
                "slot_idx": None,
                "pokemon": pokemon,
            }

            embed = discord.Embed(
                title=f"Selected: {matched_identifier.replace('-', ' ').title()}",
                description="Workspace Pokémon (not in active party yet)\n"
                            "Use `;learn`, `;iv`, `;evs`, `;nature`, `;ability`, `;item` to customise.\n"
                            "Use `;party add <slot>` to insert it into your active team.\n"
                            "Use `;qi` to view full details.",
                color=discord.Color.teal(),
            )
            await ctx.send(embed=embed)

    # -- ;learn ------------------------------------------------------------

    @commands.command(name="learn")
    async def learn(self, ctx: commands.Context, slot: int, *, move_name: str):
        """
        Teach a move to the selected Pokémon.

        Usage: ;learn <move_slot_1_to_4> <move_name>
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        if slot < 1 or slot > 4:
            await ctx.send("Move slot must be between 1 and 4.")
            return

        norm = move_name.strip().lower().replace(" ", "-")
        if norm not in MOVES:
            await ctx.send(f"Move **{move_name}** not found in the move database.")
            return

        poke = ws["pokemon"]
        # Strict learnset validation
        legal_moves = get_legal_moves(poke["pokname"])
        if legal_moves is not None:
            # Enforce check
            norm_check = norm.replace("-", "").replace("_", "")
            matched_move = None
            for lm in legal_moves:
                if lm.replace("-", "").replace("_", "") == norm_check:
                    matched_move = lm
                    break
            
            if matched_move is None:
                await ctx.send(f"**{poke['pokname'].replace('-', ' ').title()}** cannot learn **{move_name}**.")
                return
            norm = matched_move

        while len(poke["moves"]) < 4:
            poke["moves"].append("tackle")
        poke["moves"][slot - 1] = norm

        await self._save_workspace(ctx)

        move_data = MOVES.get(norm)
        power = move_data.get("power", "—") if move_data else "—"
        if power is None:
            power = "—"
        await ctx.send(
            embed=discord.Embed(
                title="Move Learned",
                description=f"**{poke['pokname'].replace('-', ' ').title()}** learned **{norm.replace('-', ' ').title()}** in slot {slot}.\n"
                            f"Power: {power}",
                color=discord.Color.green(),
            )
        )

    # -- ;ability ----------------------------------------------------------

    @commands.command(name="ability")
    async def ability(self, ctx: commands.Context, *, arg: str = "switch"):
        """
        Set or switch the ability for the selected Pokémon.

        Usage:
          ;ability <ability_name>
          ;ability switch
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        poke = ws["pokemon"]
        pn = poke["pokname"].lower()
        form_info = FORMS.get(pn)
        if form_info is None:
            await ctx.send(f"Error: form info not found for {poke['pokname']}.")
            return

        pokemon_id = form_info["pokemon_id"]
        records = POKE_ABILITIES.by_secondary(pokemon_id)
        if not records:
            await ctx.send("This Pokémon does not have any registered abilities.")
            return

        ab_options = []
        for r in records:
            ab_id = r["ability_id"]
            ab_data = ABILITIES.find_one({"id": ab_id})
            if ab_data:
                ab_options.append(ab_data)

        if not ab_options:
            await ctx.send("Could not load abilities for this Pokémon.")
            return

        legal_names = [opt["identifier"].lower() for opt in ab_options]

        arg_low = arg.strip().lower()
        if arg_low == "switch":
            curr_idx = poke.get("ability_index", 0)
            new_idx = (curr_idx + 1) % len(records)
            poke["ability_index"] = new_idx
            await self._save_workspace(ctx)
            
            selected_ab = ab_options[new_idx]
            await ctx.send(
                embed=discord.Embed(
                    description=f"Switched ability of **{poke['pokname'].replace('-', ' ').title()}** to **{selected_ab['identifier'].replace('-', ' ').title()}** (slot {new_idx + 1}).",
                    color=discord.Color.green(),
                )
            )
        else:
            target_norm = arg_low.replace(" ", "-")
            if target_norm not in legal_names:
                ab_found = ABILITIES.get(target_norm)
                if ab_found is None:
                    # check contains
                    for key, val in ABILITIES._by_key.items():
                        if target_norm in str(key):
                            ab_found = val
                            target_norm = str(key)
                            break
                
                if ab_found is None or target_norm not in legal_names:
                    options_str = ", ".join(opt["identifier"].replace("-", " ").title() for opt in ab_options)
                    await ctx.send(f"**{poke['pokname'].replace('-', ' ').title()}** cannot have the ability **{arg}**. Legal options: {options_str}")
                    return
            
            matched_idx = legal_names.index(target_norm)
            poke["ability_index"] = matched_idx
            await self._save_workspace(ctx)
            
            selected_ab = ab_options[matched_idx]
            await ctx.send(
                embed=discord.Embed(
                    description=f"Set ability of **{poke['pokname'].replace('-', ' ').title()}** to **{selected_ab['identifier'].replace('-', ' ').title()}**.",
                    color=discord.Color.green(),
                )
            )

    # -- ;moveset ----------------------------------------------------------

    @commands.command(name="moveset")
    async def moveset(self, ctx: commands.Context):
        """Show all learnable moves for the selected Pokémon."""
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        poke = ws["pokemon"]
        pokname = poke["pokname"]
        
        legal_moves_names = get_legal_moves(pokname)
        if not legal_moves_names:
            await ctx.send(f"No learnable movesets found for **{pokname.replace('-', ' ').title()}** in the database. You can teach it any valid move using `;learn`.")
            return

        moves_data = []
        for mn in sorted(legal_moves_names):
            m_info = MOVES.get(mn)
            if m_info:
                moves_data.append(m_info)

        if not moves_data:
            await ctx.send(f"Could not load move details for **{pokname.replace('-', ' ').title()}**.")
            return

        per_page = 10
        pages = []
        total_pages = (len(moves_data) + per_page - 1) // per_page
        
        for i in range(total_pages):
            chunk = moves_data[i * per_page : (i + 1) * per_page]
            
            lines = [
                "Name             │ Type     │ Category │ Pwr │ Acc",
                "─────────────────┼──────────┼──────────┼─────┼─────"
            ]
            for move in chunk:
                name = move.get("identifier", "").replace("-", " ").title()[:16]
                t_id = move.get("type_id", 0)
                type_name = _TYPE_ID_TO_NAME.get(t_id, "Normal")[:8]
                
                dmg_class = move.get("damage_class_id", 1)
                cat = "Status"
                if dmg_class == 2:
                    cat = "Physical"
                elif dmg_class == 3:
                    cat = "Special"
                    
                pwr = str(move.get("power")) if move.get("power") is not None else "—"
                acc = str(move.get("accuracy")) if move.get("accuracy") is not None else "—"
                
                lines.append(f"{name:<16} │ {type_name:<8} │ {cat:<8} │ {pwr:<3} │ {acc:<3}")
                
            page_text = "```plaintext\n" + "\n".join(lines) + f"\n```\nPage {i + 1} of {total_pages} (Total: {len(moves_data)} moves)"
            pages.append(page_text)

        embed = discord.Embed(
            title=f"{pokname.replace('-', ' ').title()}'s Learnable Moves",
            description=pages[0],
            color=discord.Color.blue(),
        )
        
        view = MovesetView(ctx.author.id, embed, pages)
        await ctx.send(embed=embed, view=view)

    # -- ;iv ---------------------------------------------------------------

    @commands.command(name="iv")
    async def iv(self, ctx: commands.Context, stat: str, value: int):
        """
        Set an IV for the selected Pokémon.

        Usage: ;iv <hp|atk|def|spa|spd|spe> <0-31>
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        stat_low = stat.lower()
        key = _IV_KEYS.get(stat_low)
        if key is None:
            await ctx.send(f"Unknown stat `{stat}`. Use: hp, atk, def, spa, spd, spe")
            return

        if value < 0 or value > 31:
            await ctx.send("IV must be between 0 and 31.")
            return

        ws["pokemon"][key] = value
        await self._save_workspace(ctx)

        await ctx.send(
            embed=discord.Embed(
                description=f"**{ws['pokemon']['pokname'].replace('-', ' ').title()}** {stat.upper()} IV set to **{value}**.",
                color=discord.Color.green(),
            )
        )

    # -- ;evs --------------------------------------------------------------

    @commands.command(name="evs")
    async def evs(self, ctx: commands.Context, stat: str, value: int):
        """
        Set an EV for the selected Pokémon.

        Usage: ;evs <hp|atk|def|spa|spd|spe> <0-252>
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        stat_low = stat.lower()
        key = _STAT_KEYS.get(stat_low)
        if key is None:
            await ctx.send(f"Unknown stat `{stat}`. Use: hp, atk, def, spa, spd, spe")
            return

        if value < 0 or value > 252:
            await ctx.send("EV must be between 0 and 252.")
            return

        poke = ws["pokemon"]
        current_total = sum(poke.get(v, 0) for v in _STAT_KEYS.values())
        old_val = poke.get(key, 0)
        new_total = current_total - old_val + value
        if new_total > 510:
            await ctx.send(
                f"EV total would be {new_total}/510. "
                f"Reduce other EVs first (current total: {current_total})."
            )
            return

        poke[key] = value
        await self._save_workspace(ctx)

        await ctx.send(
            embed=discord.Embed(
                description=f"**{poke['pokname'].replace('-', ' ').title()}** {stat.upper()} EV set to **{value}**.\n"
                            f"Total EVs: {new_total}/510",
                color=discord.Color.green(),
            )
        )

    # -- ;nature -----------------------------------------------------------

    @commands.command(name="nature")
    async def nature(self, ctx: commands.Context, *, nature_name: str):
        """
        Set the nature for the selected Pokémon.

        Usage: ;nature <nature_name>
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        norm = nature_name.strip().lower()
        nature_data = NATURES.get(norm)
        if nature_data is None:
            await ctx.send(f"Nature **{nature_name}** not found.")
            return

        ws["pokemon"]["nature"] = norm.capitalize()
        await self._save_workspace(ctx)

        inc = nature_data.get("increased_stat_id", "?")
        dec = nature_data.get("decreased_stat_id", "?")
        await ctx.send(
            embed=discord.Embed(
                description=f"**{ws['pokemon']['pokname'].replace('-', ' ').title()}** nature set to **{norm.capitalize()}**.\n"
                            f"(+stat_id={inc}, -stat_id={dec})",
                color=discord.Color.green(),
            )
        )

    # -- ;item -------------------------------------------------------------

    @commands.command(name="item")
    async def item(self, ctx: commands.Context, *, item_name: str):
        """
        Equip an item on the selected Pokémon.

        Usage: ;item <item_name>
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        norm = item_name.strip().lower().replace(" ", "-")
        if norm not in ITEMS:
            await ctx.send(f"Item **{item_name}** not found in the item database.")
            return

        ws["pokemon"]["hitem"] = norm
        await self._save_workspace(ctx)

        await ctx.send(
            embed=discord.Embed(
                description=f"**{ws['pokemon']['pokname'].replace('-', ' ').title()}** is now holding **{norm}**.",
                color=discord.Color.green(),
            )
        )

    # -- ;qi (quick info) --------------------------------------------------

    @commands.command(name="qi", aliases=["quickinfo", "pokemoninfo"])
    async def quick_info(self, ctx: commands.Context, *, poke: str | None = None):
        """
        Show details for the selected Pokémon or a specified Pokémon species/form.

        Usage:
          ;qi
          ;qi <pokemon_name>
        """
        if poke is None:
            ws = await self._load_workspace(ctx)
            if ws is None:
                return

            poke_data = ws["pokemon"]
            from ..canvas import BattleRenderer
            from pathlib import Path

            data_dir = Path(__file__).parent.parent / "data"
            renderer = BattleRenderer(data_dir)

            try:
                img_buf = renderer.render_pokemon_card(poke_data)
                file = discord.File(fp=img_buf, filename="pokemon_card.png")

                embed = discord.Embed(
                    title=f"{poke_data.get('pokname', '?').replace('-', ' ').title()}",
                    color=discord.Color.teal(),
                )
                embed.set_image(url="attachment://pokemon_card.png")
                embed.set_footer(text=f"Team: {ws['team_name']} | Slot: {str(ws['slot_idx'] + 1) if ws['slot_idx'] is not None else 'None (Workspace)'}")

                await ctx.send(embed=embed, file=file)
            except Exception as e:
                log.exception("Failed to render pokemon card for ;qi")
                await ctx.send(f"Error rendering card: {e}")
        else:
            matched_identifier = resolve_form_identifier(poke)
            if not matched_identifier:
                await ctx.send(f"Pokémon **{poke}** not found in the forms database.")
                return

            form_info = FORMS.get(matched_identifier)
            if form_info is None:
                await ctx.send(f"Error: form info not found for {matched_identifier}.")
                return

            pokemon_id = form_info["pokemon_id"]
            
            # Get stats
            from ..core.registry import POKEMON_STATS, POKE_ABILITIES, ABILITIES
            stats_entry = POKEMON_STATS.find_one({"pokemon_id": pokemon_id})
            if stats_entry:
                raw_stats = stats_entry["stats"]
                stats_str = (
                    f"**HP**: {raw_stats[0]} | "
                    f"**ATK**: {raw_stats[1]} | "
                    f"**DEF**: {raw_stats[2]} | "
                    f"**SPA**: {raw_stats[3]} | "
                    f"**SPD**: {raw_stats[4]} | "
                    f"**SPE**: {raw_stats[5]}\n"
                    f"**Total**: {sum(raw_stats)}"
                )
            else:
                stats_str = "No base stats found."

            # Get abilities
            records = POKE_ABILITIES.by_secondary(pokemon_id)
            ability_names = []
            for r in records:
                ab_id = r["ability_id"]
                ab_data = ABILITIES.find_one({"id": ab_id})
                if ab_data:
                    ab_name = ab_data["identifier"].replace("-", " ").title()
                    if r.get("is_hidden"):
                        ab_name += " (HA)"
                    ability_names.append(ab_name)

            abilities_str = ", ".join(ability_names) if ability_names else "None"

            embed = discord.Embed(
                title=f"Pokémon Info: {matched_identifier.replace('-', ' ').title()}",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Database ID", value=str(pokemon_id), inline=True)
            embed.add_field(name="Identifier", value=matched_identifier, inline=True)
            embed.add_field(name="Possible Abilities", value=abilities_str, inline=False)
            embed.add_field(name="Base Stats", value=stats_str, inline=False)

            from pathlib import Path
            img_path = Path(__file__).parent.parent / "data" / "img" / f"{pokemon_id}.png"
            file = None
            if img_path.exists():
                file = discord.File(img_path, filename="pokemon.png")
                embed.set_thumbnail(url="attachment://pokemon.png")

            if file:
                await ctx.send(embed=embed, file=file)
            else:
                await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TeambuilderCog(bot))
