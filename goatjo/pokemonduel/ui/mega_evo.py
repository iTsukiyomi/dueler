import discord


class MegaEvolveButton(discord.ui.Button):
    """Button to mega evolve."""

    def __init__(self):
        super().__init__(label="Mega Evolve", style=discord.ButtonStyle.primary)

    async def callback(self, interaction):
        self.view.mega_evolve = True
        self.view.stop()