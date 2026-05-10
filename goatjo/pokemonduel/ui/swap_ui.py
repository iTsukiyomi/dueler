import discord


class SwapPromptView(discord.ui.View):
    """View for swapping pokemon."""

    def __init__(self, trainer):
        super().__init__(timeout=60)
        self.trainer = trainer
        self.selected_pokemon = None

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        self.selected_pokemon = None
        self.stop()


class SwapView(discord.ui.View):
    """View for selecting pokemon to swap in."""

    def __init__(self, trainer):
        super().__init__(timeout=60)
        self.trainer = trainer
        self.selected_index = None


class SwapButton(discord.ui.Button):
    """Button to select a pokemon to swap to."""

    def __init__(self, pokemon, index):
        label = f"{index + 1}. {pokemon.pretty_name}"
        if pokemon.hp == 0:
            label += " (Fainted)"
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary if pokemon.hp > 0 else discord.ButtonStyle.secondary,
            disabled=pokemon.hp == 0
        )
        self.pokemon = pokemon
        self.index = index

    async def callback(self, interaction):
        if interaction.user.id != self.view.trainer.user.id:
            await interaction.response.send_message("Not your pokemon!", ephemeral=True)
            return
        self.view.selected_index = self.index
        self.view.stop()