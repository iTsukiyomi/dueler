import discord

BUTTON_TIMEOUT = 60


class DuelForfeitView(discord.ui.View):
    """View to forfeit a duel."""
    def __init__(self, trainer):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.confirm = False
    
    @discord.ui.button(label="Forfeit", style=discord.ButtonStyle.red)
    async def actuallyforfeit(self, interaction, button):
        await interaction.response.edit_message(content="Forfeited.", view=None)
        self.confirm = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Not forfeiting.", view=None)
        self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True
    
    async def on_error(self, interaction, error, item):
        await self.trainer.party[0].held_item.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class ForfeitButton(discord.ui.Button):
    """A button that forfeits the game when pressed."""
    def __init__(self, *, row=1):
        super().__init__(style=discord.ButtonStyle.danger, label="Forfeit duel", row=row)

    async def callback(self, interaction):
        view = DuelForfeitView(self.view.trainer)
        self.view.child_views.append(view)
        await interaction.response.send_message(content="Are you sure you want to forfeit?", view=view, ephemeral=True)
        await view.wait()
        if view.confirm:
            self.view.trainer.event.set()
