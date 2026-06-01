import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBattleHistory, BattleEntry } from "../api/stats";

function BattleCard({ battle }: { battle: BattleEntry }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`rounded-2xl border overflow-hidden transition-all duration-300 ${
        battle.result === "win"
          ? "bg-emerald-500/5 border-emerald-500/20"
          : "bg-rose-500/5 border-rose-500/20"
      }`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 p-4 text-left"
      >
        {/* Result indicator */}
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold ${
            battle.result === "win"
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-rose-500/20 text-rose-400"
          }`}
        >
          {battle.result === "win" ? "W" : "L"}
        </div>

        {/* Opponent info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <img
              src={battle.opponentAvatar}
              alt={battle.opponent}
              className="w-8 h-8 rounded-lg ring-2 ring-border"
            />
            <div>
              <div className="font-semibold text-text-primary truncate">{battle.opponent}</div>
              <div className="text-xs text-text-muted">{battle.myTeam} vs {battle.opponentTeam}</div>
            </div>
          </div>
        </div>

        {/* ELO change */}
        <div className="text-right">
          <div className={`font-display font-bold ${
            battle.eloChange > 0 ? "text-emerald-400" : "text-rose-400"
          }`}>
            {battle.eloChange > 0 ? "+" : ""}{battle.eloChange}
          </div>
          <div className="text-[10px] text-text-muted">ELO</div>
        </div>

        {/* Expand icon */}
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-text-muted"
        >
          ▼
        </motion.div>
      </button>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-2 border-t border-border/30 grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-lg font-mono text-text-primary">{battle.duration}</div>
                <div className="text-[10px] uppercase tracking-wider text-text-muted">Duration</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-mono text-text-primary">{battle.turns}</div>
                <div className="text-[10px] uppercase tracking-wider text-text-muted">Turns</div>
              </div>
              <div className="text-center">
                <div className="text-lg text-text-primary">{battle.timestamp}</div>
                <div className="text-[10px] uppercase tracking-wider text-text-muted">When</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function BattleHistoryPage() {
  const [filter, setFilter] = useState<"all" | "wins" | "losses">("all");
  const [battleType, setBattleType] = useState<"all" | "ranked" | "casual">("all");

  const { data: historyData, isLoading } = useBattleHistory();
  const battles = historyData?.battles || [];

  const filteredBattles = battles.filter((battle) => {
    if (filter === "all") return true;
    return battle.result === filter.slice(0, -1); // wins -> win, losses -> loss
  });

  const winCount = battles.filter((b) => b.result === "win").length;
  const lossCount = battles.filter((b) => b.result === "loss").length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 select-none w-full"
    >
      {/* Header */}
      <div className="border-b border-border/40 pb-4">
        <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">Battle History</h1>
        <p className="text-xs text-text-muted mt-1">Your recent battles and results</p>
      </div>

      {/* Stats summary */}
      <div className="grid sm:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl bg-bg-card/40 border border-border/60 p-5 text-center"
        >
          <div className="text-3xl font-display font-bold text-text-primary">{battles.length}</div>
          <div className="text-[10px] uppercase tracking-widest text-text-muted mt-1">Total Battles</div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl bg-emerald-500/10 border border-emerald-500/30 p-5 text-center"
        >
          <div className="text-3xl font-display font-bold text-emerald-400">{winCount}</div>
          <div className="text-[10px] uppercase tracking-widest text-emerald-400 mt-1">Victories</div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl bg-rose-500/10 border border-rose-500/30 p-5 text-center"
        >
          <div className="text-3xl font-display font-bold text-rose-400">{lossCount}</div>
          <div className="text-[10px] uppercase tracking-widest text-rose-400 mt-1">Defeats</div>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex bg-bg-card/40 rounded-xl border border-border/60 overflow-hidden">
          {(["all", "wins", "losses"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-all ${
                filter === f
                  ? "bg-accent text-bg-primary"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {f === "all" ? "All" : f === "wins" ? "Wins" : "Losses"}
            </button>
          ))}
        </div>

        <div className="flex bg-bg-card/40 rounded-xl border border-border/60 overflow-hidden">
          {(["all", "ranked", "casual"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setBattleType(t)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-all ${
                battleType === t
                  ? "bg-accent text-bg-primary"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {t === "all" ? "All Types" : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Battle list */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {filteredBattles.map((battle) => (
            <BattleCard key={battle.id} battle={battle} />
          ))}
        </AnimatePresence>

        {filteredBattles.length === 0 && (
          <div className="text-center py-16 rounded-2xl bg-bg-card/10 border border-dashed border-border/40">
            <div className="text-5xl mb-4">⚔️</div>
            <div className="font-display text-lg font-bold text-text-secondary">No battles found</div>
            <div className="text-xs mt-1 text-text-muted">
              {filter === "all" ? "Start battling to see your history" : `No ${filter} to display`}
            </div>
          </div>
        )}
      </div>

      {/* Load more */}
      {filteredBattles.length > 0 && (
        <div className="text-center">
          <button className="px-8 py-3 rounded-xl bg-bg-card/40 border border-border/60 text-text-muted hover:text-text-primary text-xs font-semibold uppercase tracking-wider transition-all">
            Load More Battles
          </button>
        </div>
      )}
    </motion.div>
  );
}

export default BattleHistoryPage;