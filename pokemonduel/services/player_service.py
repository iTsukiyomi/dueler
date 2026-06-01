from __future__ import annotations

import logging
import math
from typing import Optional

from ..repositories.player_repository import PlayerRepository
from ..core.database import get_db

log = logging.getLogger("dueler.svc.player")

_ELO_K = 32


def _expected_score(player_elo: int, opponent_elo: int) -> float:
    """Standard Elo expected-score formula."""
    return 1.0 / (1.0 + math.pow(10, (opponent_elo - player_elo) / 400.0))


def calculate_elo_delta(
    winner_elo: int, loser_elo: int, *, k: int = _ELO_K
) -> tuple[int, int]:
    """
    Calculate Elo deltas for the winner and loser.

    Returns ``(winner_delta, loser_delta)`` where loser_delta is negative.
    """
    expected_w = _expected_score(winner_elo, loser_elo)
    expected_l = _expected_score(loser_elo, winner_elo)
    delta_w = round(k * (1.0 - expected_w))
    delta_l = round(k * (0.0 - expected_l))
    return delta_w, delta_l


class PlayerService:
    """
    High-level operations on player profiles.

    Usage::

        svc = PlayerService()
        profile = await svc.ensure_profile(user_id, username)
        w_elo, l_elo = await svc.record_match_result(winner_id, loser_id)
    """

    def __init__(self) -> None:
        self._repo = PlayerRepository()

    async def ensure_profile(self, user_id: str, username: str) -> dict:
        """Get or create a player profile."""
        return await self._repo.get_or_create(str(user_id), username)

    async def get_profile(self, user_id: str) -> Optional[dict]:
        """Fetch a profile without auto-creating."""
        return await self._repo.get(str(user_id))


    async def record_match_result(
        self,
        winner_id: str,
        loser_id: str,
        *,
        money_reward: int = 0,
        turns: int = 0,
        duration: str = "0:00",
        winner_team: str = "Unknown",
        loser_team: str = "Unknown",
    ) -> tuple[int, int]:
        """
        Record a match outcome: update wins/losses, calculate Elo, award money, save history.

        Returns ``(winner_new_elo, loser_new_elo)``.
        """
        db = get_db()
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        winner = await self._repo.get(str(winner_id))
        loser = await self._repo.get(str(loser_id))

        if winner is None or loser is None:
            log.warning(
                "Cannot record match — missing profiles: winner=%s loser=%s",
                winner_id, loser_id,
            )
            return (0, 0)

        w_elo = winner.get("elo", 1000)
        l_elo = loser.get("elo", 1000)
        delta_w, delta_l = calculate_elo_delta(w_elo, l_elo)

        winner_doc = await self._repo.update_stats(
            str(winner_id), wins_delta=1, elo_delta=delta_w,
        )
        loser_doc = await self._repo.update_stats(
            str(loser_id), losses_delta=1, elo_delta=delta_l,
        )

        if money_reward > 0:
            await self._repo.update_wallet(str(winner_id), wallet_delta=money_reward)

        # Retrieve updated profiles to get final ELO/username/avatarUrl
        winner_final = await self._repo.get(str(winner_id))
        loser_final = await self._repo.get(str(loser_id))

        match_doc = {
            "player1_id": str(winner_id),
            "player2_id": str(loser_id),
            "player1_name": winner_final.get("username", "Unknown") if winner_final else "Unknown",
            "player2_name": loser_final.get("username", "Unknown") if loser_final else "Unknown",
            "player1_avatar": winner_final.get("avatarUrl", "") if winner_final else "",
            "player2_avatar": loser_final.get("avatarUrl", "") if loser_final else "",
            "winner_id": str(winner_id),
            "winner_name": winner_final.get("username", "Unknown") if winner_final else "Unknown",
            "player1_team": winner_team,
            "player2_team": loser_team,
            "player1_elo_change": delta_w,
            "player2_elo_change": delta_l,
            "turns": turns,
            "duration": duration,
            "timestamp": now,
            "type": "ranked"
        }
        try:
            await db["matches"].insert_one(match_doc)
        except Exception as e:
            log.warning("Failed to save match history: %s", e)

        new_w = winner_doc["elo"] if winner_doc else w_elo + delta_w
        new_l = loser_doc["elo"] if loser_doc else l_elo + delta_l

        log.info(
            "Match recorded: %s (Elo %d→%d) beat %s (Elo %d→%d)  Δ=(%+d, %+d)",
            winner_id, w_elo, new_w,
            loser_id, l_elo, new_l,
            delta_w, delta_l,
        )
        return new_w, new_l

    async def record_npc_match_result(
        self,
        player_id: str,
        username: str,
        *,
        won: bool,
        money_reward: int = 0,
        turns: int = 0,
        duration: str = "0:00",
        player_team: str = "Unknown",
        npc_team: str = "Unknown",
    ) -> int:
        """
        Record a match against an NPC: increment wins/losses, award money, save history, no Elo change.

        Returns the player's current Elo.
        """
        await self.ensure_profile(str(player_id), username)
        player = await self._repo.get(str(player_id))
        if player is None:
            log.warning("Cannot record NPC match — missing profile for player %s", player_id)
            return 1000

        w_elo = player.get("elo", 1000)

        if won:
            player_doc = await self._repo.update_stats(
                str(player_id), wins_delta=1, elo_delta=0,
            )
            if money_reward > 0:
                await self._repo.update_wallet(str(player_id), wallet_delta=money_reward)
        else:
            player_doc = await self._repo.update_stats(
                str(player_id), losses_delta=1, elo_delta=0,
            )

        db = get_db()
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        player_final = await self._repo.get(str(player_id))

        match_doc = {
            "player1_id": str(player_id),
            "player2_id": "npc",
            "player1_name": player_final.get("username", username) if player_final else username,
            "player2_name": "NPC Challenger",
            "player1_avatar": player_final.get("avatarUrl", "") if player_final else "",
            "player2_avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=npc",
            "winner_id": str(player_id) if won else "npc",
            "winner_name": (player_final.get("username", username) if player_final else username) if won else "NPC Challenger",
            "player1_team": player_team,
            "player2_team": npc_team,
            "player1_elo_change": 0,
            "player2_elo_change": 0,
            "turns": turns,
            "duration": duration,
            "timestamp": now,
            "type": "casual"
        }
        try:
            await db["matches"].insert_one(match_doc)
        except Exception as e:
            log.warning("Failed to save NPC match history: %s", e)

        return player_doc["elo"] if player_doc else w_elo


    async def get_balance(self, user_id: str) -> dict:
        """Return ``{wallet}`` for a player."""
        profile = await self._repo.get(str(user_id))
        if profile is None:
            return {"wallet": 0}
        return {
            "wallet": profile.get("wallet", 0),
        }


    async def get_leaderboard(
        self, offset: int = 0, limit: int = 10
    ) -> list[dict]:
        """Return top players by Elo."""
        return await self._repo.get_leaderboard(offset, limit)

    async def get_rank(self, user_id: str) -> Optional[int]:
        """Return the 1-based rank of a player."""
        return await self._repo.get_rank(str(user_id))


    async def set_active_party(
        self, user_id: str, team_name: Optional[str]
    ) -> None:
        """Set the player's active party name."""
        await self._repo.set_active_party(str(user_id), team_name)


    async def ensure_indexes(self) -> None:
        """Ensure database indexes exist."""
        await self._repo.ensure_indexes()
