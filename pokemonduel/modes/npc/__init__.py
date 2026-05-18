"""
modes/npc — backwards-compatibility shim.

The old DQN-based implementation has been replaced by the AlphaZero
system that lives under ``pokemonduel.ai``. We keep the public name
``NPCTeamAI`` so existing imports in the cog work without modification.
"""
from ...ai.npc_bridge import NPCTeamAI, reload_network
from .npc_team_gen import generate_npc_team, convert_to_raw_data, create_npc_team

__all__ = [
    "NPCTeamAI",
    "reload_network",
    "generate_npc_team",
    "convert_to_raw_data",
    "create_npc_team",
]
