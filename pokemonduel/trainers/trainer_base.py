import asyncio
from ..enums import Ability, DamageClass, ElementType
from ..misc import ExpiringEffect, ExpiringWish, ExpiringItem


class Trainer():
    """Base trainer class."""

    def __init__(self, name: str, party: list):
        self.name = name
        self.party = party
        self.current_pokemon = party[0] if len(party) > 0 else None
        for poke in self.party:
            poke.owner = self
        self.event = asyncio.Event()
        self.selected_action = None
        self.mid_turn_remove = False
        self.baton_pass = None
        self.spikes = 0
        self.toxic_spikes = 0
        self.stealth_rock = False
        self.sticky_web = False
        # Int - The last index of self.party that was selected.
        self.last_idx = 0
        self.wish = ExpiringWish()
        self.aurora_veil = ExpiringEffect(0)
        self.light_screen = ExpiringEffect(0)
        self.reflect = ExpiringEffect(0)
        self.mist = ExpiringEffect(0)
        self.safeguard = ExpiringEffect(0)
        # Boolean - Whether the next poke to swap in should be restored via healing wish.
        self.healing_wish = False
        # Boolean - Whether the next poke to swap in should be restored via lunar dance.
        self.lunar_dance = False
        # ExpiringEffect - Stores the number of turns that pokes have doubled speed.
        self.tailwind = ExpiringEffect(0)
        self.mud_sport = ExpiringEffect(0)
        self.water_sport = ExpiringEffect(0)
        self.retaliate = ExpiringEffect(0)
        self.future_sight = ExpiringItem()
        self.has_mega_evolved = False
        self.num_fainted = 0
        self.next_substitute = 0

    def has_alive_pokemon(self) -> bool:
        """Returns True if this trainer still has at least one pokemon that is alive."""
        return any((poke.hp > 0 for poke in self.party))

    def next_turn(self, battle):
        """
        Updates this trainer for a new turn.

        Returns a formatted message.
        """
        msg = ""
        self.selected_action = None
        self.mid_turn_remove = False
        hp = self.wish.next_turn()
        if hp and self.current_pokemon is not None:
            msg += self.current_pokemon.heal(hp, source="its wish")
        if self.aurora_veil.next_turn():
            msg += f"{self.name}'s aurora veil wore off!\n"
        if self.light_screen.next_turn():
            msg += f"{self.name}'s light screen wore off!\n"
        if self.reflect.next_turn():
            msg += f"{self.name}'s reflect wore off!\n"
        if self.mist.next_turn():
            msg += f"{self.name}'s mist wore off!\n"
        if self.safeguard.next_turn():
            msg += f"{self.name}'s safeguard wore off!\n"
        if self.tailwind.next_turn():
            msg += f"{self.name}'s tailwind died down!\n"
        if self.mud_sport.next_turn():
            msg += f"{self.name}'s mud sport wore off!\n"
        if self.water_sport.next_turn():
            msg += f"{self.name}'s water sport evaporated!\n"
        self.retaliate.next_turn()
        future_sight_data = self.future_sight.item
        if self.future_sight.next_turn() and self.current_pokemon is not None:
            msg += f"{self.current_pokemon.name} took the future sight attack!\n"
            # pyrefly: ignore [not-iterable]
            future_sight_attacker, future_sight_move = future_sight_data
            msgadd, _ = future_sight_move.attack(future_sight_attacker, self.current_pokemon, battle)
            msg += msgadd
        return msg

    def switch_poke(self, slot: int, *, mid_turn=False):
        """Switch the currently active poke to the given slot."""
        if slot < 0 or slot >= len(self.party):
            raise ValueError("out of bounds")
        if not self.party[slot].hp > 0:
            raise ValueError("no hp")
        self.current_pokemon = self.party[slot]
        self.mid_turn_remove = False
        self.last_idx = slot
        if mid_turn:
            self.current_pokemon.swapped_in = True

    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        raise NotImplementedError()

    def valid_swaps(self, defender, battle, *, check_trap=True):
        """Returns a list of indexes of pokes in the party that can be swapped to."""
        if self.current_pokemon is not None:
            if ElementType.GHOST in self.current_pokemon.type_ids:
                check_trap = False
            if self.current_pokemon.held_item == "shed-shell":
                check_trap = False

            if check_trap:
                if self.current_pokemon.trapping:
                    return []
                if self.current_pokemon.ingrain:
                    return []
                if self.current_pokemon.fairy_lock.active() or (
                    defender is not None and defender.fairy_lock.active()
                ):
                    return []
                if self.current_pokemon.no_retreat:
                    return []
                if self.current_pokemon.bind.active() and not self.current_pokemon.substitute:
                    return []
                if defender is not None:
                    if defender.ability() == Ability.SHADOW_TAG and not self.current_pokemon.ability() == Ability.SHADOW_TAG:
                        return []
                    if defender.ability() == Ability.MAGNET_PULL and ElementType.STEEL in self.current_pokemon.type_ids:
                        return []
                    if defender.ability() == Ability.ARENA_TRAP and self.current_pokemon.grounded(battle):
                        return []
        result = [idx for idx, poke in enumerate(self.party) if poke.hp > 0]
        if self.last_idx in result:
            result.remove(self.last_idx)
        return result

    def valid_moves(self, defender):
        """
        https://www.smogon.com/dp/articles/move_restrictions

        Returns
        - ("forced", Move) - The move-action this trainer is FORCED to use.
        - ("idxs", List[int]) - The indexes of moves that are valid to CHOOSE to use.
        - ("struggle", List[int]) - If the user attempts to use any move, use struggle instead (no valid moves).
        """
        # Check if they are FORCED to use a certain move
        # pyrefly: ignore [missing-attribute]
        if self.current_pokemon.locked_move:
            # pyrefly: ignore [missing-attribute]
            return ("forced", self.current_pokemon.locked_move.move)
        result = []
        # pyrefly: ignore [missing-attribute]
        for idx, move in enumerate(self.current_pokemon.moves):
            if move.pp <= 0:
                continue
            # pyrefly: ignore [missing-attribute]
            if move.damage_class == DamageClass.STATUS and self.current_pokemon.held_item == "assault-vest":
                continue
            # pyrefly: ignore [missing-attribute]
            if move.damage_class == DamageClass.STATUS and self.current_pokemon.taunt.active():
                continue
            # pyrefly: ignore [missing-attribute]
            if move.effect == 247 and not all(m.used for m in self.current_pokemon.moves if m.effect != 247):
                continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.disable.active() and move is self.current_pokemon.disable.item:
                continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.held_item in ("choice-scarf", "choice-band", "choice-specs") or self.current_pokemon.ability() == Ability.GORILLA_TACTICS:
                # pyrefly: ignore [missing-attribute]
                if self.current_pokemon.choice_move is not None and move is not self.current_pokemon.choice_move:
                    continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.torment and self.current_pokemon.last_move is move:
                continue
            if (
                # pyrefly: ignore [missing-attribute]
                self.current_pokemon.last_move is not None
                # pyrefly: ignore [missing-attribute]
                and self.current_pokemon.last_move.effect == 492
                # pyrefly: ignore [missing-attribute]
                and self.current_pokemon.last_move.id == move.id
                # pyrefly: ignore [missing-attribute]
                and not self.current_pokemon.last_move_failed
            ):
                continue
            if defender is not None and defender.imprison and move.id in [x.id for x in defender.moves]:
                continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.heal_block.active() and move.is_affected_by_heal_block():
                continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.silenced.active() and move.is_sound_based():
                continue
            # pyrefly: ignore [missing-attribute]
            if move.effect == 339 and not self.current_pokemon.ate_berry:
                continue
            # pyrefly: ignore [missing-attribute]
            if move.effect == 453 and not self.current_pokemon.held_item.is_berry():
                continue
            # pyrefly: ignore [missing-attribute]
            if self.current_pokemon.encore.active() and move is not self.current_pokemon.encore.item:
                continue
            result.append(idx)
        if not result:
            return ("struggle", [0, 1, 2, 3])
        return ("idxs", result)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, party={self.party!r})"
