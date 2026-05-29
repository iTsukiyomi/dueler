from __future__ import annotations

import math


def expected_score(player_elo: int, opponent_elo: int) -> float:
    """
    Standard Elo expected-score formula.

    Returns the probability [0, 1] that the player wins against
    the opponent.
    """
    return 1.0 / (1.0 + math.pow(10, (opponent_elo - player_elo) / 400.0))


def calculate_delta(
    winner_elo: int,
    loser_elo: int,
    *,
    k: int = 32,
) -> tuple[int, int]:
    """
    Calculate Elo deltas for the winner and loser.

    Parameters
    ----------
    winner_elo : int
        Current Elo of the winner.
    loser_elo : int
        Current Elo of the loser.
    k : int
        K-factor (volatility). Default 32 is standard for online play.

    Returns
    -------
    tuple[int, int]
        ``(winner_delta, loser_delta)`` where ``loser_delta`` is negative.
    """
    exp_w = expected_score(winner_elo, loser_elo)
    exp_l = expected_score(loser_elo, winner_elo)
    delta_w = round(k * (1.0 - exp_w))
    delta_l = round(k * (0.0 - exp_l))
    return delta_w, delta_l
