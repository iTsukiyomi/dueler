import discord
from ..enums import Ability

BUTTON_TIMEOUT = 60


class InfoButton(discord.ui.Button):
    """A button that shows the user's current pokemon info."""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Info", row=1)

    async def callback(self, interaction):
        # pyrefly: ignore [missing-attribute]
        pokemon = self.view.trainer.current_pokemon
        item = pokemon.held_item.get() if pokemon.held_item.has_item() else "None"

        ev_lines = []
        ev_mapping = [
            ("HP", pokemon.hpev),
            ("Atk", pokemon.atkev),
            ("Def", pokemon.defev),
            ("SpA", pokemon.spatkev),
            ("SpD", pokemon.spdefev),
            ("Spe", pokemon.speedev),
        ]
        for stat_name, ev_value in ev_mapping:
            if ev_value > 0:
                ev_lines.append(f"{stat_name}: `{ev_value}`")

        ev_text = "\n".join(ev_lines) if ev_lines else "None"

        ability_name = Ability(pokemon.ability_id).pretty_name

        content = (
            f"**{pokemon.name}** ({pokemon.pokemon_id})\n"
            f"Nature: `{pokemon.nature}`\n"
            f"Ability: `{ability_name}`\n"
            f"Item: `{item}`\n"
            f"EVs:\n{ev_text}"
        )

        await interaction.response.send_message(content=content, ephemeral=True)
