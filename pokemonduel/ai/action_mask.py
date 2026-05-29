from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from . import config as C
from . import features as F


def legal_action_mask(battle, trainer, opponent) -> np.ndarray:
    """Return a boolean mask of shape ``(C.N_ACTIONS,)`` over legal actions.

    The mask is *truthy* even in degenerate situations (e.g. when the
    Pokémon must struggle); the AI will simply pick "any move" and the
    underlying engine resolves it.
    """
    mask = np.zeros(C.N_ACTIONS, dtype=bool)

    if trainer is None or trainer.current_pokemon is None:
        # Forced switch from a fainted active — only switch actions are legal.
        if trainer is not None:
            valid_sw = trainer.valid_swaps(opponent.current_pokemon if opponent else None,
                                           battle, check_trap=False)
            for pi in valid_sw:
                if 0 <= pi < C.N_SWITCH_ACTIONS:
                    poke = trainer.party[pi] if pi < len(trainer.party) else None
                    if poke is not None and getattr(poke, "hp", 0) > 0:
                        mask[C.SWITCH_OFFSET + pi] = True
            if not mask.any():
                for pi, poke in enumerate(trainer.party):
                    if pi < C.N_SWITCH_ACTIONS and getattr(poke, "hp", 0) > 0:
                        mask[C.SWITCH_OFFSET + pi] = True
        if not mask.any():
            # Truly nothing alive — pick slot 0 so callers downstream don't crash trying to index an empty mask. The caller is expected to also check ``has_alive_pokemon`` before applying the action.
            mask[C.SWITCH_OFFSET] = True
        return mask

    status, data = trainer.valid_moves(opponent.current_pokemon if opponent else None)
    if status == "forced":
        mask[C.MOVE_OFFSET] = True
    elif status == "struggle":
        for i in range(C.N_MOVE_ACTIONS):
            mask[C.MOVE_OFFSET + i] = True
    else:
        for idx in data:
            if 0 <= idx < C.N_MOVE_ACTIONS:
                mask[C.MOVE_OFFSET + idx] = True

    valid_sw = trainer.valid_swaps(opponent.current_pokemon if opponent else None,
                                   battle, check_trap=True)
    for pi in valid_sw:
        if 0 <= pi < C.N_SWITCH_ACTIONS:
            poke = trainer.party[pi] if pi < len(trainer.party) else None
            if poke is not None and getattr(poke, "hp", 0) > 0:
                mask[C.SWITCH_OFFSET + pi] = True

    active = trainer.current_pokemon
    can_mega = bool(active
                    and getattr(active, "held_item", None)
                    and getattr(active.held_item, "name", None) in (
                        "mega-stone", "mega-stone-x", "mega-stone-y")
                    and not getattr(trainer, "has_mega_evolved", False))
    if (not can_mega
            and active and getattr(active, "_name", "") == "Rayquaza"
            and any(getattr(m, "name", "") == "dragon-ascent" for m in active.moves)
            and not getattr(trainer, "has_mega_evolved", False)):
        can_mega = True

    if can_mega:
        for i in range(C.N_MOVE_ACTIONS):
            if mask[C.MOVE_OFFSET + i]:
                mask[C.MEGA_OFFSET + i] = True

    if not mask.any():  # Safety net.
        mask[C.MOVE_OFFSET] = True
    return mask


def action_to_engine(action: int, trainer, opponent, battle
                     ) -> Tuple[object, Optional[int], bool]:
    """Translate an action index to the engine-level decision.

    Returns ``(selected_action, switch_index, mega)`` where:

    * ``selected_action`` is what should be written to
      ``trainer.selected_action`` if no switch is required — either a
      ``Move`` object or an ``int`` representing a party slot.
    * ``switch_index`` is set when the AI elected to switch (party slot
      to swap to), otherwise ``None``.
    * ``mega`` indicates whether the agent wants this Pokémon to mega-
      evolve before its move resolves.
    """
    from ..moves import Move

    mega = False
    if C.MEGA_OFFSET <= action < C.MEGA_OFFSET + C.N_MEGA_ACTIONS:
        mega = True
        local = action - C.MEGA_OFFSET
        return _move_action_to_engine(local, trainer, opponent), None, mega

    if C.SWITCH_OFFSET <= action < C.SWITCH_OFFSET + C.N_SWITCH_ACTIONS:
        slot = action - C.SWITCH_OFFSET
        return slot, slot, False

    return _move_action_to_engine(action - C.MOVE_OFFSET, trainer, opponent), None, False


def _move_action_to_engine(slot: int, trainer, opponent):
    from ..moves import Move
    if trainer is None or trainer.current_pokemon is None:
        return Move.struggle()
    status, data = trainer.valid_moves(opponent.current_pokemon if opponent else None)
    if status == "forced":
        return data
    if status == "struggle":
        return Move.struggle()
    if slot in data:
        return trainer.current_pokemon.moves[slot]
    if data:
        return trainer.current_pokemon.moves[data[0]]
    return Move.struggle()


def apply_action(action: int, trainer, opponent, battle) -> None:
    """Apply an action to a trainer by mutating ``selected_action`` and the
    Pokémon's ``should_mega_evolve`` flag. The Battle main loop will then
    pick this up when both trainers' events are set."""
    selected, switch_idx, mega = action_to_engine(action, trainer, opponent, battle)
    if mega and trainer.current_pokemon is not None:
        trainer.current_pokemon.should_mega_evolve = True
    trainer.selected_action = selected
    if switch_idx is not None:
        trainer.selected_action = switch_idx


__all__ = [
    "legal_action_mask",
    "action_to_engine",
    "apply_action",
]
