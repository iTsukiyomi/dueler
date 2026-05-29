from __future__ import annotations

from . import config
from . import features

_LAZY = {
    "apply_action":          ("action_mask",   "apply_action"),
    "action_to_engine":      ("action_mask",   "action_to_engine"),
    "legal_action_mask":     ("action_mask",   "legal_action_mask"),
    "save_checkpoint":       ("checkpoint",    "save_checkpoint"),
    "load_checkpoint":       ("checkpoint",    "load_checkpoint"),
    "BattleEncoder":         ("encoder",       "BattleEncoder"),
    "HiddenInfoTracker":     ("hidden_info",   "HiddenInfoTracker"),
    "PokemonAlphaZeroNet":   ("network",       "PokemonAlphaZeroNet"),
    "InferenceEngine":       ("inference",     "InferenceEngine"),
    "PrioritizedReplayBuffer": ("replay_buffer", "PrioritizedReplayBuffer"),
    "TrajectoryBatch":         ("replay_buffer", "TrajectoryBatch"),
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


def __getattr__(name):
    if name in _LAZY:
        modname, attrname = _LAZY[name]
        from importlib import import_module
        mod = import_module(f"{__name__}.{modname}")
        return getattr(mod, attrname)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY.keys()))
