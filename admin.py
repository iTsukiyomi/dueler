from discord.ext import commands
import subprocess
from typing import List


def git(cmd: List[str]):
    result = subprocess.run(
        ["git"] + cmd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()



class Admin(commands.Cog, name="DevAdmin"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"pong {round(self.bot.latency * 1000)}ms")

    @commands.command(name="refresh", aliases=['reload'])
    @commands.is_owner()
    async def refresh(self, ctx):
        try:
            diff = git(["diff", "--stat"])
            if not diff:
                diff = "change something first bruh"
            status = git(["status", "--porcelain"])
            if not status:
                diff = "change something first bruh"
            await self.bot.reload_extension('pokemonduel')
            msg = (
                "```diff\n"
                f"{diff}\n"
                "```\n"
                f"reloaded ``pokemonduel``"
            )
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"no\n{e}")

    @commands.command(name="push")
    @commands.is_owner()
    async def push(self, ctx, *, args: str):
        try:
            tag = None
            if "tag" in args:
                args, tag = args.split("tag=", 1)
                tag = tag.strip()
            commit_msg = args.strip().strip('"')
            if not commit_msg:
                return await ctx.send("lil bro add commit msg")
            status = git(["status", "--porcelain"])
            if status:
                git(["add", "."])
                git(["commit", "-m", commit_msg])
            if tag:
                git(["tag", tag])
            git(["push"])
            if tag:
                git(["push", "origin", tag])
            await ctx.send(f"pushed commit\n{commit_msg}" + (f"\ntag {tag}" if tag else ""))
        except Exception as e:
            await ctx.send(f"no\n{e}")

async def setup(bot):
    await bot.add_cog(Admin(bot))