"""
pokemonduel.cog.party_cog
==========================
Party management commands — create, load, list, delete saved teams, and customize active slots.

Commands:
    ;party create <name> <showdown_paste>
    ;party load <name>
    ;party list
    ;party delete <name>
    ;party add <slot>
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..services.team_service import TeamService
from ..services.player_service import PlayerService

log = logging.getLogger("dueler.cog.party")


class PartyCog(commands.Cog, name="Party"):
    """Manage your Pokémon teams — save, load, and organise parties."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._team_svc = TeamService()
        self._player_svc = PlayerService()

    # -- Group root --------------------------------------------------------

    @commands.group(name="party", invoke_without_command=True)
    async def party(self, ctx: commands.Context):
        """Party management command group. Use ;party --help for subcommands."""
        if ctx.invoked_subcommand is None:
            await self._list_impl(ctx)

    # -- Implementation Details ---------------------------------------------

    async def _create_impl(self, ctx: commands.Context, name: str, paste: str) -> None:
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        try:
            team = await self._team_svc.create_from_showdown(
                str(ctx.author.id), name, paste
            )
        except ValueError as exc:
            embed = discord.Embed(
                title="Team Creation Failed",
                description=str(exc),
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return
        except Exception as exc:
            if "duplicate key" in str(exc).lower():
                embed = discord.Embed(
                    title="Name Taken",
                    description=f"You already have a team named **{name}**. "
                                f"Delete it first with `;party delete {name}`.",
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed)
                return
            raise

        pokemon_names = [p.get("pokname", "?") for p in team.get("pokemon", [])]
        desc = "\n".join(f"**{i+1}.** {n.replace('-', ' ').title()}" for i, n in enumerate(pokemon_names))

        embed = discord.Embed(
            title=f"Team \"{name}\" Created",
            description=desc,
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Load with: ;party load {name}")
        await ctx.send(embed=embed)

    async def _load_impl(self, ctx: commands.Context, name: str) -> None:
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        success = await self._team_svc.set_active(str(ctx.author.id), name.strip())
        if not success:
            embed = discord.Embed(
                title="Team Not Found",
                description=f"No team named **{name}** found. "
                            "Use `;party list` to see your saved teams.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"Team \"{name}\" Loaded",
            description="This team is now your active party for battles.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    async def _list_impl(self, ctx: commands.Context) -> None:
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        teams = await self._team_svc.list_teams(str(ctx.author.id))
        if not teams:
            embed = discord.Embed(
                title="No Teams Saved",
                description="Create a team with `;party create <name> <showdown_paste>`",
                color=discord.Color.greyple(),
            )
            await ctx.send(embed=embed)
            return

        profile = await self._player_svc.get_profile(str(ctx.author.id))
        active_name = profile.get("active_party_name") if profile else None

        lines = []
        for team in teams:
            team_name = team.get("name", "?")
            pokemon = team.get("pokemon", [])
            poke_names = ", ".join(p.get("pokname", "?").replace("-", " ").title() for p in pokemon[:6])
            active_marker = " ⭐" if team_name == active_name else ""
            lines.append(f"**{team_name}**{active_marker}\n  └ {poke_names}")

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Teams",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="⭐ = active party  |  ;party load <name> to switch")
        await ctx.send(embed=embed)

    async def _delete_impl(self, ctx: commands.Context, name: str) -> None:
        deleted = await self._team_svc.delete_team(str(ctx.author.id), name.strip())
        if not deleted:
            embed = discord.Embed(
                title="Team Not Found",
                description=f"No team named **{name}** found.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"Team \"{name}\" Deleted",
            color=discord.Color.dark_grey(),
        )
        await ctx.send(embed=embed)

    # -- Subcommands --------------------------------------------------------

    @party.command(name="create")
    async def party_create(self, ctx: commands.Context, name: str, *, paste: str):
        """Save a new team from a Pokémon Showdown paste."""
        await self._create_impl(ctx, name, paste)

    @party.command(name="load")
    async def party_load(self, ctx: commands.Context, *, name: str):
        """Load a saved team as your active party."""
        await self._load_impl(ctx, name)

    @party.command(name="list")
    async def party_list(self, ctx: commands.Context):
        """List all your saved teams."""
        await self._list_impl(ctx)

    @party.command(name="delete")
    async def party_delete(self, ctx: commands.Context, *, name: str):
        """Delete a saved team."""
        await self._delete_impl(ctx, name)

    @party.command(name="add")
    async def party_add(self, ctx: commands.Context, slot: int):
        """
        Add the currently selected/customized Pokémon to active team.

        Usage: ;party add <slot_number>  (1-6)
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        tb_cog = self.bot.get_cog("Teambuilder")
        if tb_cog is None:
            await ctx.send("Teambuilder system is currently unavailable.")
            return

        ws_dict = getattr(tb_cog, "_workspace", None)
        if ws_dict is None:
            await ctx.send("Teambuilder system is currently unavailable.")
            return
        ws = ws_dict.get(str(ctx.author.id))
        if ws is None or ws.get("pokemon") is None:
            await ctx.send(
                embed=discord.Embed(
                    title="No Pokémon Selected",
                    description="Use `;select <name>` or `;select <slot>` first to pick a Pokémon.",
                    color=discord.Color.red(),
                )
            )
            return

        if slot < 1 or slot > 6:
            await ctx.send("Slot number must be between 1 and 6.")
            return

        profile = await self._player_svc.get_profile(str(ctx.author.id))
        active_party_name = profile.get("active_party_name") if profile else None
        if not active_party_name:
            await ctx.send(
                embed=discord.Embed(
                    title="No Active Team",
                    description="You do not have an active team loaded. Create one with `;party create <name> <paste>` or load one with `;party load <name>` first.",
                    color=discord.Color.red(),
                )
            )
            return

        party = await self._team_svc.load_active_party(str(ctx.author.id))
        if party is None:
            party = []

        # Pad party with default slots up to the requested slot if it's smaller
        while len(party) < slot:
            party.append({
                "id": 0,
                "pokname": "pikachu",
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
                "ability_index": 0,
                "gender": "",
                "shiny": False,
                "radiant": False,
                "skin": None,
            })

        # Overwrite the slot
        party[slot - 1] = ws["pokemon"].copy()

        await self._team_svc.update_team(str(ctx.author.id), active_party_name, party)

        # Update the workspace metadata
        ws["slot_idx"] = slot - 1
        ws["team_name"] = active_party_name

        pokemon_name = ws["pokemon"].get("pokname", "?")
        embed = discord.Embed(
            title="Added to Party",
            description=f"Added **{pokemon_name.replace('-', ' ').title()}** to slot {slot} of team **{active_party_name}**.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    # -- Top-level Legacy Aliases --------------------------------------------

    @commands.command(name="pcreate", aliases=["partycreate"], hidden=True)
    async def pcreate_alias(self, ctx: commands.Context, name: str, *, paste: str):
        await self._create_impl(ctx, name, paste)

    @commands.command(name="pload", aliases=["partyload"], hidden=True)
    async def pload_alias(self, ctx: commands.Context, *, name: str):
        await self._load_impl(ctx, name)

    @commands.command(name="plist", aliases=["partylist", "teams"], hidden=True)
    async def plist_alias(self, ctx: commands.Context):
        await self._list_impl(ctx)

    @commands.command(name="pdelete", aliases=["partydelete"], hidden=True)
    async def pdelete_alias(self, ctx: commands.Context, *, name: str):
        await self._delete_impl(ctx, name)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PartyCog(bot))
