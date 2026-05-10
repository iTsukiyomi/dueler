import discord
import asyncio


class DuelAcceptView(discord.ui.View):
    """View to accept a duel."""

    def __init__(self, ctx, opponent):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.confirm = False
        self.event = asyncio.Event()
        self.opponent = opponent

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction, button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("You're not the opponent!", ephemeral=True)
            return
        self.confirm = True
        await interaction.response.edit_message(view=None)
        self.event.set()
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction, button):
        await interaction.response.edit_message(view=None)
        self.stop()

    async def interaction_check(self, interaction):
        return interaction.user.id == self.opponent.id