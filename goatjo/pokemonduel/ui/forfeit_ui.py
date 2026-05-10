import discord


class DuelForfeitView(discord.ui.View):
    """View for confirming forfeit."""

    def __init__(self, trainer):
        super().__init__(timeout=60)
        self.trainer = trainer
        self.confirmed = False

    @discord.ui.button(label="Forfeit", style=discord.ButtonStyle.danger)
    async def confirm_forfeit(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your choice!", ephemeral=True)
            return
        self.confirmed = True
        self.stop()

    @discord.ui.button(label="Stay", style=discord.ButtonStyle.green)
    async def cancel_forfeit(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your choice!", ephemeral=True)
            return
        self.confirmed = False
        self.stop()


class ForfeitButton(discord.ui.Button):
    """Button for forfeit."""

    def __init__(self):
        super().__init__(label="Forfeit", style=discord.ButtonStyle.danger)

    async def callback(self, interaction):
        self.view.confirmed = True
        self.view.stop()