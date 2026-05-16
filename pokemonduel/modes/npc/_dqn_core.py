"""
_dqn_core.py  ─  Pure-NumPy Double-DQN brain + experience replay buffer.
No game imports → runs standalone for pre-training and progress viewing.

Run directly to view training progress:
    python _dqn_core.py
"""
import os, json
import numpy as np
import joblib
from collections import deque

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_data")
Q_NET_PATH   = os.path.join(DATA_DIR, "q_network.pkl")
TGT_NET_PATH = os.path.join(DATA_DIR, "q_target.pkl")
BUFFER_PATH  = os.path.join(DATA_DIR, "replay_buffer.pkl")
STATS_PATH   = os.path.join(DATA_DIR, "ai_stats.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Hyper-parameters ──────────────────────────────────────────────────────────
N_FEATURES  = 64
N_ACTIONS   = 9          # actions 0-3: moves │ actions 4-8: switch to party[0-4]
LR          = 2e-4       # Adam learning rate
GAMMA       = 0.97       # discount (higher = more long-term thinking)
EPS_START   = 1.0        # start fully exploring
EPS_END     = 0.08       # floor: 8% random keeps diversity, avoids pure exploitation
EPS_DECAY   = 0.9985     # per battle; hits floor ~battle 2500 (was 500 — too fast)
TGT_UPDATE  = 25         # copy weights to target net every N battles
BATCH_SZ    = 512        # replay batch size
MIN_BUF     = 1_000      # don't train until buffer has this many samples
SAVE_FREQ   = 10         # checkpoint to disk every N battles
STEPS_PER_TURN  = 2     # training steps per in-battle transition
STEPS_PER_END   = 64    # training steps at battle end (was 32 — doubled)


# ═════════════════════════════════════════════════════════════════════════════
class DQNetwork:
    """
    Deep Q-Network — pure NumPy, zero extra dependencies.

    Architecture:  64 → 256 → 128 → 64 → 9
    Activation:    ReLU (hidden), linear (output)
    Optimiser:     Adam  (β₁=0.9, β₂=0.999)
    Init:          He — correct for ReLU nets
    """

    ARCH = (N_FEATURES, 256, 128, 64, N_ACTIONS)

    def __init__(self, lr: float = LR):
        self.lr = lr
        sizes   = self.ARCH
        n       = len(sizes) - 1

        # He init: std = √(2 / fan_in)
        self.W = [(np.random.randn(sizes[i], sizes[i+1]) * np.sqrt(2.0 / sizes[i])).astype(np.float32)
                  for i in range(n)]
        self.b = [np.zeros(sizes[i+1], dtype=np.float32) for i in range(n)]

        # Adam first/second moments
        self.t   = 0
        self.mW  = [np.zeros_like(w) for w in self.W]
        self.vW  = [np.zeros_like(w) for w in self.W]
        self.mb  = [np.zeros_like(b) for b in self.b]
        self.vb  = [np.zeros_like(b) for b in self.b]
        self.B1, self.B2, self.AEPS = 0.9, 0.999, 1e-8

    # ── forward ──────────────────────────────────────────────────────────────
    def predict(self, x: np.ndarray) -> np.ndarray:
        """x: (N_FEATURES,) or (B, N_FEATURES)  →  Q-values same leading shape."""
        single = x.ndim == 1
        h = (x[np.newaxis] if single else x).astype(np.float32)
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = h @ W + b
            h = np.maximum(0, z) if i < len(self.W) - 1 else z   # ReLU / linear
        return h[0] if single else h

    # ── training step ─────────────────────────────────────────────────────────
    def train_batch(self,
                    states:     np.ndarray,   # (B, N_FEATURES)
                    td_targets: np.ndarray,   # (B,)
                    actions:    np.ndarray,   # (B,) int
                    ) -> float:
        """
        Double-DQN update.  Only updates the Q-value of the *taken* action
        per sample — other action heads are left unchanged.
        Returns mean squared TD error for logging.
        """
        B      = len(states)
        states = states.astype(np.float32)

        # ─ cached forward ─
        acts, pres = [states], []
        h = states
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = h @ W + b;  pres.append(z)
            h = np.maximum(0, z) if i < len(self.W) - 1 else z
            acts.append(h)
        q_out = acts[-1]          # (B, N_ACTIONS)

        # ─ gradient: only taken action ─
        dL  = np.zeros_like(q_out)
        mse = 0.0
        for k in range(B):
            err              = q_out[k, actions[k]] - td_targets[k]
            dL[k, actions[k]] = 2.0 * err / B
            mse             += err * err
        mse /= B

        # ─ backprop ─
        delta    = dL
        gW, gb   = [], []
        for i in reversed(range(len(self.W))):
            gW.insert(0, acts[i].T @ delta)
            gb.insert(0, delta.sum(0))
            if i > 0:
                delta = (delta @ self.W[i].T) * (pres[i - 1] > 0).astype(np.float32)

        # ─ Adam ─
        self.t += 1
        bc1 = 1 - self.B1 ** self.t
        bc2 = 1 - self.B2 ** self.t
        for i in range(len(self.W)):
            for m, v, g, lst in (
                (self.mW[i], self.vW[i], gW[i], self.W),
                (self.mb[i], self.vb[i], gb[i], self.b),
            ):
                m[:]    = self.B1 * m + (1 - self.B1) * g
                v[:]    = self.B2 * v + (1 - self.B2) * g ** 2
                lst[i] -= self.lr * (m / bc1) / (np.sqrt(v / bc2) + self.AEPS)

        return float(mse)

    # ── utilities ─────────────────────────────────────────────────────────────
    def copy_weights_from(self, other: "DQNetwork"):
        self.W = [w.copy() for w in other.W]
        self.b = [b.copy() for b in other.b]

    def save(self, path: str):
        joblib.dump({
            "W": self.W, "b": self.b, "t": self.t, "lr": self.lr,
            "mW": self.mW, "vW": self.vW, "mb": self.mb, "vb": self.vb,
        }, path, compress=3)

    @classmethod
    def load(cls, path: str) -> "DQNetwork":
        d   = joblib.load(path)
        net = cls(d.get("lr", LR))
        net.W, net.b, net.t = d["W"], d["b"], d.get("t", 0)
        net.mW = d.get("mW", [np.zeros_like(w) for w in net.W])
        net.vW = d.get("vW", [np.zeros_like(w) for w in net.W])
        net.mb = d.get("mb", [np.zeros_like(b) for b in net.b])
        net.vb = d.get("vb", [np.zeros_like(b) for b in net.b])
        return net


# ═════════════════════════════════════════════════════════════════════════════
class ReplayBuffer:
    """
    Fixed-size circular replay buffer with disk persistence.
    Stores (state, action, reward, next_state, done) tuples.
    """

    def __init__(self, maxlen: int = 200_000):
        self.maxlen = maxlen
        self.buf: deque = deque(maxlen=maxlen)

    def push(self, state, action: int, reward: float, next_state, done: bool):
        self.buf.append((
            np.array(state,      dtype=np.float32),
            int(action),
            float(reward),
            np.array(next_state, dtype=np.float32),
            bool(done),
        ))

    def sample(self, n: int):
        n     = min(n, len(self.buf))
        idx   = np.random.choice(len(self.buf), n, replace=False)
        batch = [self.buf[i] for i in idx]
        return (
            np.array([x[0] for x in batch], dtype=np.float32),
            np.array([x[1] for x in batch], dtype=np.int32),
            np.array([x[2] for x in batch], dtype=np.float32),
            np.array([x[3] for x in batch], dtype=np.float32),
            np.array([x[4] for x in batch], dtype=np.float32),
        )

    def __len__(self) -> int: return len(self.buf)

    def save(self, path: str):
        subset = list(self.buf)[-100_000:]    # cap file at 100k most-recent
        joblib.dump(subset, path, compress=3)

    def load(self, path: str):
        if not os.path.exists(path):
            return
        try:
            data     = joblib.load(path)
            self.buf = deque(data, maxlen=self.maxlen)
            print(f"   📦  Loaded {len(self.buf):,} transitions from replay buffer")
        except Exception as e:
            print(f"   ⚠️  Buffer load error: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Standalone progress viewer
# ═════════════════════════════════════════════════════════════════════════════
def _bar(val: float, width: int = 40, fill: str = "█", empty: str = "░") -> str:
    n = int(round(val * width))
    return fill * n + empty * (width - n)


def show_progress():
    """Pretty-print everything the AI has learned so far."""
    print("\n" + "═" * 62)
    print("   🧠  NPC DQN — Training Progress Report")
    print("═" * 62)

    # ── stats ──────────────────────────────────────────────────────────────
    if not os.path.exists(STATS_PATH):
        print("  No training data found yet. Run some battles first!")
        print("═" * 62 + "\n")
        return

    with open(STATS_PATH) as f:
        s = json.load(f)

    battles     = s.get("battles",      0)
    wins        = s.get("wins",         0)
    epsilon     = s.get("epsilon",      EPS_START)
    train_steps = s.get("train_steps",  0)
    avg_loss    = s.get("avg_loss",     0.0)
    history     = s.get("wr_history",   [])   # list of (battle_num, win_rate)
    buf_size    = s.get("buffer_size",  0)
    action_dist = s.get("action_dist",  {})

    losses      = wins
    win_rate    = wins / max(1, battles)

    print(f"  Battles completed : {battles:,}")
    print(f"  Win / Loss        : {wins} W  /  {battles-wins} L")
    print(f"  Win rate          : {win_rate:.1%}  {_bar(win_rate, 30)}")
    print(f"  Epsilon (explore) : {epsilon:.4f}  "
          f"{'[exploring 🎲]' if epsilon > 0.3 else '[exploiting 🎯]'}")
    print(f"  Buffer size       : {buf_size:,} transitions")
    print(f"  Training steps    : {train_steps:,}")
    print(f"  Avg TD loss       : {avg_loss:.5f}")

    # ── model weight norms (proxy for 'how much it has learned') ───────────
    if os.path.exists(Q_NET_PATH):
        try:
            net = DQNetwork.load(Q_NET_PATH)
            norms = [float(np.linalg.norm(w)) for w in net.W]
            print(f"\n  Weight norms (layer magnitudes — grows as it learns):")
            for i, n_ in enumerate(norms):
                print(f"    Layer {i+1}: {n_:8.2f}  {_bar(min(n_/500, 1), 25)}")
            print(f"    Adam step t = {net.t:,}")
        except Exception:
            pass

    # ── action distribution ─────────────────────────────────────────────────
    if action_dist:
        total_acts = sum(action_dist.values()) or 1
        print("\n  What it does most often:")
        labels = {"move": "Attack moves", "switch": "Switches", "other": "Status / other"}
        for k, label in labels.items():
            v = action_dist.get(k, 0)
            print(f"    {label:18s}: {v/total_acts:5.1%}  {_bar(v/total_acts, 25)}")

    # ── win-rate graph ──────────────────────────────────────────────────────
    if len(history) >= 2:
        print("\n  Win rate over time (each point = 10 battles):")
        rows   = 5
        rates  = [r for _, r in history[-40:]]
        w      = len(rates)
        for row in range(rows, -1, -1):
            pct  = row / rows
            line = f"  {pct:4.0%}│"
            for r in rates:
                line += "█" if r >= pct else " "
            print(line + "│")
        print("      └" + "─" * w + "┘")
        print(f"       Battle {history[-min(40,len(history))][0]}{'':>10}→ {battles}")

    # ── milestone advice ────────────────────────────────────────────────────
    print("\n  Status:")
    if battles < 50:
        print("    🌱 Early stage — still filling replay buffer (run more battles)")
    elif battles < 200:
        print("    📈 Learning basic type matchups and switching")
    elif battles < 500:
        print("    🚀 Improving — learning HP management and momentum")
    elif win_rate < 0.55:
        print("    🔄 Plateau — consider running simulated_battle.py for extra training")
    else:
        print("    🏆 Competitive — should challenge experienced players")

    print("═" * 62 + "\n")


if __name__ == "__main__":
    show_progress()
