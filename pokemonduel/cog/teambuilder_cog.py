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

from ..core.registry import MOVES, NATURES, ITEMS, ABILITIES
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


class TeambuilderCog(commands.Cog, name="Teambuilder"):
    """Customise individual Pokémon — moves, EVs, IVs, nature, ability, item."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._team_svc = TeamService()
        self._player_svc = PlayerService()
        # Per-user workspace: {user_id: {"team_name": str, "slot_idx": int, "pokemon": dict}}
        self._workspace: dict[str, dict] = {}

    # -- Helpers -----------------------------------------------------------

    async def _load_workspace(self, ctx: commands.Context) -> dict | None:
        """Return the current workspace Pokémon, or None with an error message."""
        ws = self._workspace.get(str(ctx.author.id))
        if ws is None:
            await ctx.send(
                embed=discord.Embed(
                    title="No Pokémon Selected",
                    description="Use `;select <slot_number>` to pick a Pokémon from your active team.",
                    color=discord.Color.red(),
                )
            )
            return None
        return ws

    async def _save_workspace(self, ctx: commands.Context) -> None:
        """Persist workspace changes back to the team in MongoDB."""
        ws = self._workspace.get(str(ctx.author.id))
        if ws is None:
            return

        party = await self._team_svc.load_active_party(str(ctx.author.id))
        if party is None or ws["slot_idx"] >= len(party):
            return

        party[ws["slot_idx"]] = ws["pokemon"]
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        if profile and profile.get("active_party_name"):
            await self._team_svc.update_team(
                str(ctx.author.id),
                profile["active_party_name"],
                party,
            )

    # -- ;select -----------------------------------------------------------

    @commands.command(name="select")
    async def select(self, ctx: commands.Context, slot: int):
        """
        Select a Pokémon from your active team to customise.

        Usage: ;select <slot_number>  (1-6)
        """
        if slot < 1 or slot > 6:
            await ctx.send("Slot must be between 1 and 6.")
            return

        party = await self._team_svc.load_active_party(str(ctx.author.id))
        if party is None:
            await ctx.send(
                embed=discord.Embed(
                    title="No Active Team",
                    description="Load a team first with `;pload <team_name>`.",
                    color=discord.Color.red(),
                )
            )
            return

        if slot > len(party):
            await ctx.send(f"Your team only has {len(party)} Pokémon.")
            return

        idx = slot - 1
        pokemon = party[idx]
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        team_name = profile.get("active_party_name", "?") if profile else "?"

        self._workspace[str(ctx.author.id)] = {
            "team_name": team_name,
            "slot_idx": idx,
            "pokemon": pokemon.copy(),
        }

        embed = discord.Embed(
            title=f"Selected: {pokemon.get('pokname', '?')}",
            description=f"Slot {slot} of team **{team_name}**\n"
                        "Use `;learn`, `;iv`, `;evs`, `;nature`, `;ability`, `;item` to customise.\n"
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
        while len(poke["moves"]) < 4:
            poke["moves"].append("tackle")
        poke["moves"][slot - 1] = norm

        await self._save_workspace(ctx)

        move_data = MOVES.get(norm)
        power = move_data.get("power", "—") if move_data else "—"
        await ctx.send(
            embed=discord.Embed(
                title=f"Move Learned",
                description=f"**{poke['pokname']}** learned **{norm}** in slot {slot}.\n"
                            f"Power: {power}",
                color=discord.Color.green(),
            )
        )

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
                description=f"**{ws['pokemon']['pokname']}** {stat.upper()} IV set to **{value}**.",
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

        # Check total EV limit (510)
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
                description=f"**{poke['pokname']}** {stat.upper()} EV set to **{value}**.\n"
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
        if norm not in NATURES:
            await ctx.send(f"Nature **{nature_name}** not found.")
            return

        nature_data = NATURES.get(norm)
        ws["pokemon"]["nature"] = norm.capitalize()
        await self._save_workspace(ctx)

        inc = nature_data.get("increased_stat_id", "?")
        dec = nature_data.get("decreased_stat_id", "?")
        await ctx.send(
            embed=discord.Embed(
                description=f"**{ws['pokemon']['pokname']}** nature set to **{norm.capitalize()}**.\n"
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
                description=f"**{ws['pokemon']['pokname']}** is now holding **{norm}**.",
                color=discord.Color.green(),
            )
        )

    # -- ;qi (quick info) --------------------------------------------------

    @commands.command(name="qi", aliases=["quickinfo", "pokemoninfo"])
    async def quick_info(self, ctx: commands.Context):
        """
        Show full details for the selected Pokémon.

        Usage: ;qi
        """
        ws = await self._load_workspace(ctx)
        if ws is None:
            return

        poke = ws["pokemon"]
        from ..canvas import BattleRenderer
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data"
        renderer = BattleRenderer(data_dir)

        try:
            img_buf = renderer.render_pokemon_card(poke)
            file = discord.File(fp=img_buf, filename="pokemon_card.png")

            embed = discord.Embed(
                title=f"{poke.get('pokname', '?').replace('-', ' ').title()}",
                color=discord.Color.teal(),
            )
            embed.set_image(url="attachment://pokemon_card.png")
            embed.set_footer(text=f"Team: {ws['team_name']} | Slot: {ws['slot_idx'] + 1}")

            await ctx.send(embed=embed, file=file)
        except Exception as e:
            log.exception("Failed to render pokemon card for ;qi")
            await ctx.send(f"Error rendering card: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TeambuilderCog(bot))
