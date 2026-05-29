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

        type_ids = getattr(pokemon, 'type_ids', [])
        _TYPE_ID_TO_NAME = {
            1: "Normal", 2: "Fighting", 3: "Flying", 4: "Poison", 5: "Ground",
            6: "Rock", 7: "Bug", 8: "Ghost", 9: "Steel", 10: "Fire",
            11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
            16: "Dragon", 17: "Dark", 18: "Fairy",
        }
        type_names = [_TYPE_ID_TO_NAME.get(tid, "???") for tid in type_ids]
        type_str = " / ".join(type_names) if type_names else "Unknown"

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
            f"**{pokemon.name}** (#{pokemon.pokemon_id})\n"
            f"Type: `{type_str}`\n"
            f"Nature: `{pokemon.nature}`\n"
            f"Ability: `{ability_name}`\n"
            f"Item: `{item}`\n"
            f"EVs:\n{ev_text}"
        )

        await interaction.response.send_message(content=content, ephemeral=True)
