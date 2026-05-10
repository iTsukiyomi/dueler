import discord


class PreviewPromptView(discord.ui.View):
    """View for previewing team before battle."""

    def __init__(self, battle):
        super().__init__(timeout=60)
        self.battle = battle
        self.result = None

    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green)
    async def ready(self, button, interaction):
        self.result = True
        self.stop()


class LeadView(discord.ui.View):
    """View for selecting lead pokemon."""

    def __init__(self, trainer):
        super().__init__(timeout=60)
        self.trainer = trainer
        self.lead = None

    @discord.ui.button(label="Select Lead", style=discord.ButtonStyle.primary)
    async def select_lead(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your button!", ephemeral=True)
            return
        self.stop()


class LeadButton(discord.ui.Button):
    """Button to select a lead pokemon."""

    def __init__(self, pokemon, index):
        super().__init__(
            label=f"{index + 1}. {pokemon.pretty_name}",
            style=discord.ButtonStyle.primary
        )
        self.pokemon = pokemon
        self.index = index

    async def callback(self, interaction):
        self.view.lead = self.pokemon
        self.view.stop()