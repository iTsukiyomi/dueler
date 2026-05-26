"""
pokemonduel.services.battle_state_service
==========================================
Redis-backed battle state persistence for crash recovery.

Serialises the essential battle state into a Redis hash with a TTL,
allowing the bot to resume interrupted battles after a restart.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from ..core import cache

log = logging.getLogger("dueler.svc.battle_state")

_KEY_PREFIX = "battle:"
_STATE_TTL = 3600  # 1 hour — battles shouldn't last longer


class BattleStateService:
    """
    Manages serialisation and persistence of active battle states.

    Usage::

        svc = BattleStateService()
        battle_id = svc.generate_id()
        await svc.save_state(battle_id, {"turn": 5, "trainer1_hp": [...]})
        state = await svc.load_state(battle_id)
        await svc.delete_state(battle_id)
    """

    @staticmethod
    def generate_id() -> str:
        """Generate a unique battle ID."""
        return f"battle-{uuid.uuid4().hex[:12]}"

    async def save_state(self, battle_id: str, state: dict[str, Any]) -> None:
        """
        Persist battle state to Redis.

        The state dict is stored as a Redis hash with JSON-encoded values.
        """
        key = f"{_KEY_PREFIX}{battle_id}"
        await cache.hash_set(key, state, ttl=_STATE_TTL)
        log.debug("Battle state saved: %s", battle_id)

    async def load_state(self, battle_id: str) -> Optional[dict]:
        """
        Load a previously saved battle state.

        Returns ``None`` if the battle has expired or doesn't exist.
        """
        key = f"{_KEY_PREFIX}{battle_id}"
        data = await cache.hash_get_all(key)
        if data is None:
            return None

        # Attempt to JSON-decode values that look like JSON
        decoded = {}
        for k, v in data.items():
            try:
                decoded[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                decoded[k] = v
        return decoded

    async def delete_state(self, battle_id: str) -> None:
        """Remove a battle state from Redis (battle finished normally)."""
        key = f"{_KEY_PREFIX}{battle_id}"
        await cache.hash_delete(key)
        log.debug("Battle state cleared: %s", battle_id)

    async def list_active_battles(self) -> list[str]:
        """
        Return a list of active battle IDs.

        Uses a Redis SCAN to find all battle keys.
        """
        r = cache.get_redis()
        if r is None:
            return []

        battle_ids: list[str] = []
        cursor = 0
        while True:
            cursor, keys = await r.scan(
                cursor=cursor,
                match=f"{_KEY_PREFIX}*",
                count=100,
            )
            for k in keys:
                key_str = k.decode() if isinstance(k, bytes) else k
                battle_ids.append(key_str.removeprefix(_KEY_PREFIX))
            if cursor == 0:
                break
        return battle_ids

    async def get_active_count(self) -> int:
        """Return the number of currently active battles."""
        return len(await self.list_active_battles())
