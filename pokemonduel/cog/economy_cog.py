"""
pokemonduel.cog.economy_cog
=============================
Economy and ranking commands — balance, deposit, withdraw,
leaderboard, rank, and profile.

Commands:
    ;balance / ;bal
    ;deposit <amount>
    ;withdraw <amount>
    ;leaderboard / ;lb
    ;rank [user]
    ;profile [user]
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..services.player_service import PlayerService

log = logging.getLogger("dueler.cog.economy")


class EconomyCog(commands.Cog, name="Economy"):
    """Economy, rankings, and player profiles."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._svc = PlayerService()

    # -- ;balance ----------------------------------------------------------

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx: commands.Context):
        """
        Check your wallet balance.

        Usage: ;balance
        """
        await self._svc.ensure_profile(str(ctx.author.id), ctx.author.name)
        bal = await self._svc.get_balance(str(ctx.author.id))

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Balance",
            color=discord.Color.gold(),
        )
        embed.add_field(name="💰 Wallet", value=f"¥{bal['wallet']:,}", inline=True)
        await ctx.send(embed=embed)

    # -- ;leaderboard ------------------------------------------------------

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """
        Show the top players by Elo rating.

        Usage: ;leaderboard [page]
        """
        page = max(1, page)
        per_page = 10
        offset = (page - 1) * per_page

        entries = await self._svc.get_leaderboard(offset, per_page)
        if not entries:
            await ctx.send("The leaderboard is empty.")
            return

        lines = []
        for i, entry in enumerate(entries):
            rank = offset + i + 1
            user_id = entry.get("_id")
            
            resolved_name = entry.get("username", "Unknown")
            if user_id:
                try:
                    user = self.bot.get_user(int(user_id))
                    if user is None:
                        user = await self.bot.fetch_user(int(user_id))
                    if user:
                        resolved_name = user.name
                except Exception:
                    pass

            elo = entry.get("elo", 1000)
            wins = entry.get("wins", 0)
            losses = entry.get("losses", 0)

            medal = ""
            if rank == 1:
                medal = "🥇 "
            elif rank == 2:
                medal = "🥈 "
            elif rank == 3:
                medal = "🥉 "

            lines.append(
                f"{medal}**#{rank}** {resolved_name} — Elo: **{elo}** ({wins}W/{losses}L)"
            )

        embed = discord.Embed(
            title="🏆 Elo Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Page {page}")
        await ctx.send(embed=embed)

    # -- ;rank -------------------------------------------------------------

    @commands.command(name="rank")
    # pyrefly: ignore [bad-function-definition]
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """
        Show a player's rank and Elo.

        Usage: ;rank [user]
        """
        target = member or ctx.author
        await self._svc.ensure_profile(str(target.id), target.name)

        profile = await self._svc.get_profile(str(target.id))
        rank = await self._svc.get_rank(str(target.id))

        if profile is None:
            await ctx.send("Profile not found.")
            return

        elo = profile.get("elo", 1000)
        wins = profile.get("wins", 0)
        losses = profile.get("losses", 0)
        total = wins + losses
        win_rate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"

        embed = discord.Embed(
            title=f"{target.name}'s Rank",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Rank", value=f"#{rank}" if rank else "Unranked", inline=True)
        embed.add_field(name="Elo", value=str(elo), inline=True)
        embed.add_field(name="Record", value=f"{wins}W / {losses}L ({win_rate})", inline=True)
        await ctx.send(embed=embed)

    # -- ;profile ----------------------------------------------------------

    @commands.command(name="profile", aliases=["prof"])
    # pyrefly: ignore [bad-function-definition]
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        """
        Show a player's full profile.

        Usage: ;profile [user]
        """
        target = member or ctx.author
        await self._svc.ensure_profile(str(target.id), target.name)

        profile = await self._svc.get_profile(str(target.id))
        rank = await self._svc.get_rank(str(target.id))

        if profile is None:
            await ctx.send("Profile not found.")
            return

        elo = profile.get("elo", 1000)
        wins = profile.get("wins", 0)
        losses = profile.get("losses", 0)
        wallet = profile.get("wallet", 0)
        active_team = profile.get("active_party_name") or "None"
        total = wins + losses
        win_rate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"

        embed = discord.Embed(
            title=f"{target.name}'s Profile",
            color=discord.Color.purple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Rank", value=f"#{rank}" if rank else "Unranked", inline=True)
        embed.add_field(name="Elo", value=str(elo), inline=True)
        embed.add_field(name="Record", value=f"{wins}W / {losses}L ({win_rate})", inline=True)
        embed.add_field(name="💰 Wallet", value=f"¥{wallet:,}", inline=True)
        embed.add_field(name="Active Team", value=active_team, inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EconomyCog(bot))
