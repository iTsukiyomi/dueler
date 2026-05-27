import discord

BUTTON_TIMEOUT = 60



class SwapPromptView(discord.ui.View):
    """Prompts the trainer to view their pokemon."""
    def __init__(self, trainer, opponent, battle, *, mid_turn=False):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.opponent = opponent
        self.battle = battle
        self.turn = battle.turn
        self.mid_turn = mid_turn
        self.child_views = []

    @discord.ui.button(label="POKéMON", style=discord.ButtonStyle.primary, emoji="🔄")
    async def swap(self, interaction, button):
        view = SwapView(self.trainer, self.opponent, self.battle, mid_turn=self.mid_turn)
        self.child_views.append(view)
        await interaction.response.send_message(
            content="Pick a pokemon to swap to:",
            view=view,
            ephemeral=True
        )

    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True

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


class SwapView(discord.ui.View):
    """Shows the user their pokemon, allowing them to click one to swap to."""
    def __init__(self, trainer, opponent, battle, *, set_move=False, mid_turn=False):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.opponent = opponent
        self.battle = battle
        self.set_move = set_move
        self.mid_turn = mid_turn
        swapdata = trainer.valid_swaps(opponent.current_pokemon, battle, check_trap=set_move)
        for idx, poke in enumerate(trainer.party):
            self.add_item(SwapButton(poke, disabled=idx not in swapdata))
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class SwapButton(discord.ui.Button):
    """A button that swaps to that pokemon when pressed."""
    def __init__(self, poke, *, disabled=False):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"{poke._name} | {poke.hp}/{poke.starting_hp}hp", disabled=disabled)
        self.poke = poke

    async def callback(self, interaction):
        content = f"You picked {self.poke.name}."
        # pyrefly: ignore [missing-attribute]
        if self.view.set_move:
            # pyrefly: ignore [missing-attribute]
            self.view.trainer.selected_action = self.view.trainer.party.index(self.poke)
            content += " Waiting for opponent."
        else:
            # pyrefly: ignore [missing-attribute]
            self.view.trainer.switch_poke(self.view.trainer.party.index(self.poke), mid_turn=self.view.mid_turn)
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=content, view=None)
