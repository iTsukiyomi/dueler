"""
pokemonduel.ai — Foul-play MCTS battle AI (poke_engine backend).

Only the two names the cog actually imports are exported directly.
Everything else has been removed (no AlphaZero, no neural networks,
no self-play training loop).

Usage::

    from pokemonduel.ai import NPCTeamAI, reload_network
"""
from __future__ import annotations

from .npc_bridge import NPCTeamAI, reload_network

__all__ = ["NPCTeamAI", "reload_network"]
