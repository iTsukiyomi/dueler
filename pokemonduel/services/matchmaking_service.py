from __future__ import annotations

import json
import logging
from typing import Optional

from ..core import cache

log = logging.getLogger("dueler.svc.matchmaking")

_QUEUE_KEY = "matchmaking:ranked"
_DEFAULT_ELO_RANGE = 200


class MatchmakingService:
    """
    Manages the ranked matchmaking queue.

    Usage::

        svc = MatchmakingService()
        await svc.enqueue(user_id, elo=1200)
        match = await svc.dequeue_match(elo=1200, elo_range=200)
        if match:
            player_a, player_b = match
    """

    async def enqueue(self, user_id: str, elo: int) -> None:
        """Add a player to the matchmaking queue."""
        entry = json.dumps({"user_id": str(user_id), "elo": elo})
        await cache.queue_push(_QUEUE_KEY, entry)
        log.info("Player %s queued for matchmaking (Elo %d)", user_id, elo)

    async def dequeue_match(
        self,
        user_id: str,
        elo: int,
        *,
        elo_range: int = _DEFAULT_ELO_RANGE,
    ) -> Optional[tuple[str, str]]:
        """
        Try to find a suitable opponent from the queue.

        Scans the queue for a player within ``elo_range`` of the
        requesting player.  Returns ``(player_a_id, player_b_id)``
        if a match is found, or ``None`` if no suitable opponent exists.
        """
        r = cache.get_redis()
        if r is None:
            return None

        queue_len = await cache.queue_length(_QUEUE_KEY)
        if queue_len == 0:
            return None

        # Scan the queue for a compatible opponent.
        # We read the full list and find the best match by Elo proximity.
        # pyrefly: ignore [not-async]
        raw_entries = await r.lrange(_QUEUE_KEY, 0, -1)
        best_match = None
        best_delta = float("inf")

        for raw in raw_entries:
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            opponent_id = entry.get("user_id", "")
            opponent_elo = entry.get("elo", 1000)

            if str(opponent_id) == str(user_id):
                continue

            delta = abs(elo - opponent_elo)
            if delta <= elo_range and delta < best_delta:
                best_match = (opponent_id, raw)
                best_delta = delta

        if best_match is None:
            return None

        opponent_id, raw_entry = best_match

        removed = await cache.queue_remove(
            _QUEUE_KEY,
            raw_entry.decode() if isinstance(raw_entry, bytes) else raw_entry,
        )
        if removed == 0:
            # Someone else grabbed this opponent — race condition.
            return None

        log.info(
            "Match found: %s (Elo %d) vs %s (Elo delta: %d)",
            user_id, elo, opponent_id, best_delta,
        )
        return (str(user_id), str(opponent_id))

    async def cancel(self, user_id: str) -> bool:
        """
        Remove a player from the matchmaking queue.

        Returns ``True`` if the player was actually in the queue.
        """
        r = cache.get_redis()
        if r is None:
            return False

        # pyrefly: ignore [not-async]
        raw_entries = await r.lrange(_QUEUE_KEY, 0, -1)
        for raw in raw_entries:
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if str(entry.get("user_id", "")) == str(user_id):
                removed = await cache.queue_remove(
                    _QUEUE_KEY,
                    raw.decode() if isinstance(raw, bytes) else raw,
                )
                if removed > 0:
                    log.info("Player %s removed from matchmaking queue.", user_id)
                    return True
        return False

    async def get_queue_size(self) -> int:
        """Return the number of players currently in queue."""
        return await cache.queue_length(_QUEUE_KEY)
