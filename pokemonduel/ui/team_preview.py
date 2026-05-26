import discord

BUTTON_TIMEOUT = 60


class PreviewPromptView(discord.ui.View):
    """Prompts a user to select their lead pokemon when previewing both player's parties."""
    def __init__(self, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.child_views = []

    @discord.ui.button(label="Select a lead pokemon", style=discord.ButtonStyle.primary)
    async def actions(self, interaction, button):
        if interaction.user.id == self.battle.trainer1.id:
            trainer = self.battle.trainer1
        else:
            trainer = self.battle.trainer2
        view = LeadView(trainer, self.battle)
        self.child_views.append(view)
        await interaction.response.send_message(content="Pick a pokemon to lead with:", view=view, ephemeral=True)

    async def interaction_check(self, interaction):
        if interaction.user.id == self.battle.trainer1.id:
            if self.battle.trainer1.event.is_set():
                await interaction.response.send_message(content="You have already selected a lead.", ephemeral=True)
                return False
            return True
        if interaction.user.id == self.battle.trainer2.id:
            if self.battle.trainer2.event.is_set():
                await interaction.response.send_message(content="You have already selected a lead.", ephemeral=True)
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


class LeadView(discord.ui.View):
    """Shows the user their pokemon, allowing them to click one to make their lead to."""
    def __init__(self, trainer, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.battle = battle
        for poke in trainer.party:
            self.add_item(LeadButton(poke))
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class LeadButton(discord.ui.Button):
    """A button that makes the pokemon the user's lead when pressed."""
    def __init__(self, poke):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"{poke._name} | {poke.hp}hp")
        self.poke = poke

    async def callback(self, interaction):
        content = f"You will lead with {self.poke.name}. Waiting for opponent."
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.switch_poke(self.view.trainer.party.index(self.poke))
        # pyrefly: ignore [missing-attribute]
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=content, view=None)
