"""
pokemonduel.cog.party_cog
==========================
Party management commands — create, load, list, delete saved teams.

Commands:
    ;party create <name> <showdown_paste>
    ;party load <name>
    ;party list
    ;party delete <name>
    ;party rename <old_name> <new_name>
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

    # -- ;party create -----------------------------------------------------

    @commands.command(name="pcreate", aliases=["partycreate"])
    async def party_create(self, ctx: commands.Context, name: str, *, paste: str):
        """
        Save a new team from a Pokémon Showdown paste.

        Usage: ;pcreate <team_name> <paste>
        """
        # Ensure player profile exists
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
                                f"Delete it first with `;pdelete {name}`.",
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed)
                return
            raise

        pokemon_names = [p.get("pokname", "?") for p in team.get("pokemon", [])]
        desc = "\n".join(f"**{i+1}.** {n}" for i, n in enumerate(pokemon_names))

        embed = discord.Embed(
            title=f"Team \"{name}\" Created",
            description=desc,
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Load with: ;pload {name}")
        await ctx.send(embed=embed)

    # -- ;party load -------------------------------------------------------

    @commands.command(name="pload", aliases=["partyload"])
    async def party_load(self, ctx: commands.Context, *, name: str):
        """
        Load a saved team as your active party.

        Usage: ;pload <team_name>
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        success = await self._team_svc.set_active(str(ctx.author.id), name.strip())
        if not success:
            embed = discord.Embed(
                title="Team Not Found",
                description=f"No team named **{name}** found. "
                            "Use `;plist` to see your saved teams.",
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

    # -- ;party list -------------------------------------------------------

    @commands.command(name="plist", aliases=["partylist", "teams"])
    async def party_list(self, ctx: commands.Context):
        """
        List all your saved teams.

        Usage: ;plist
        """
        await self._player_svc.ensure_profile(str(ctx.author.id), ctx.author.name)

        teams = await self._team_svc.list_teams(str(ctx.author.id))
        if not teams:
            embed = discord.Embed(
                title="No Teams Saved",
                description="Create a team with `;pcreate <name> <showdown_paste>`",
                color=discord.Color.greyple(),
            )
            await ctx.send(embed=embed)
            return

        # Get active party name
        profile = await self._player_svc.get_profile(str(ctx.author.id))
        active_name = profile.get("active_party_name") if profile else None

        lines = []
        for team in teams:
            team_name = team.get("name", "?")
            pokemon = team.get("pokemon", [])
            poke_names = ", ".join(p.get("pokname", "?") for p in pokemon[:6])
            active_marker = " ⭐" if team_name == active_name else ""
            lines.append(f"**{team_name}**{active_marker}\n  └ {poke_names}")

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Teams",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="⭐ = active party  |  ;pload <name> to switch")
        await ctx.send(embed=embed)

    # -- ;party delete -----------------------------------------------------

    @commands.command(name="pdelete", aliases=["partydelete"])
    async def party_delete(self, ctx: commands.Context, *, name: str):
        """
        Delete a saved team.

        Usage: ;pdelete <team_name>
        """
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PartyCog(bot))
