from .expiring_item import ExpiringItem
from ..enums import Ability, ElementType


class Terrain(ExpiringItem):
    """The terrain of the battle"""

    def __init__(self, battle):
        super().__init__()
        self.battle = battle

    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        if expired:
            self.end()
        return expired

    # pyrefly: ignore [bad-override-param-name]
    def set(self, item, attacker):
        """
        Set the terrain and turns until expiration.

        Returns a formatted string.
        """
        if item == self.item:
            return f"There's already a {item} terrain!\n"
        turns = 8 if attacker.held_item == "terrain-extender" else 5
        super().set(item, turns)
        msg = f"{attacker.name} creates a{'n' if item == 'electric' else ''} {item} terrain!\n"
        element = None
        if item == "electric":
            element = ElementType.ELECTRIC
        elif item == "grassy":
            element = ElementType.GRASS
        elif item == "misty":
            element = ElementType.FAIRY
        elif item == "psychic":
            element = ElementType.PSYCHIC
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.MIMICRY:
                poke.type_ids = [element]
                t = ElementType(element).name.lower()
                msg += f"{poke.name} became a {t} type using its mimicry!\n"
            if poke.held_item == "electric-seed" and item == "electric":
                msg += poke.append_defense(1, attacker=poke, source="its electric seed")
                # pyrefly: ignore [missing-attribute]
                poke.held_item.use()
            if poke.held_item == "psychic-seed" and item == "psychic":
                msg += poke.append_spdef(1, attacker=poke, source="its psychic seed")
                # pyrefly: ignore [missing-attribute]
                poke.held_item.use()
            if poke.held_item == "misty-seed" and item == "misty":
                msg += poke.append_spdef(1, attacker=poke, source="its misty seed")
                # pyrefly: ignore [missing-attribute]
                poke.held_item.use()
            if poke.held_item == "grassy-seed" and item == "grassy":
                msg += poke.append_defense(1, attacker=poke, source="its grassy seed")
                # pyrefly: ignore [missing-attribute]
                poke.held_item.use()
        return msg

    def end(self):
        """Ends the terrain."""
        super().end()
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.MIMICRY:
                poke.type_ids = poke.starting_type_ids.copy()
