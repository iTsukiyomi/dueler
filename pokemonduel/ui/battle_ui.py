import discord
from ..moves import Move
from .mega_evo import MegaEvolveButton
from .forfeit_ui import ForfeitButton
from .swap_ui import SwapView
from .info_view import InfoButton

BUTTON_TIMEOUT = 60


class BattlePromptView(discord.ui.View):
    """Prompts users to select an action for their turn."""
    def __init__(self, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.turn = battle.turn
        self.child_views = []

    @discord.ui.button(label="FIGHT", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def actions(self, interaction, button):
        if interaction.user.id == self.battle.trainer1.id:
            trainer = self.battle.trainer1
            opponent = self.battle.trainer2
        else:
            trainer = self.battle.trainer2
            opponent = self.battle.trainer1
        view = MoveSelectView(self.battle, trainer, opponent)
        self.child_views.append(view)
        await interaction.response.send_message(content="Pick an action:", view=view, ephemeral=True)

    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        if self.battle.trainer1.is_human() and interaction.user.id == self.battle.trainer1.id:
            if self.battle.trainer1.selected_action is not None:
                await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
                return False
            return True
        if self.battle.trainer2.is_human() and interaction.user.id == self.battle.trainer2.id:
            if self.battle.trainer2.selected_action is not None:
                await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
                return False
            return True
        return False

    async def on_timeout(self):
        self.battle.trainer1.event.set()
        self.battle.trainer2.event.set()

    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)

    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class MoveSelectView(discord.ui.View):
    """Prompts the user to pick a move, enter the swap pokes view, or cancel the duel."""
    def __init__(self, battle, trainer, opponent):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.turn = battle.turn
        self.trainer = trainer
        self.opponent = opponent
        self.child_views = []
        status_code, movedata = trainer.valid_moves(opponent.current_pokemon)
        if status_code == "forced":
            trainer.selected_action = movedata
            trainer.event.set()
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="You were forced to play:", disabled=True))
            self.add_item(MoveButton(movedata, disabled=True))
            return
        swapdata = trainer.valid_swaps(opponent.current_pokemon, battle)
        if status_code == "struggle":
            self.add_item(MoveButton(Move.struggle()))
            self.add_item(SwapRequestButton(disabled=not swapdata))
            self.add_item(InfoButton())
            self.add_item(ForfeitButton(row=0))
            return

        for idx, move in enumerate(trainer.current_pokemon.moves):
            self.add_item(MoveButton(move, disabled=idx not in movedata, row=idx // 2))
        self.add_item(SwapRequestButton(disabled=not swapdata))
        self.add_item(InfoButton())
        self.add_item(ForfeitButton())
        if (
            trainer.current_pokemon is not None
            and trainer.current_pokemon.mega_type_ids is not None
            and not trainer.has_mega_evolved
        ):
            self.add_item(MegaEvolveButton())

    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        # Should never be hit, but just in case :P.
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        if self.trainer.selected_action is not None:
            await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
            return False
        return True

    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)

    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class MoveButton(discord.ui.Button):
    """A button that represents a selection of a specific move."""
    def __init__(self, move, *, disabled=False, row=0):
        label = f"{move.pretty_name}"
        if move.id != 165:
            label += f" | {move.pp}pp"
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=disabled, row=row)
        self.move = move

    async def callback(self, interaction):
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.selected_action = self.move
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=f"You picked {self.move.pretty_name}. Waiting for opponent.", view=None)


class SwapRequestButton(discord.ui.Button):
    """A button that represents a request to swap pokemon."""
    def __init__(self, *, disabled=False):
        super().__init__(style=discord.ButtonStyle.primary, label="Swap pokemon", disabled=disabled)

    async def callback(self, interaction):
        # pyrefly: ignore [missing-attribute]
        view = SwapView(self.view.trainer, self.view.opponent, self.view.battle, set_move=True)
        # pyrefly: ignore [missing-attribute]
        self.view.child_views.append(view)
        await interaction.response.edit_message(content="Pick a pokemon:", view=view)
