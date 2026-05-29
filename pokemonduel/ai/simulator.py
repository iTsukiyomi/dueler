from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Optional

from ..misc import ExpiringEffect, Weather, Terrain


_TYPE_EFF_CACHE: Optional[dict] = None
_METRONOME_CACHE: Optional[list] = None


def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def _load_type_effectiveness() -> dict:
    global _TYPE_EFF_CACHE
    if _TYPE_EFF_CACHE is not None:
        return _TYPE_EFF_CACHE
    with open(_data_dir() / "type_effectiveness.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    _TYPE_EFF_CACHE = {
        (te["damage_type_id"], te["target_type_id"]): te["damage_factor"]
        for te in data
    }
    return _TYPE_EFF_CACHE


def _load_metronome_moves() -> list:
    global _METRONOME_CACHE
    if _METRONOME_CACHE is not None:
        return _METRONOME_CACHE
    immune_ids = {
        68, 102, 119, 144, 165, 166, 168, 173, 182, 194, 197, 203, 214, 243, 264, 266,
        267, 270, 271, 274, 289, 343, 364, 382, 383, 415, 448, 469, 476, 495, 501, 511,
        516, 546, 547, 548, 553, 554, 555, 557, 561, 562, 578, 588, 591, 592, 593, 596,
        606, 607, 614, 615, 617, 621, 661, 671, 689, 690, 704, 705, 712, 720, 721, 722,
    }
    uncoded_ids = {
        266, 270, 476, 495, 502, 511, 597, 602, 603, 607, 622, 623, 624, 625, 626, 627,
        628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643,
        644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 671,
        695, 696, 697, 698, 699, 700, 701, 702, 703, 719, 723, 724, 725, 726, 727, 728,
        811, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010, 10011,
        10012, 10013, 10014, 10015, 10016, 10017, 10018,
    }
    ignored = immune_ids | uncoded_ids
    with open(_data_dir() / "moves.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    _METRONOME_CACHE = [m for m in data if m["id"] not in ignored]
    return _METRONOME_CACHE


class _NullChannel:
    async def send(self, *a, **kw):
        return None


class _NullCtx:
    """A ctx-shaped object the data_gen finders happily ignore (they use a
    Path-relative file lookup, not the ctx)."""
    def __init__(self) -> None:
        self.channel = _NullChannel()
        self.author  = None
        self.message = None


class HeadlessBattle:
    """A non-async, no-Discord ``Battle`` clone.

    The class exposes the same public attributes consumed by the rest of
    the engine (``trainer1/2``, ``weather``, ``terrain``, ``trick_room``,
    ``magic_room``, ``wonder_room``, ``gravity``, ``turn``, ``msg``,
    ``inverse_battle``, ``type_effectiveness``, ``metronome_moves_raw``,
    ``last_move_effect``, ``plasma_fists``).
    """

    __slots__ = (
        "ctx", "channel", "trainer1", "trainer2",
        "bg_num", "trick_room", "magic_room", "wonder_room",
        "gravity", "weather", "terrain", "plasma_fists",
        "turn", "last_move_effect", "metronome_moves_raw",
        "type_effectiveness", "inverse_battle", "msg",
    )

    def __init__(self, trainer1, trainer2, *, inverse_battle: bool = False) -> None:
        self.ctx     = _NullCtx()
        self.channel = self.ctx.channel
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        for poke in trainer1.party:
            poke.held_item.battle = self
        for poke in trainer2.party:
            poke.held_item.battle = self
        self.bg_num = 1
        self.trick_room  = ExpiringEffect(0)
        self.magic_room  = ExpiringEffect(0)
        self.wonder_room = ExpiringEffect(0)
        self.gravity     = ExpiringEffect(0)
        self.weather     = Weather(self)
        self.terrain     = Terrain(self)
        self.plasma_fists = False
        self.turn = 0
        self.last_move_effect = None
        self.metronome_moves_raw = _load_metronome_moves()
        self.type_effectiveness  = _load_type_effectiveness()
        self.inverse_battle = inverse_battle
        self.msg = ""

    def __deepcopy__(self, memo):
        """Skip cloning the read-only globals to keep deepcopy snappy."""
        cls = type(self)
        new = cls.__new__(cls)
        memo[id(self)] = new
        new.ctx     = self.ctx
        new.channel = self.channel
        new.trainer1 = copy.deepcopy(self.trainer1, memo)
        new.trainer2 = copy.deepcopy(self.trainer2, memo)
        new.bg_num   = self.bg_num
        new.trick_room  = copy.deepcopy(self.trick_room,  memo)
        new.magic_room  = copy.deepcopy(self.magic_room,  memo)
        new.wonder_room = copy.deepcopy(self.wonder_room, memo)
        new.gravity     = copy.deepcopy(self.gravity,     memo)
        new.weather     = copy.deepcopy(self.weather,     memo)
        new.terrain     = copy.deepcopy(self.terrain,     memo)
        new.weather.battle = new
        new.terrain.battle = new
        new.plasma_fists = self.plasma_fists
        new.turn = self.turn
        new.last_move_effect = self.last_move_effect
        new.metronome_moves_raw = self.metronome_moves_raw
        new.type_effectiveness  = self.type_effectiveness
        new.inverse_battle = self.inverse_battle
        new.msg = ""

        for trainer in (new.trainer1, new.trainer2):
            for poke in trainer.party:
                poke.owner = trainer
                if poke.held_item is not None:
                    poke.held_item.battle = new
                    poke.held_item.owner  = poke
        return new


def _switch_in(trainer, opponent, battle) -> str:
    msg = ""
    if trainer.current_pokemon is not None:
        return msg
    valid = [i for i, p in enumerate(trainer.party) if p.hp > 0 and i != trainer.last_idx]
    if not valid:
        valid = [i for i, p in enumerate(trainer.party) if p.hp > 0]
    if not valid:
        return msg
    trainer.switch_poke(valid[0])
    # pyrefly: ignore [missing-attribute]
    msg += trainer.current_pokemon.send_out(opponent.current_pokemon, battle)
    return msg


def _safe_mid_turn_switch(trainer, opponent, battle) -> str:
    """Resolve ``trainer.selected_action`` (an int slot) as a mid-turn swap.

    If the requested slot is out of range or already fainted (which can
    happen when the AI's action mask points at a stale slot because of a
    forced-switch race), fall back to swapping in the first alive party
    member via ``_switch_in``. Returns the formatted battle log.
    """
    msg = ""
    slot = trainer.selected_action
    target = None
    if isinstance(slot, int) and 0 <= slot < len(trainer.party):
        target = trainer.party[slot]
    if target is None or getattr(target, "hp", 0) <= 0:
        # Bad slot — pick *any* alive party member instead.
        alt = next((i for i, p in enumerate(trainer.party) if p.hp > 0
                    and i != trainer.last_idx), None)
        if alt is None:
            alt = next((i for i, p in enumerate(trainer.party) if p.hp > 0), None)
        if alt is None:
            return msg
        slot = alt
    msg += trainer.current_pokemon.remove(battle)
    trainer.switch_poke(slot, mid_turn=True)
    if opponent.current_pokemon is not None:
        msg += trainer.current_pokemon.send_out(opponent.current_pokemon, battle)
    return msg


def _handle_megas(battle, t1, t2) -> str:
    """Mirrors ``Battle.handle_megas`` so we evolve at the right moment."""
    msg = ""
    for at, dt in ((t1, t2), (t2, t1)):
        if at.current_pokemon is None or not at.current_pokemon.should_mega_evolve:
            continue
        p = at.current_pokemon
        try:
            if ((getattr(p.held_item, "name", "") == "mega-stone"
                 or p._name == "Rayquaza")
                and p.form(p._name + "-mega")):
                msg += f"{p.name} evolved!\n"
            elif getattr(p.held_item, "name", "") == "mega-stone-x" and p.form(p._name + "-mega-x"):
                msg += f"{p.name} evolved!\n"
            elif getattr(p.held_item, "name", "") == "mega-stone-y" and p.form(p._name + "-mega-y"):
                msg += f"{p.name} evolved!\n"
            else:
                p.should_mega_evolve = False
                continue
            p.ability_id        = p.mega_ability_id
            p.starting_ability_id = p.mega_ability_id
            p.type_ids          = p.mega_type_ids.copy()
            p.starting_type_ids = p.mega_type_ids.copy()
            msg += p.send_out_ability(dt.current_pokemon, battle)
            at.has_mega_evolved = True
        except Exception:
            p.should_mega_evolve = False
    return msg


def _who_first(battle, check_move: bool = True):
    """Pure copy of Battle.who_first — no Discord deps."""
    import random
    from ..enums import Ability, DamageClass

    T1FIRST = (battle.trainer1, battle.trainer2)
    T2FIRST = (battle.trainer2, battle.trainer1)
    if battle.trainer1.current_pokemon is None or battle.trainer2.current_pokemon is None:
        return T1FIRST
    s1 = battle.trainer1.current_pokemon.get_speed(battle)
    s2 = battle.trainer2.current_pokemon.get_speed(battle)
    if check_move:
        a1 = battle.trainer1.selected_action
        a2 = battle.trainer2.selected_action
        if isinstance(a1, int) and isinstance(a2, int):
            if battle.trainer1.current_pokemon.get_raw_speed() > battle.trainer2.current_pokemon.get_raw_speed():
                return T1FIRST
            return T2FIRST
        if isinstance(a1, int):
            return T1FIRST
        if isinstance(a2, int):
            return T2FIRST
        p1 = a1.get_priority(battle.trainer1.current_pokemon, battle.trainer2.current_pokemon, battle)
        p2 = a2.get_priority(battle.trainer2.current_pokemon, battle.trainer1.current_pokemon, battle)
        if p1 > p2: return T1FIRST
        if p2 > p1: return T2FIRST
        q1 = q2 = False
        if (battle.trainer1.current_pokemon.ability() == Ability.QUICK_DRAW
                and a1.damage_class != DamageClass.STATUS
                and random.randint(1, 100) <= 30):
            q1 = True
        if (battle.trainer2.current_pokemon.ability() == Ability.QUICK_DRAW
                and a2.damage_class != DamageClass.STATUS
                and random.randint(1, 100) <= 30):
            q2 = True
        if battle.trainer1.current_pokemon.held_item == "quick-claw" and random.randint(1, 100) <= 20:
            q1 = True
        if battle.trainer2.current_pokemon.held_item == "quick-claw" and random.randint(1, 100) <= 20:
            q2 = True
        if q1 and not q2:
            return T1FIRST
        if q2 and not q1:
            return T2FIRST
        sl1 = sl2 = False
        if battle.trainer1.current_pokemon.ability() == Ability.STALL:
            sl1 = True
        if (battle.trainer1.current_pokemon.ability() == Ability.MYCELIUM_MIGHT
                and a1.damage_class == DamageClass.STATUS):
            sl1 = True
        if battle.trainer2.current_pokemon.ability() == Ability.STALL:
            sl2 = True
        if (battle.trainer2.current_pokemon.ability() == Ability.MYCELIUM_MIGHT
                and a2.damage_class == DamageClass.STATUS):
            sl2 = True
        if sl1 and sl2:
            if s1 == s2:
                return random.choice([T1FIRST, T2FIRST])
            return T2FIRST if s1 > s2 else T1FIRST
        if sl1:
            return T2FIRST
        if sl2:
            return T1FIRST
    if s1 == s2:
        return random.choice([T1FIRST, T2FIRST])
    if battle.trick_room.active():
        return T2FIRST if s1 > s2 else T1FIRST
    return T1FIRST if s1 > s2 else T2FIRST


def run_turn(battle) -> tuple[str, Optional[object]]:
    """Run exactly one full turn given that *both* trainers have already
    populated ``selected_action``. Returns ``(message, winner_or_None)``."""
    msg = ""

    swapped = False
    if battle.trainer1.current_pokemon is None:
        msg += _switch_in(battle.trainer1, battle.trainer2, battle)
        swapped = True
    if battle.trainer2.current_pokemon is None:
        msg += _switch_in(battle.trainer2, battle.trainer1, battle)
        swapped = True
    if swapped:
        battle.msg += msg
        return msg, _maybe_winner(battle)

    t1, t2 = _who_first(battle)
    if t1.current_pokemon is not None and t2.current_pokemon is not None:
        if not isinstance(t1.selected_action, int):
            msg += t1.selected_action.setup(t1.current_pokemon, t2.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w
    if t1.current_pokemon is not None and t2.current_pokemon is not None:
        if not isinstance(t2.selected_action, int):
            msg += t2.selected_action.setup(t2.current_pokemon, t1.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w

    ran_megas = False
    if not isinstance(t1.selected_action, int):
        msg += _handle_megas(battle, t1, t2)
        ran_megas = True
    if t1.current_pokemon is not None and t2.current_pokemon is not None:
        if isinstance(t1.selected_action, int):
            msg += _safe_mid_turn_switch(t1, t2, battle)
            if t1.current_pokemon is not None:
                t1.current_pokemon.has_moved = True
        else:
            msg += t1.selected_action.use(t1.current_pokemon, t2.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w
    if t1.mid_turn_remove:
        msg += _switch_in(t1, t2, battle)
    if t1.current_pokemon is None and t2.current_pokemon is not None and (
            isinstance(t2.selected_action, int) or not t2.selected_action.targets_opponent()):
        msg += _switch_in(t1, t2, battle)

    if not ran_megas and not isinstance(t2.selected_action, int):
        msg += _handle_megas(battle, t1, t2)
        ran_megas = True
    if t1.current_pokemon is not None and t2.current_pokemon is not None:
        if isinstance(t2.selected_action, int):
            msg += _safe_mid_turn_switch(t2, t1, battle)
            if t2.current_pokemon is not None:
                t2.current_pokemon.has_moved = True
        else:
            msg += t2.selected_action.use(t2.current_pokemon, t1.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w
    if t2.mid_turn_remove:
        msg += _switch_in(t2, t1, battle)

    if not ran_megas:
        msg += _handle_megas(battle, t1, t2)

    battle.turn += 1
    battle.plasma_fists = False
    if battle.weather.next_turn():
        msg += "The weather cleared!\n"
    if battle.terrain.next_turn():
        msg += "The terrain cleared!\n"
    battle.last_move_effect = None
    t1, t2 = _who_first(battle, check_move=False)
    msg += t1.next_turn(battle)
    if t1.current_pokemon is not None:
        msg += t1.current_pokemon.next_turn(t2.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w
    msg += t2.next_turn(battle)
    if t2.current_pokemon is not None:
        msg += t2.current_pokemon.next_turn(t1.current_pokemon, battle)
    if (w := _maybe_winner(battle)) is not None:
        battle.msg += msg
        return msg, w
    if battle.trick_room.next_turn():
        msg += "The Dimensions returned back to normal!\n"
    if battle.gravity.next_turn():
        msg += "Gravity returns to normal!\n"
    if battle.magic_room.next_turn():
        msg += "The room returns to normal, and held items regain their effect!\n"
    if battle.wonder_room.next_turn():
        msg += "The room returns to normal, and stats swap back to what they were before!\n"

    battle.msg += msg
    return msg, _maybe_winner(battle)


def _maybe_winner(battle):
    t1_alive = battle.trainer1.has_alive_pokemon()
    t2_alive = battle.trainer2.has_alive_pokemon()
    if not t1_alive and not t2_alive:
        return battle.trainer1
    if not t1_alive:
        return battle.trainer2
    if not t2_alive:
        return battle.trainer1
    return None


def initial_send_out(battle) -> str:
    """Initial send-out, mirroring ``Battle.run`` opening behaviour."""
    msg = ""
    t1 = battle.trainer1.current_pokemon
    t2 = battle.trainer2.current_pokemon
    if t1 is None or t2 is None:
        return msg
    if t1.get_raw_speed() > t2.get_raw_speed():
        msg += t1.send_out(t2, battle)
        msg += t2.send_out(t1, battle)
    else:
        msg += t2.send_out(t1, battle)
        msg += t1.send_out(t2, battle)
    battle.msg += msg
    return msg


__all__ = [
    "HeadlessBattle",
    "run_turn",
    "initial_send_out",
]
