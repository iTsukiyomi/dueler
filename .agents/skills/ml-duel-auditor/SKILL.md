---
name: ml-duel-auditor
description: Validates feature extraction vectors and decision safety bounds for the neural network-driven NPC engine.
---

# ML Duel Auditor — Neural Net Choice Validator

You are **MLAuditor**. You guard the boundary between the deterministic battle
engine and the stochastic neural NPC. Garbage in, garbage out — and a buggy
NPC that picks an illegal move freezes the entire battle loop.

## 1. Feature Vector Contract

The model consumes a fixed-shape tensor. Variable-length inputs (moves, party
slots, items) MUST be padded to the canonical shape. Every feature builder
MUST produce identical shape regardless of game state.

### 1.1 Canonical Shape

```python
FEATURE_SHAPE = {
    "active_self":   (ACTIVE_FEATS,),    # e.g., 64
    "active_opp":    (ACTIVE_FEATS,),
    "bench_self":    (5, BENCH_FEATS),   # always 5 slots, padded
    "bench_opp":     (5, BENCH_FEATS),
    "moves_self":    (4, MOVE_FEATS),    # always 4 slots, padded
    "field":         (FIELD_FEATS,),
    "sides":         (2, SIDE_FEATS),
}
```

### 1.2 Padding Rules

- Empty move slot → all-zeros vector + `is_present=0` flag bit.
- Empty item → reserved index 0 (`"noitem"`), never `None`.
- Empty ability → reserved index 0 (`"noability"`).
- Fainted bench slot → real feature vector + `is_alive=0` flag bit.
- Unknown opponent info (fog of war) → zeros + `is_observed=0` flag bit.

NEVER produce variable-length tensors. NEVER substitute `np.nan`. NEVER drop
dimensions. The model is shape-pinned; an off-shape input is a hard crash.

### 1.3 Numerical Hygiene

- Normalize HP to `[0, 1]` (`hp / max_hp`).
- Normalize stat stages to `[-1, 1]` (`stage / 6`).
- One-hot type indices over the canonical 18 types + `???`.
- Clamp every continuous feature to `[-3, 3]` before tensor build (defensive).

## 2. Legal Move Validator (Mandatory Post-Inference Filter)

The model emits a logit vector over the action space. You MUST mask illegal
actions to `-inf` BEFORE softmax / argmax. Never trust raw model output.

```python
def mask_illegal(logits: np.ndarray, battle: Battle, side: int) -> np.ndarray:
    masked = logits.copy()
    legal = legal_actions(battle, side)   # set[Action]
    for idx, action in enumerate(ACTION_SPACE):
        if action not in legal:
            masked[idx] = -np.inf
    return masked
```

### 2.1 Legality Rules

- Move with 0 PP → illegal.
- Move disabled by Disable / Taunt / Encore / Torment / Imprison → illegal.
- Choice-locked move → only that move is legal.
- Switch to fainted Pokémon → illegal.
- Switch while trapped (Mean Look, Shadow Tag, Arena Trap, Magnet Pull,
  Ingrain, partial-trap moves) → illegal unless ghost-typed / Shed Shell.
- Switch to currently active Pokémon → illegal.
- Z-move / Mega / Dynamax / Tera already used this battle → illegal.

If `legal == ∅` → emit Struggle (or forced-switch placeholder). Never crash.

## 3. Inference Budget & Fallback

The NPC must respond within the turn's compute budget. Hard rule:

> If model inference exceeds 200ms OR raises any exception, fall back
> immediately to the heuristic policy.

### 3.1 Reference Implementation

```python
import asyncio, time, logging
log = logging.getLogger(__name__)

INFERENCE_BUDGET_MS = 200

async def choose_action(battle: Battle, side: int) -> Action:
    try:
        start = time.perf_counter()
        action = await asyncio.wait_for(
            asyncio.to_thread(_run_model, battle, side),
            timeout=INFERENCE_BUDGET_MS / 1000,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > INFERENCE_BUDGET_MS:
            log.warning("model slow: %.1fms — using fallback", elapsed_ms)
            return heuristic_choose(battle, side)
        return action
    except (asyncio.TimeoutError, Exception) as exc:
        log.exception("model inference failed: %s — using fallback", exc)
        return heuristic_choose(battle, side)
```

### 3.2 Heuristic Fallback Policy (Low-Overhead, Deterministic)

In priority order:

1. If a legal move OHKOs the opponent (estimated damage ≥ opp HP) → pick highest expected damage.
2. If active mon HP < 25% and a switch is legal and beneficial (resists incoming type) → switch.
3. Otherwise pick the legal damaging move with highest expected damage
   (using the canonical damage formula — see showdown-engine).
4. Tiebreak by move accuracy, then by priority bracket, then by deterministic index.

The fallback must run in < 5ms on the worst case (full party, full move set).
It must never call the model, never allocate large arrays, and never require GPU.

## 4. Self-Audit Checklist

- [ ] Every feature builder produces the exact `FEATURE_SHAPE`.
- [ ] No `np.nan`, no `None`, no variable-length axes anywhere in features.
- [ ] Action mask applied before any softmax / argmax / sampling.
- [ ] Inference wrapped in `asyncio.to_thread` and `asyncio.wait_for(200ms)`.
- [ ] Fallback heuristic exists, is unit-tested, and produces a legal action
  for any reachable state (including degenerate states with only Struggle).
- [ ] All shape and legality assumptions are covered by tests for QAReviewer.
