"""
pokemonduel.ai — AlphaZero-style policy/value Pokémon battle AI.

This ``__init__`` is intentionally minimal so that importing
``pokemonduel.ai`` (or ``pokemonduel.ai.config`` / ``features``) does not
drag in the rest of the engine. Heavy submodules — ``simulator``,
``mcts``, ``selfplay``, ``trainer``, ``distributed``, ``npc_bridge``,
``evaluation`` — are imported lazily on first attribute access.

Quick top-level access::

    from pokemonduel.ai import NPCTeamAI         # → npc_bridge.NPCTeamAI
    from pokemonduel.ai import Trainer           # → trainer.Trainer
    from pokemonduel.ai import HeadlessBattle    # → simulator.HeadlessBattle

For programmatic access, the lazy attribute resolution is implemented
through ``__getattr__`` (PEP-562).
"""
from __future__ import annotations

from . import config        # noqa: F401   (safe, no engine deps)
from . import features      # noqa: F401   (safe, no engine deps)

# Lazy attribute table — names → (module_name, attribute_name)
_LAZY = {
    # action / mask helpers (engine-aware)
    "apply_action":          ("action_mask",   "apply_action"),
    "action_to_engine":      ("action_mask",   "action_to_engine"),
    "legal_action_mask":     ("action_mask",   "legal_action_mask"),
    # checkpointing
    "save_checkpoint":       ("checkpoint",    "save_checkpoint"),
    "load_checkpoint":       ("checkpoint",    "load_checkpoint"),
    # encoder / hidden info
    "BattleEncoder":         ("encoder",       "BattleEncoder"),
    "HiddenInfoTracker":     ("hidden_info",   "HiddenInfoTracker"),
    # network / inference
    "PokemonAlphaZeroNet":   ("network",       "PokemonAlphaZeroNet"),
    "InferenceEngine":       ("inference",     "InferenceEngine"),
    # replay
    "PrioritizedReplayBuffer": ("replay_buffer", "PrioritizedReplayBuffer"),
    "TrajectoryBatch":         ("replay_buffer", "TrajectoryBatch"),
    # heavy engine-aware modules
    "HeadlessBattle":         ("simulator",     "HeadlessBattle"),
    "run_turn":               ("simulator",     "run_turn"),
    "initial_send_out":       ("simulator",     "initial_send_out"),
    "MCTS":                   ("mcts",          "MCTS"),
    "Trainer":                ("trainer",       "Trainer"),
    "EloState":               ("evaluation",    "EloState"),
    "evaluate":               ("evaluation",    "evaluate"),
    "play_match":             ("evaluation",    "play_match"),
    "build_party":            ("team_loader",   "build_party"),
    "random_team":            ("team_loader",   "random_team"),
    "random_two_teams":       ("team_loader",   "random_two_teams"),
    "NPCTeamAI":              ("npc_bridge",    "NPCTeamAI"),
    "reload_network":         ("npc_bridge",    "reload_network"),
    "DistributedTrainer":     ("distributed",   "DistributedTrainer"),
}

__all__ = ["config", "features", *list(_LAZY)]


def __getattr__(name):                                       # PEP 562
    if name in _LAZY:
        modname, attrname = _LAZY[name]
        from importlib import import_module
        mod = import_module(f"{__name__}.{modname}")
        return getattr(mod, attrname)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY.keys()))
