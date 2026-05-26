"""
ai/evaluation.py — Arena matches + ELO tracking.

Used in two places:

* During training, after every ``OPT_EVAL_EVERY`` steps we play
  ``EVAL_MATCHES`` headless games between the latest network and the best
  network so far. If the candidate's win rate ≥ ``EVAL_PROMOTE_WR`` we
  promote it.

* On demand from the Discord bot (``;duel npcaistats``) to print the
  current ELO trajectory.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

    def _guarded_match(*a, **kw):
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
        signal.alarm(180)
        try:
            return play_match(*a, **kw)
        except TimeoutError:
            return 0
        finally:
            signal.alarm(0)

    for i in range(n_matches):
        s = rng.randint(0, 2**31 - 1)
        # alternate sides to remove first-move advantage
        if i % 2 == 0:
            r = _guarded_match(candidate_inference, best_inference,
                           simulations=simulations, seed=s)
            if r == 1:
                wins += 1
            elif r == -1:
                losses += 1
            else:
                draws += 1
        else:
            r = _guarded_match(best_inference, candidate_inference,
                           simulations=simulations, seed=s)
            if r == 1:
                losses += 1
            elif r == -1:
                wins += 1
            else:
                draws += 1
    total = max(1, n_matches)
    return wins / total, wins, losses, draws


__all__ = ["EloState", "play_match", "evaluate"]
