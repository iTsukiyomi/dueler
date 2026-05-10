import discord
from ..moves import Move


class BattlePromptView(discord.ui.View):
    """Main battle interface view."""

    def __init__(self, battle, trainer):
        super().__init__(timeout=60)
        self.battle = battle
        self.trainer = trainer
        self.selected_move = None
        self.selected_action = None

    @discord.ui.button(label="Fight", style=discord.ButtonStyle.red)
    async def fight(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        self.selected_action = "fight"
        self.stop()

    @discord.ui.button(label="Switch", style=discord.ButtonStyle.secondary)
    async def switch(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        self.selected_action = "switch"
        self.stop()

    @discord.ui.button(label="Item", style=discord.ButtonStyle.green)
    async def item(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        self.selected_action = "item"
        self.stop()

    @discord.ui.button(label="Forfeit", style=discord.ButtonStyle.gray)
    async def forfeit(self, button, interaction):
        if interaction.user.id != self.trainer.user.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        self.selected_action = "forfeit"
        self.stop()


class MoveSelectView(discord.ui.View):
    """View for selecting a move."""

    def __init__(self, pokemon):
        super().__init__(timeout=60)
        self.pokemon = pokemon
        self.selected_move = None


class MoveButton(discord.ui.Button):
    """Button to select a move."""

    def __init__(self, move: Move, index):
        label = f"{move.pretty_name}"
        if move.pp == 0:
            label += " (No PP)"
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary if move.pp > 0 else discord.ButtonStyle.secondary,
            disabled=move.pp == 0
        )
        self.move = move
        self.index = index

    async def callback(self, interaction):
        self.view.selected_move = self.move
        self.view.stop()


class SwapRequestButton(discord.ui.Button):
    """Button for swap request."""

    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction):
        self.view.result = True
        self.view.stop()