import discord


class MegaEvolveButton(discord.ui.Button):
    """A button that toggles whether the trainer's pokemon should mega evolve this turn."""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Mega Evolve", row=0)

    def get_color(self):
        # pyrefly: ignore [missing-attribute]
        return [discord.ButtonStyle.gray, discord.ButtonStyle.green][self.view.trainer.current_pokemon.should_mega_evolve]

    async def callback(self, interaction):
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.current_pokemon.should_mega_evolve = not self.view.trainer.current_pokemon.should_mega_evolve
        self.style = self.get_color()
        await interaction.response.edit_message(view=self.view)
