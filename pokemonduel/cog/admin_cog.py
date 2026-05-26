"""
pokemonduel.cog.admin_cog
==========================
Owner-only admin commands — data migration, server configuration,
AI management, and diagnostic commands.

Commands:
    ;migrate      — run JSON→MongoDB migration
    ;dbstatus     — show database health
    ;setprefix    — change guild command prefix
    ;reloaddata   — hot-reload static game data
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..core.registry import reload_all
from ..core import database, cache

log = logging.getLogger("dueler.cog.admin")


def _is_owner():
    """Check decorator that restricts a command to bot owners."""
    async def predicate(ctx: commands.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)
    return commands.check(predicate)


class AdminCog(commands.Cog, name="Admin"):
    """Owner-only server administration commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # -- ;migrate ----------------------------------------------------------

    @commands.command(name="migrate")
    @_is_owner()
    async def migrate(self, ctx: commands.Context):
        """
        Run JSON→MongoDB migration for legacy user data.

        This reads all data/PokemonDuel/member_*.json files and creates
        player profiles + legacy teams in MongoDB.

        **Owner only.**
        """
        msg = await ctx.send("⏳ Starting migration...")

        try:
            from ..core.migration import migrate as run_migration
            result = await run_migration()
        except Exception as exc:
            await msg.edit(content=f"❌ Migration failed: {exc}")
            return

        embed = discord.Embed(
            title="Migration Complete",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Players", value=str(result["players_created"]), inline=True
        )
        embed.add_field(
            name="Teams", value=str(result["teams_created"]), inline=True
        )
        embed.add_field(
            name="Errors", value=str(len(result["errors"])), inline=True
        )

        if result["errors"]:
            truncated_errors = []
            for err in result["errors"][:3]:
                if len(err) > 200:
                    truncated_errors.append(err[:197] + "...")
                else:
                    truncated_errors.append(err)
            
            error_text = "\n".join(truncated_errors)
            if len(result["errors"]) > 3:
                error_text += f"\n... and {len(result['errors']) - 3} more"
                
            if len(error_text) > 1000:
                error_text = error_text[:997] + "..."
                
            embed.add_field(name="Error Details", value=error_text, inline=False)

        await msg.edit(content=None, embed=embed)

    # -- ;dbstatus ---------------------------------------------------------

    @commands.command(name="dbstatus")
    @_is_owner()
    async def dbstatus(self, ctx: commands.Context):
        """
        Show database and cache health status.

        **Owner only.**
        """
        mongo_ok = await database.health_check()
        redis_ok = cache.is_available()

        embed = discord.Embed(
            title="Database Status",
            color=discord.Color.green() if (mongo_ok and redis_ok) else discord.Color.orange(),
        )
        embed.add_field(
            name="MongoDB",
            value="✅ Connected" if mongo_ok else "❌ Disconnected",
            inline=True,
        )
        embed.add_field(
            name="Redis",
            value="✅ Connected" if redis_ok else "⚠️ Degraded (no caching)",
            inline=True,
        )

        # Active battles count (if Redis available)
        if redis_ok:
            from ..services.battle_state_service import BattleStateService
            battle_count = await BattleStateService().get_active_count()
            embed.add_field(
                name="Active Battles", value=str(battle_count), inline=True
            )

        await ctx.send(embed=embed)

    # -- ;reloaddata -------------------------------------------------------

    @commands.command(name="reloaddata")
    @_is_owner()
    async def reload_data(self, ctx: commands.Context):
        """
        Hot-reload static game data registries from disk.

        **Owner only.**
        """
        try:
            reload_all()
            await ctx.send("✅ Static game data reloaded successfully.")
        except Exception as exc:
            await ctx.send(f"❌ Reload failed: {exc}")

    # -- ;setprefix --------------------------------------------------------

    @commands.command(name="setprefix")
    @commands.has_guild_permissions(administrator=True)
    async def setprefix(self, ctx: commands.Context, new_prefix: str):
        """
        Change the command prefix for this server.

        Usage: ;setprefix <new_prefix>
        Requires administrator permission.
        """
        if len(new_prefix) > 5:
            await ctx.send("Prefix must be 5 characters or fewer.")
            return

        try:
            from ..repositories.guild_repository import GuildRepository
            repo = GuildRepository()
            # pyrefly: ignore [missing-attribute]
            await repo.update(str(ctx.guild.id), prefix=new_prefix)
            await ctx.send(f"✅ Prefix changed to `{new_prefix}`")
        except Exception as exc:
            await ctx.send(f"❌ Failed to update prefix: {exc}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
