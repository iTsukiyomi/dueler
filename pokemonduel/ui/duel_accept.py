import discord
from discord.ext import commands
import asyncio

BUTTON_TIMEOUT = 60

class DuelAcceptView(discord.ui.View):
    """View to accept a duel."""
    def __init__(self, ctx: "commands.Context", opponent: discord.Member):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.ctx = ctx
        self.confirm = False
        self.event = asyncio.Event()
        self.opponent = opponent

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction, button):
        self.confirm = True
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction, button):
        await interaction.response.edit_message(view=None)
        self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        # pyrefly: ignore [missing-attribute]
        await self.message.edit(view=None)
        self.stop()

    async def on_error(self, interaction, error, item):
        # pyrefly: ignore [missing-attribute]
        await self.ctx.cog.log.error("Exception in a button.", exc_info=error)
