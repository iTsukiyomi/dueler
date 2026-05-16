"""
npc_learning.py  ─  Double-DQN Pokemon Battle AI

The AI learns to WIN through reinforcement learning:
  • Win/loss terminal reward (±1.0)
  • Per-turn HP-swing + KO rewards (dense signal)
  • Double-DQN with experience replay (stable learning)
  • Shared weights across NPC vs NPC — both sides train the same brain

In NPC vs NPC mode (500 battles → 1000 training perspectives):
  • Battle N end: AI-1 trains and saves model  →  AI-2 loads updated model
  • Each battle adds ~20-40 transitions per AI, trains 16+ steps at end

Run directly to see training progress:
    python npc_learning.py
"""
from __future__ import annotations
import os, random, json
import numpy as np

# ── game imports (only needed when running inside the bot) ────────────────────
try:
    from ...enums import DamageClass
    from ...moves import Move as GameMove
    _IN_BOT = True
except ImportError:
    _IN_BOT = False

from ._dqn_core import (
    DQNetwork, ReplayBuffer,
    Q_NET_PATH, TGT_NET_PATH, BUFFER_PATH, STATS_PATH,
    N_FEATURES, N_ACTIONS, LR, GAMMA,
    EPS_START, EPS_END, EPS_DECAY,
    TGT_UPDATE, BATCH_SZ, MIN_BUF, SAVE_FREQ,
    STEPS_PER_TURN, STEPS_PER_END,
)

# ─────────────────────────────────────────────────────────────────────────────
# Shared brain — all NPCLearningAI instances in the same process
# share ONE model so NPC vs NPC trains both perspectives into one brain.
# ─────────────────────────────────────────────────────────────────────────────
class _SharedBrain:
    q_net:      DQNetwork    | None = None
    tgt_net:    DQNetwork    | None = None
    buffer:     ReplayBuffer | None = None
    battles:    int   = 0
    wins:       int   = 0
    epsilon:    float = EPS_START
    train_steps: int  = 0
    total_loss: float = 0.0
    wr_history: list  = []      # [(battle_num, win_rate), ...]
    action_dist: dict = {"move": 0, "switch": 0, "other": 0}
    ready:      bool  = False

    @classmethod
    def init(cls):
        if cls.ready:
            return
        cls.q_net   = DQNetwork()
        cls.tgt_net = DQNetwork()
        cls.buffer  = ReplayBuffer()
        cls._load()
        cls.ready   = True

    @classmethod
    def _load(cls):
        if os.path.exists(Q_NET_PATH):
            try:
                cls.q_net  = DQNetwork.load(Q_NET_PATH)
                cls.tgt_net = (DQNetwork.load(TGT_NET_PATH)
                               if os.path.exists(TGT_NET_PATH)
                               else DQNetwork())
                if not os.path.exists(TGT_NET_PATH):
                    cls.tgt_net.copy_weights_from(cls.q_net)
                print(f"✅  DQN loaded — Adam t={cls.q_net.t:,}")
            except Exception as e:
                print(f"⚠️  Model load error ({e}) — starting fresh")
                cls.q_net  = DQNetwork()
                cls.tgt_net = DQNetwork()
                cls.tgt_net.copy_weights_from(cls.q_net)
        else:
            cls.tgt_net.copy_weights_from(cls.q_net)
            print("🆕  No saved model — starting fresh")
        cls.buffer.load(BUFFER_PATH)
        cls._load_stats()

    @classmethod
    def _load_stats(cls):
        if not os.path.exists(STATS_PATH):
            return
        try:
            with open(STATS_PATH) as f:
                d = json.load(f)
            cls.battles    = d.get("battles",     0)
            cls.wins       = d.get("wins",        0)
            saved_eps      = d.get("epsilon", EPS_START)
            # If epsilon is already at the floor (model over-exploited early),
            # bump it up so the agent explores more before converging again.
            if saved_eps <= EPS_END + 1e-4:
                cls.epsilon = min(0.30, EPS_START)   # re-explore from 30%
                print(f"⚡  Epsilon was at floor — reset to {cls.epsilon:.2f} for fresh exploration")
            else:
                cls.epsilon = max(EPS_END, saved_eps)
            cls.train_steps = d.get("train_steps", 0)
            cls.total_loss  = d.get("total_loss",  0.0)
            cls.wr_history  = d.get("wr_history",  [])
            cls.action_dist = d.get("action_dist",
                                    {"move": 0, "switch": 0, "other": 0})
        except Exception:
            pass

    @classmethod
    def save(cls):
        try:
            cls.q_net.save(Q_NET_PATH)
            cls.tgt_net.save(TGT_NET_PATH)
            cls.buffer.save(BUFFER_PATH)
            avg_loss = cls.total_loss / max(1, cls.train_steps)
            with open(STATS_PATH, "w") as f:
                json.dump({
                    "battles":     cls.battles,
                    "wins":        cls.wins,
                    "epsilon":     cls.epsilon,
                    "train_steps": cls.train_steps,
                    "avg_loss":    avg_loss,
                    "total_loss":  cls.total_loss,
                    "buffer_size": len(cls.buffer),
                    "wr_history":  cls.wr_history[-100:],
                    "action_dist": cls.action_dist,
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Save error: {e}")

    @classmethod
    def train_step(cls) -> float:
        """One Double-DQN update. Returns TD loss."""
        s, a, r, ns, d = cls.buffer.sample(BATCH_SZ)

        # Double DQN: main net selects action, target net evaluates it
        next_q_main = cls.q_net.predict(ns)
        next_q_tgt  = cls.tgt_net.predict(ns)
        best_acts   = np.argmax(next_q_main, axis=1)
        next_vals   = next_q_tgt[np.arange(len(s)), best_acts]

        td_targets  = r + GAMMA * next_vals * (1.0 - d)
        loss        = cls.q_net.train_batch(s, td_targets, a)
        cls.train_steps += 1
        cls.total_loss  += loss
        return loss


_G = _SharedBrain          # alias for brevity


# ═════════════════════════════════════════════════════════════════════════════
class NPCLearningAI:
    """
    DQN battle AI — plug-in replacement for NPCTeamAI.
    Integrates with the Trainer object's .move() / .swap() / .set_ai() hooks.
    """

    def __init__(self, trainer, opponent):
        self.trainer  = trainer
        self.opponent = opponent
        self.battle   = None
        self.turn_count = 0
        _G.init()                         # idempotent — only loads once

        # ── per-episode bookkeeping (not shared) ──────────────────────────
        self._pending_state:  np.ndarray | None = None
        self._pending_action: int        | None = None
        self._last_state:     np.ndarray | None = None
        self._prev_our_hp    = None
        self._prev_opp_hp    = None
        self._prev_our_alive = None
        self._prev_opp_alive = None

    # ═════════════════════════════════════════════════════════════════════════
    # Battle hooks (called by the Trainer / Battle engine)
    # ═════════════════════════════════════════════════════════════════════════

    def set_battle(self, battle):
        """
        Called at the START of every turn.
        Records the transition (s, a, r, s') from the PREVIOUS turn.
        """
        self.battle     = battle
        self.turn_count += 1

        if self._pending_state is not None:
            our = self.trainer.current_pokemon
            opp = self.opponent.current_pokemon

            cur_our_hp    = _total_hp(self.trainer)
            cur_opp_hp    = _total_hp(self.opponent)
            cur_our_alive = _alive(self.trainer)
            cur_opp_alive = _alive(self.opponent)

            reward     = _step_reward(
                self._prev_our_hp,    cur_our_hp,
                self._prev_opp_hp,    cur_opp_hp,
                self._prev_our_alive, cur_our_alive,
                self._prev_opp_alive, cur_opp_alive,
                self.trainer, self.opponent,
            )
            next_state = self._encode(our, opp)
            _G.buffer.push(self._pending_state, self._pending_action,
                           reward, next_state, False)
            self._last_state  = self._pending_state
            self._pending_state  = None
            self._pending_action = None

            if len(_G.buffer) >= MIN_BUF:
                for _ in range(STEPS_PER_TURN):
                    _G.train_step()

        # snapshot HP for next reward computation
        self._prev_our_hp    = _total_hp(self.trainer)
        self._prev_opp_hp    = _total_hp(self.opponent)
        self._prev_our_alive = _alive(self.trainer)
        self._prev_opp_alive = _alive(self.opponent)

    def choose_lead(self) -> int:
        """Pick starting Pokémon — heuristic (battle hasn't started yet)."""
        if not self.trainer.party:
            return 0
        best_idx, best_score = 0, -999.0
        for i, poke in enumerate(self.trainer.party):
            if poke.hp <= 0:
                continue
            score = poke.get_raw_speed() / 10.0
            for m in poke.moves:
                if getattr(m, "effect", None) in [34, 372, 373]:   # Spikes / SR / TS
                    score += 30
            if score > best_score:
                best_score = score;  best_idx = i
        print(f"  🎯 Lead → {self.trainer.party[best_idx].name}")
        return best_idx

    def choose_move(self):
        """
        Select the best move or proactive switch.
        Returns (move_obj, switch_party_idx_or_None).
        """
        status, movedata = self.trainer.valid_moves(self.opponent.current_pokemon)

        if status == "forced":
            return movedata, None
        if status == "struggle":
            if _IN_BOT:
                return GameMove.struggle(), None
            return movedata[0], None

        our = self.trainer.current_pokemon
        opp = self.opponent.current_pokemon
        if not our or not opp:
            # Safely fall back — do NOT dereference our/opp if either is None
            if our and our.moves and movedata:
                return our.moves[movedata[0]], None
            # Absolute last resort: return struggle-equivalent
            if _IN_BOT:
                return GameMove.struggle(), None
            return movedata[0] if movedata else 0, None

        valid_sw = self.trainer.valid_swaps(opp, self.battle, check_trap=False)
        state    = self._encode(our, opp)
        mask     = _valid_mask(movedata, valid_sw)
        action   = _select_action(state, mask)

        # record for next turn's transition
        self._pending_state  = state
        self._pending_action = action

        # track action distribution
        if action < 4:
            pw = getattr(our.moves[action if action in movedata else movedata[0]], "power", 0) or 0
            _G.action_dist["move" if pw > 0 else "other"] += 1
        else:
            _G.action_dist["switch"] += 1

        self._log_decision(our, opp, state, mask, action, movedata, valid_sw)
        return _action_to_move(action, movedata, valid_sw, our)

    def choose_switch(self, mid_turn: bool = False) -> int | None:
        """
        Choose best switch-in.  ALWAYS returns a valid index — never None —
        because returning None on a forced switch causes an automatic forfeit.
        """
        opp      = self.opponent.current_pokemon if self.opponent else None
        valid_sw = self.trainer.valid_swaps(opp, self.battle, check_trap=False)
        if not valid_sw:
            return None

        our   = self.trainer.current_pokemon
        state = self._encode(our, opp) if our and opp else np.full(N_FEATURES, 0.5, np.float32)
        q     = _G.q_net.predict(state)

        best_idx, best_q = valid_sw[0], -1e9
        for pi in valid_sw:
            if pi < 5 and q[4 + pi] > best_q:
                best_q   = q[4 + pi]
                best_idx = pi

        name = self.trainer.party[best_idx].name
        print(f"  🔄 Forced switch → {name}  (Q={best_q:+.2f})")
        return best_idx

    def on_battle_end(self, npc_won: bool):
        """
        Terminal reward, heavy training pass, target-net update, ε decay, save.
        """
        _G.battles += 1
        if npc_won:
            _G.wins += 1

        terminal_r = 1.0 if npc_won else -1.0
        terminal_s = (self._last_state
                      if self._last_state is not None
                      else np.full(N_FEATURES, 0.5, np.float32))

        # store terminal transition
        if self._pending_state is not None:
            _G.buffer.push(self._pending_state, self._pending_action or 0,
                           terminal_r, terminal_s, True)
        else:
            _G.buffer.push(terminal_s, 0, terminal_r, terminal_s, True)

        # heavy training at battle end
        if len(_G.buffer) >= MIN_BUF:
            for _ in range(STEPS_PER_END):
                _G.train_step()

        # update target network
        if _G.battles % TGT_UPDATE == 0:
            _G.tgt_net.copy_weights_from(_G.q_net)
            print(f"  🎯 Target network synced (battle {_G.battles})")

        # decay exploration
        _G.epsilon = max(EPS_END, _G.epsilon * EPS_DECAY)

        # win-rate history (every 10 battles)
        if _G.battles % 10 == 0:
            wr = _G.wins / _G.battles
            _G.wr_history.append((_G.battles, round(wr, 3)))

        # checkpoint
        if _G.battles % SAVE_FREQ == 0:
            _G.save()

        self._log_battle_end(npc_won)
        self._reset_episode()

    # ═════════════════════════════════════════════════════════════════════════
    # Feature encoding  —  64 features matching SimPokemon and DuelPokemon
    # ═════════════════════════════════════════════════════════════════════════

    def _encode(self, our, opp) -> np.ndarray:
        if our is None or opp is None:
            return np.full(N_FEATURES, 0.5, np.float32)

        f = []
        bt = self.battle

        # ── Group 1: our active Pokémon (16) ─────────────────────────────
        f.append(our.hp / max(1, our.starting_hp))
        f.append(getattr(our, "attack_stage",  0) / 6)
        f.append(getattr(our, "defense_stage", 0) / 6)
        f.append(getattr(our, "spatk_stage",   0) / 6)
        f.append(getattr(our, "spdef_stage",   0) / 6)
        f.append(getattr(our, "speed_stage",   0) / 6)

        nv = our.nv
        f.append(1.0 if getattr(nv, "burn",     False) else 0.0)
        f.append(1.0 if getattr(nv, "paralyze", False) else 0.0)
        f.append(1.0 if (getattr(nv, "toxic",   False)
                         or getattr(nv, "poison", False)) else 0.0)
        f.append(1.0 if (getattr(nv, "sleep",   False)
                         or getattr(nv, "freeze", False)) else 0.0)

        spd = our.get_speed(bt) if bt else our.get_raw_speed()
        atk = our.get_attack(bt) if bt and hasattr(our, "get_attack") else getattr(our, "attack", 100)
        spa = our.get_spatk(bt)  if bt and hasattr(our, "get_spatk")  else getattr(our, "spatk",  100)
        f.extend([min(spd / 300, 1.0), min(atk / 300, 1.0), min(spa / 300, 1.0)])

        best_pow, best_eff, has_prio = 0.0, 0.5, 0.0
        te = getattr(bt, "type_effectiveness", {}) if bt else {}
        for m in our.moves:
            pw = getattr(m, "power", 0) or 0
            best_pow = max(best_pow, pw / 150)
            if pw > 0:
                eff = _type_eff(m, opp.type_ids, te)
                best_eff = max(best_eff, min(eff / 4, 1.0))
            if getattr(m, "priority", 0) > 0:
                has_prio = 1.0
        f.extend([min(best_pow, 1.0), best_eff, has_prio])   # f[13..15]
        # total so far: 16

        # ── Group 2: opponent active Pokémon (10) ─────────────────────────
        f.append(opp.hp / max(1, opp.starting_hp))
        onv = opp.nv
        f.append(1.0 if getattr(onv, "burn",     False) else 0.0)
        f.append(1.0 if getattr(onv, "paralyze", False) else 0.0)
        f.append(1.0 if (getattr(onv, "toxic",   False)
                         or getattr(onv, "poison", False)) else 0.0)
        f.append(1.0 if (getattr(onv, "sleep",   False)
                         or getattr(onv, "freeze", False)) else 0.0)

        o_spd = opp.get_speed(bt) if bt else opp.get_raw_speed()
        o_atk = opp.get_attack(bt) if bt and hasattr(opp, "get_attack") else getattr(opp, "attack", 100)
        o_spa = opp.get_spatk(bt)  if bt and hasattr(opp, "get_spatk")  else getattr(opp, "spatk",  100)
        f.extend([min(o_spd / 300, 1.0), min(o_atk / 300, 1.0), min(o_spa / 300, 1.0)])

        opp_best_eff, opp_has_prio = 0.5, 0.0
        for m in opp.moves:
            pw = getattr(m, "power", 0) or 0
            if pw > 0:
                eff = _type_eff(m, our.type_ids, te)
                opp_best_eff = max(opp_best_eff, min(eff / 4, 1.0))
            if getattr(m, "priority", 0) > 0:
                opp_has_prio = 1.0
        f.extend([opp_best_eff, opp_has_prio])               # total: 26

        # ── Group 3: our 4 moves in detail (4 × 4 = 16) ──────────────────
        for i in range(4):
            if i < len(our.moves):
                m   = our.moves[i]
                pw  = getattr(m, "power", 0) or 0
                eff = _type_eff(m, opp.type_ids, te) if pw > 0 else 1.0
                acc = (getattr(m, "accuracy", 100) or 100) / 100
                pri = 1.0 if getattr(m, "priority", 0) > 0 else 0.0
                f.extend([min(pw / 150, 1.0), min(eff / 4, 1.0), acc, pri])
            else:
                f.extend([0.0, 0.0, 0.0, 0.0])               # total: 42

        # ── Group 4: switch options (6) ──────────────────────────────────
        valid_sw   = self.trainer.valid_swaps(opp, bt, check_trap=False)
        can_sw     = 1.0 if valid_sw else 0.0
        n_sw       = len(valid_sw) / 5.0
        best_sw_hp, best_sw_eff, best_sw_spd = 0.0, 0.5, 0.0
        bench_hps  = []
        for pi in valid_sw:
            cand = self.trainer.party[pi]
            hp_r = cand.hp / max(1, cand.starting_hp)
            best_sw_hp = max(best_sw_hp, hp_r)
            bench_hps.append(hp_r)
            cand_spd = cand.get_raw_speed()
            if cand_spd > o_spd:
                best_sw_spd = 1.0
            for m in cand.moves:
                pw = getattr(m, "power", 0) or 0
                if pw > 0:
                    eff = _type_eff(m, opp.type_ids, te)
                    best_sw_eff = max(best_sw_eff, min(eff / 4, 1.0))
        avg_bench = float(np.mean(bench_hps)) if bench_hps else 0.5
        f.extend([best_sw_hp, best_sw_eff, n_sw, can_sw, avg_bench, best_sw_spd])  # total: 48

        # ── Group 5: field state (12) ────────────────────────────────────
        tr, op = self.trainer, self.opponent
        f.extend([
            getattr(tr, "spikes",       0) / 3,
            getattr(tr, "toxic_spikes", 0) / 2,
            1.0 if getattr(tr, "stealth_rock", False) else 0.0,
            1.0 if getattr(tr, "sticky_web",   False) else 0.0,
            getattr(op, "spikes",       0) / 3,
            getattr(op, "toxic_spikes", 0) / 2,
            1.0 if getattr(op, "stealth_rock", False) else 0.0,
            1.0 if getattr(op, "sticky_web",   False) else 0.0,
            _alive(tr) / 6,
            _alive(op) / 6,
            _avg_hp(tr),
            _avg_hp(op),
        ])                                                     # total: 60

        # ── Group 6: global context (4) ──────────────────────────────────
        our_tot = _total_hp(tr);  opp_tot = _total_hp(op)
        momentum = our_tot / max(1, our_tot + opp_tot)
        f.extend([
            min(self.turn_count / 50, 1.0),
            1.0 if spd > o_spd else (0.5 if spd == o_spd else 0.0),
            momentum,
            (_alive(tr) - _alive(op) + 6) / 12,
        ])                                                     # total: 64

        arr = np.array(f, dtype=np.float32)
        assert len(arr) == N_FEATURES, f"BUG: {len(arr)} features instead of {N_FEATURES}"
        return arr

    # ═════════════════════════════════════════════════════════════════════════
    # Logging
    # ═════════════════════════════════════════════════════════════════════════

    def _log_decision(self, our, opp, state, mask, chosen_action, movedata, valid_sw):
        """Print a clean decision breakdown every turn."""
        q     = _G.q_net.predict(state)
        eps   = _G.epsilon
        mode  = "EXPLORE🎲" if random.random() < eps else f"EXPLOIT🎯 ε={eps:.3f}"
        spd   = our.get_speed(self.battle) if self.battle else our.get_raw_speed()
        o_spd = opp.get_speed(self.battle) if self.battle else opp.get_raw_speed()
        spd_s = f"FASTER({int(spd)}>{int(o_spd)})" if spd > o_spd else f"SLOWER({int(spd)}<{int(o_spd)})"
        te    = getattr(self.battle, "type_effectiveness", {}) if self.battle else {}

        # our HP%
        our_hp_pct = f"{our.hp*100//our.starting_hp}%"
        opp_hp_pct = f"{opp.hp*100//opp.starting_hp}%"

        buf_sz = len(_G.buffer)
        avg_loss = _G.total_loss / max(1, _G.train_steps)

        print(f"\n┌─ Turn {self.turn_count} [{mode}] {'─'*38}┐")
        print(f"│  {our.name}({our_hp_pct}) vs {opp.name}({opp_hp_pct})  │  {spd_s}")
        print(f"│  Buf:{buf_sz:,}  Steps:{_G.train_steps:,}  Loss:{avg_loss:.4f}")
        print(f"├─ Move Rankings {'─'*46}┤")

        for mi in range(4):
            if mi >= len(our.moves):
                break
            m      = our.moves[mi]
            pw     = getattr(m, "power", 0) or 0
            valid  = mi in movedata
            eff    = _type_eff(m, opp.type_ids, te) if pw > 0 else 1.0
            stab   = "STAB" if m.type in getattr(our, "type_ids", []) and pw > 0 else ""
            eff_s  = (f"{eff:.1f}x" if eff != 1.0 else "  1x") if pw > 0 else "status"
            star   = "★" if mi == chosen_action and mi < 4 else " "
            inv    = "" if valid else "[PP OUT]"
            qv     = q[mi] if valid else float("nan")
            print(f"│ {star} {m.name:<16} Q={qv:+6.2f}  {stab:<4} {eff_s:<6}  pw={pw:<4} acc={getattr(m,'accuracy',100) or 100}  {inv}")

        if valid_sw:
            print(f"├─ Switch Options {'─'*45}┤")
            best_move_q  = max((q[mi] for mi in movedata if mi < 4), default=-999)
            best_sw_q    = max((q[4+pi] for pi in valid_sw if pi < 5), default=-999)
            for pi in valid_sw[:3]:
                cand = self.trainer.party[pi]
                hp_r = f"{cand.hp*100//max(1,cand.starting_hp)}%"
                qv   = q[4 + pi] if pi < 5 else float("nan")
                star = "★" if chosen_action == 4 + pi else " "
                print(f"│ {star} {cand.name:<16} Q={qv:+6.2f}  hp={hp_r}")
            decision = ("SWITCH" if chosen_action >= 4
                        else f"STAY IN (best move Q={best_move_q:+.2f} > switch Q={best_sw_q:+.2f})")
            print(f"│   → {decision}")

        chosen_name = (
            our.moves[chosen_action if chosen_action in movedata else movedata[0]].name
            if chosen_action < 4
            else f"switch→{self.trainer.party[chosen_action-4].name}"
        )
        print(f"├─ CHOSEN: {chosen_name} {'─'*(50-len(chosen_name))}┤")
        print(f"└{'─'*63}┘")

    def _log_battle_end(self, won: bool):
        wr    = _G.wins / max(1, _G.battles)
        avg_l = _G.total_loss / max(1, _G.train_steps)
        icon  = "🏆 WON" if won else "💀 LOST"
        print(f"\n{'═'*60}")
        print(f"  Battle {_G.battles} │ {icon}")
        print(f"  Win rate  : {_G.wins}/{_G.battles} ({wr:.1%})  "
              f"{'▓'*int(wr*30)}{'░'*(30-int(wr*30))}")
        print(f"  Epsilon   : {_G.epsilon:.4f}  "
              f"{'[exploring]' if _G.epsilon > 0.3 else '[exploiting]'}")
        print(f"  Buffer    : {len(_G.buffer):,} transitions")
        print(f"  Avg loss  : {avg_l:.5f}")
        print(f"{'═'*60}\n")

    # ═════════════════════════════════════════════════════════════════════════
    # Internal helpers
    # ═════════════════════════════════════════════════════════════════════════

    def _reset_episode(self):
        self._pending_state  = None
        self._pending_action = None
        self._last_state     = None
        self._prev_our_hp    = None
        self._prev_opp_hp    = None
        self._prev_our_alive = None
        self._prev_opp_alive = None
        self.turn_count      = 0


# ═════════════════════════════════════════════════════════════════════════════
# Pure helper functions (no self)
# ═════════════════════════════════════════════════════════════════════════════

def _total_hp(trainer) -> float:
    return sum(p.hp for p in trainer.party)

def _alive(trainer) -> int:
    return sum(1 for p in trainer.party if p.hp > 0)

def _avg_hp(trainer) -> float:
    alive = [p for p in trainer.party if p.hp > 0]
    if not alive:
        return 0.0
    return float(np.mean([p.hp / max(1, p.starting_hp) for p in alive]))

def _type_eff(move, defender_type_ids: list, te: dict) -> float:
    """Compute type effectiveness multiplier from the battle type-effectiveness table."""
    eff = 1.0
    mt  = getattr(move, "type", None)
    if mt is None:
        return 1.0
    for dt in defender_type_ids:
        eff *= te.get((mt, dt), 100) / 100.0
    return eff

def _step_reward(prev_our, cur_our, prev_opp, cur_opp,
                 prev_alive_our, cur_alive_our,
                 prev_alive_opp, cur_alive_opp,
                 trainer, opponent) -> float:
    """
    Intermediate reward for one turn.
    Dense signal: HP swings + KOs.  Clipped to [-1, 1].
    """
    our_max = sum(p.starting_hp for p in trainer.party)  or 1
    opp_max = sum(p.starting_hp for p in opponent.party) or 1

    hp_loss_us  = max(0, prev_our - cur_our) / our_max
    hp_loss_opp = max(0, prev_opp - cur_opp) / opp_max

    our_faints = max(0, prev_alive_our - cur_alive_our)
    opp_faints = max(0, prev_alive_opp - cur_alive_opp)

    r  = (hp_loss_opp - hp_loss_us) * 0.3
    r += opp_faints * 0.25
    r -= our_faints * 0.25
    return float(np.clip(r, -1.0, 1.0))

def _valid_mask(move_indices: list, switch_indices: list) -> np.ndarray:
    mask = np.zeros(N_ACTIONS, dtype=bool)
    for mi in move_indices:
        if 0 <= mi < 4:
            mask[mi] = True
    for pi in switch_indices:
        if 0 <= pi < 5:
            mask[4 + pi] = True
    if not mask.any():
        mask[:] = True     # absolute fallback
    return mask

def _select_action(state: np.ndarray, mask: np.ndarray) -> int:
    if random.random() < _G.epsilon:
        valid = np.where(mask)[0]
        return int(np.random.choice(valid))
    q        = _G.q_net.predict(state)
    q_masked = q.copy();  q_masked[~mask] = -1e9
    return int(np.argmax(q_masked))

def _action_to_move(action: int, movedata: list, valid_sw: list, our):
    """Convert a 0-8 action index into (move_obj, switch_party_idx_or_None)."""
    if action < 4:
        idx = action if action in movedata else movedata[0]
        return our.moves[idx], None
    else:
        party_idx = action - 4
        # confirm it's in valid_sw; fallback to first valid if not
        if party_idx not in valid_sw and valid_sw:
            party_idx = valid_sw[0]
        fallback_move = our.moves[movedata[0]]
        return fallback_move, party_idx


# ── backward-compat alias ────────────────────────────────────────────────────
NPCTeamAI = NPCLearningAI


# ═════════════════════════════════════════════════════════════════════════════
# Standalone progress viewer
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _dqn_core import show_progress
    show_progress()
