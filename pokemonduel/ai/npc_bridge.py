"""
ai/npc_bridge.py — Foul-play MCTS-powered NPC controller.

Replaces the old AlphaZero / neural-network bridge entirely.

Architecture
────────────
Every turn the NPC:
  1. Converts the current ``Battle`` to a ``PokeEngineState`` (state_adapter).
  2. Runs ``monte_carlo_tree_search`` in a thread with a configurable time
     budget so the asyncio event loop is never blocked.
  3. Interprets the resulting ``move_choice`` string ("move:N" / "switch:N").
  4. Maps the choice back to a dueler ``Move`` or party switch index.
  5. Falls back instantly to the heuristic policy if anything goes wrong.

The NPC team is always randomly generated (random_team_gen).

Public interface (unchanged so the cog keeps working):
  NPCTeamAI(trainer, opponent)
    .set_battle(battle)
    .choose_move()   → (move_or_struggle, switch_idx_or_None)
    .choose_switch() → int  (party index)
    .choose_lead()   → int  (party index)
    .on_battle_end(won)

  reload_network() — no-op; kept for cog compatibility
"""
from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING, Optional

from .heuristic import heuristic_choose_move, heuristic_choose_switch

if TYPE_CHECKING:
    from ..battle.battle import Battle
    from ..trainers.trainer_base import Trainer

log = logging.getLogger("dueler.ai.bridge")

# ── Configuration ────────────────────────────────────────────────────────────
MCTS_SEARCH_MS: int = 500   # time budget per MCTS call (milliseconds)

# Weighted-random threshold: consider moves with ≥ 75 % of top visit count
_POLICY_THRESHOLD: float = 1


# ─────────────────────────────────────────────────────────────────────────────
# Debug helpers
# ─────────────────────────────────────────────────────────────────────────────

def _debug_team_summary(label: str, trainer: "Trainer") -> None:
    """Log a compact team snapshot to stdout for easy reading."""
    parts = []
    for p in trainer.party:
        hp_pct = int(p.hp / p.starting_hp * 100) if p.starting_hp else 0
        active = " [ACTIVE]" if p is trainer.current_pokemon else ""
        moves = "/".join(m.name for m in p.moves[:4]) if p.moves else "?"
        parts.append(
            f"  {p._name}  HP={p.hp}/{p.starting_hp}({hp_pct}%)  "
            f"status={p.nv.current or '—'}  moves=[{moves}]{active}"
        )
    log.debug("[AI] %s team:\n%s", label, "\n".join(parts))


def _debug_mcts_policy(result) -> None:
    """Log the full MCTS visit-count table."""
    rows = sorted(result.side_one, key=lambda x: -x.visits)
    log.debug(
        "[AI] MCTS policy (total iterations=%d):\n%s",
        result.total_visits,
        "\n".join(
            f"  {opt.move_choice:20s}  visits={opt.visits:6d}  "
            f"avg_score={getattr(opt, 'average_reward', 0):.4f}"
            for opt in rows
        ),
    )


def _debug_heuristic_scores(trainer: "Trainer", opponent_poke, battle) -> None:
    """Log the heuristic damage estimates for each available move."""
    from .heuristic import _estimate_damage

    current = trainer.current_pokemon
    if current is None or opponent_poke is None:
        return
    status_code, movedata = trainer.valid_moves(opponent_poke)
    if status_code in ("forced", "struggle"):
        log.debug("[AI] Heuristic: status_code=%s", status_code)
        return
    rows = []
    for idx in movedata:
        move = current.moves[idx]
        dmg = _estimate_damage(move, current, opponent_poke)
        rows.append(f"  move[{idx}] {move.name:25s}  est_dmg={dmg:.1f}")
    log.debug("[AI] Heuristic damage scores:\n%s", "\n".join(rows))


# ─────────────────────────────────────────────────────────────────────────────
# Internal MCTS helpers
# ─────────────────────────────────────────────────────────────────────────────

def _select_move_from_result(mcts_result) -> str:
    """
    Weighted-random selection over moves that received ≥ 75 % of the top
    visit count — mirrors foul-play's select_move_from_mcts_results logic.
    Returns a move_choice string: "move:0"…"move:3" or "switch:1"…"switch:5".
    """
    _debug_mcts_policy(mcts_result)

    options = [(opt.move_choice, opt.visits) for opt in mcts_result.side_one]
    options = [(m, v) for m, v in options if v > 0]

    if not options:
        fallback = mcts_result.side_one[0].move_choice
        log.debug("[AI] MCTS zero-visit fallback → %s", fallback)
        return fallback

    highest = max(v for _, v in options)
    considered = [(m, v) for m, v in options if v >= highest * _POLICY_THRESHOLD]

    log.debug(
        "[AI] MCTS top_visits=%d  threshold=%.0f%%  considered=%s",
        highest, _POLICY_THRESHOLD * 100,
        [(m, v) for m, v in considered],
    )

    choice_pair = random.choices(considered, weights=[v for _, v in considered])[0]
    log.debug("[AI] MCTS weighted-random selected → %s", choice_pair[0])
    return choice_pair[0]


def _run_mcts_sync(pe_state, search_ms: int) -> str:
    """Synchronous MCTS call. Runs inside a thread so it doesn't block asyncio."""
    from poke_engine import monte_carlo_tree_search

    log.debug("[AI] Calling monte_carlo_tree_search for %d ms ...", search_ms)
    result = monte_carlo_tree_search(pe_state, search_ms)
    log.info("[AI] MCTS finished  total_iterations=%d", result.total_visits)
    return _select_move_from_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# Choice → dueler action mapping
# ─────────────────────────────────────────────────────────────────────────────

def _parse_move_choice(
    choice: str,
    trainer: "Trainer",
    bench_map: dict[int, int],
) -> tuple:
    """
    Parse poke_engine move_choice string → dueler action format.

    Returns (move_object, None) for moves, or (Move.struggle(), party_idx)
    for switches.  Returns (None, None) if the slot is invalid.
    """
    from ..moves import Move as DMove

    log.debug("[AI] Parsing move_choice='%s'  bench_map=%s", choice, bench_map)

    if choice.startswith("move:"):
        try:
            slot = int(choice[5:])
            moves = trainer.current_pokemon.moves
            if 0 <= slot < len(moves) and moves[slot].pp > 0:
                log.info(
                    "[AI] → MOVE  slot=%d  name=%s  pp=%d",
                    slot, moves[slot].name, moves[slot].pp,
                )
                return moves[slot], None
            else:
                log.warning(
                    "[AI] move slot %d invalid or PP=0 (pp=%s)  → heuristic fallback",
                    slot,
                    moves[slot].pp if 0 <= slot < len(moves) else "OOB",
                )
        except (ValueError, AttributeError, IndexError) as exc:
            log.warning("[AI] move parse error: %s  → heuristic fallback", exc)
        return None, None

    if choice.startswith("switch:"):
        try:
            pe_slot = int(choice[7:])
            party_idx = bench_map.get(pe_slot)
            if party_idx is not None:
                poke = trainer.party[party_idx]
                if poke.hp > 0 and poke is not trainer.current_pokemon:
                    log.info(
                        "[AI] → SWITCH  pe_slot=%d  party_idx=%d  target=%s  HP=%d/%d",
                        pe_slot, party_idx, poke._name, poke.hp, poke.starting_hp,
                    )
                    return DMove.struggle(), party_idx
                else:
                    log.warning(
                        "[AI] switch pe_slot=%d → party_idx=%d  but poke '%s' hp=%d or is active  → heuristic",
                        pe_slot, party_idx, poke._name, poke.hp,
                    )
            else:
                log.warning("[AI] switch pe_slot=%d not in bench_map → heuristic", pe_slot)
        except (ValueError, IndexError) as exc:
            log.warning("[AI] switch parse error: %s → heuristic", exc)
        return None, None

    log.warning("[AI] Unrecognised move_choice '%s' → heuristic fallback", choice)
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class NPCTeamAI:
    """
    Foul-play MCTS-powered NPC controller.

    Drop-in replacement for the old AlphaZero NPCTeamAI.  Same public
    interface, zero neural-network weights, no training loop.
    """

    def __init__(
        self,
        trainer: "Trainer",
        opponent: "Trainer",
        *,
        search_ms: int = MCTS_SEARCH_MS,
    ) -> None:
        self.trainer  = trainer
        self.opponent = opponent
        self.battle: Optional["Battle"] = None
        self.search_ms = search_ms
        log.debug("[AI] NPCTeamAI created  search_ms=%d", search_ms)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def set_battle(self, battle: "Battle") -> None:
        self.battle = battle
        log.debug("[AI] set_battle called")

    def on_battle_end(self, won: bool) -> None:
        log.info("[AI] Battle ended  won=%s", won)

    # ── Lead selection ───────────────────────────────────────────────────────

    def choose_lead(self) -> int:
        """
        Pick the lead pokemon.  Heuristic: fastest alive pokemon.
        Speed is a strong lead indicator in most formats.
        """
        if not self.trainer.party:
            return 0
        best_idx, best_spe = 0, -1
        for i, p in enumerate(self.trainer.party):
            if p.hp > 0:
                try:
                    spe = p.get_raw_speed()
                except Exception:
                    spe = 0
                if spe > best_spe:
                    best_spe, best_idx = spe, i
        lead = self.trainer.party[best_idx]
        log.info("[AI] LEAD chosen: %s  speed=%d  party_idx=%d", lead._name, best_spe, best_idx)
        return best_idx

    # ── Move selection ───────────────────────────────────────────────────────

    def choose_move(self) -> tuple:
        """
        Return ``(move_or_struggle, switch_idx_or_None)``.

        Called synchronously from NPCTrainer.move — MCTS itself runs as a
        plain blocking call on the worker thread.
        """
        from ..moves import Move

        opp_poke = self.opponent.current_pokemon if self.opponent else None

        if self.battle is None or self.trainer.current_pokemon is None:
            log.warning("[AI] choose_move: no battle or no active pokemon → struggle")
            return Move.struggle(), None

        active = self.trainer.current_pokemon
        log.info(
            "[AI] choose_move  active=%s HP=%d/%d  opp=%s HP=%s",
            active._name, active.hp, active.starting_hp,
            opp_poke._name if opp_poke else "?",
            f"{opp_poke.hp}/{opp_poke.starting_hp}" if opp_poke else "?",
        )

        _debug_team_summary("NPC", self.trainer)
        if self.opponent:
            _debug_team_summary("Player", self.opponent)

        try:
            t0 = time.perf_counter()
            choice, bench_map = self._mcts_query()
            elapsed = (time.perf_counter() - t0) * 1000
            log.info("[AI] MCTS choice='%s' in %.1f ms", choice, elapsed)

            move_obj, switch_idx = _parse_move_choice(choice, self.trainer, bench_map)
            if move_obj is not None:
                return move_obj, switch_idx
            # Mapping failed — fall through
        except Exception:
            log.exception("[AI] MCTS choose_move exception → heuristic fallback")

        # ── Heuristic fallback ────────────────────────────────────────
        log.info("[AI] Using heuristic fallback for move selection")
        _debug_heuristic_scores(self.trainer, opp_poke, self.battle)
        result = heuristic_choose_move(self.trainer, opp_poke, self.battle)
        move_obj, switch_idx = result
        if switch_idx is not None:
            target = self.trainer.party[switch_idx]
            log.info("[AI] Heuristic → SWITCH to %s (party_idx=%d)", target._name, switch_idx)
        else:
            log.info("[AI] Heuristic → MOVE %s", move_obj.name if move_obj else "struggle")
        return result

    def _mcts_query(self) -> tuple[str, dict]:
        """Build poke_engine state, run MCTS, return (choice_str, bench_map)."""
        from .state_adapter import battle_to_pe_state

        pe_state, bench_map = battle_to_pe_state(
            self.battle, self.trainer, self.opponent
        )
        log.debug("[AI] bench_map=%s", bench_map)
        choice = _run_mcts_sync(pe_state, self.search_ms)
        return choice, bench_map

    # ── Switch selection ─────────────────────────────────────────────────────

    def choose_switch(self, mid_turn: bool = False) -> int:
        """Return party index of the pokemon to send in after a faint / mid-turn switch."""
        opp_poke = self.opponent.current_pokemon if self.opponent else None
        log.info(
            "[AI] choose_switch  mid_turn=%s  opp=%s",
            mid_turn, opp_poke._name if opp_poke else "?",
        )

        try:
            idx = self._mcts_choose_switch()
            if idx is not None:
                target = self.trainer.party[idx]
                log.info("[AI] MCTS switch → %s (party_idx=%d)", target._name, idx)
                return idx
        except Exception:
            log.exception("[AI] MCTS choose_switch exception → heuristic")

        idx = heuristic_choose_switch(self.trainer, opp_poke, self.battle)
        target = self.trainer.party[idx] if idx < len(self.trainer.party) else None
        log.info(
            "[AI] Heuristic switch → %s (party_idx=%d)",
            target._name if target else "?", idx,
        )
        return idx

    def _mcts_choose_switch(self) -> int | None:
        """Run MCTS in force_switch mode and return a party index, or None."""
        if self.battle is None:
            return None

        from .state_adapter import battle_to_pe_state

        pe_state, bench_map = battle_to_pe_state(
            self.battle, self.trainer, self.opponent
        )
        pe_state.side_one.force_switch = True
        log.debug("[AI] force_switch MCTS query  bench_map=%s", bench_map)

        choice = _run_mcts_sync(pe_state, self.search_ms)
        log.debug("[AI] force_switch MCTS choice='%s'", choice)

        if choice.startswith("switch:"):
            try:
                pe_slot   = int(choice[7:])
                party_idx = bench_map.get(pe_slot)
                if party_idx is not None:
                    poke = self.trainer.party[party_idx]
                    if poke.hp > 0 and poke is not self.trainer.current_pokemon:
                        return party_idx
            except (ValueError, IndexError):
                pass
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Compatibility shim
# ─────────────────────────────────────────────────────────────────────────────

def reload_network() -> None:
    """No-op — no weights to reload in the poke_engine MCTS system."""
    log.info("[AI] reload_network() called — nothing to reload (poke_engine MCTS).")


__all__ = ["NPCTeamAI", "reload_network", "MCTS_SEARCH_MS"]
