import discord


class DuelAcceptView(discord.ui.View):
    """View to accept a duel."""

    def __init__(self, ctx, opponent):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.opponent = opponent
        self.result = None

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, button, interaction):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("You're not the opponent!", ephemeral=True)
            return
        self.result = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, button, interaction):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("You're not the opponent!", ephemeral=True)
            return
        self.result = False
        self.stop()

    async def interaction_check(self, interaction):
        return interaction.user.id == self.opponent.id