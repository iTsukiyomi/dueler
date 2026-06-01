import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBattleHistory, BattleEntry } from "../api/stats";
import { BorderBeam } from "../components/ui/BorderBeam";

function BattleCard({ battle }: { battle: BattleEntry }) {
  const [expanded, setExpanded] = useState(false);
  const isWin = battle.result === "win";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className={`rounded-2xl border transition-all duration-300 overflow-hidden relative group ${
        isWin
          ? "bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40"
          : "bg-rose-500/5 border-rose-500/20 hover:border-rose-500/40"
      }`}
    >
      <BorderBeam
        duration={5}
        borderWidth={1.5}
        colorFrom={isWin ? "#10b981" : "#ef4444"}
        colorTo={isWin ? "#34d399" : "#f87171"}
        className="opacity-0 group-hover:opacity-100 transition-opacity duration-300"
      />

      {/* Header Block */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 p-4 text-left cursor-pointer select-none"
      >
        {/* Result Indicator Badge */}
        <div
          className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center text-sm font-black border transition-transform duration-300 group-hover:scale-105 ${
            isWin
              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
              : "bg-rose-500/15 border-rose-500/30 text-rose-400"
          }`}
        >
          {isWin ? "WIN" : "LOSS"}
        </div>

        {/* Rival and Team Data */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            {battle.opponentAvatar ? (
              <img
                src={battle.opponentAvatar}
                alt={battle.opponent}
                className="w-8 h-8 rounded-lg ring-1 ring-border/80 object-cover shrink-0"
              />
            ) : (
              <div className="w-8 h-8 rounded-lg bg-bg-secondary flex items-center justify-center text-sm shrink-0">
                🧢
              </div>
            )}
            <div className="min-w-0">
              <div className="font-bold text-sm text-text-primary truncate">{battle.opponent}</div>
              <div className="text-[10px] text-text-muted mt-0.5 font-bold uppercase tracking-wider">
                {battle.myTeam} vs {battle.opponentTeam}
              </div>
            </div>
          </div>
        </div>

        {/* ELO Changes */}
        <div className="text-right shrink-0">
          <div className={`font-mono text-sm font-black ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
            {isWin ? "+" : ""}{battle.eloChange}
          </div>
          <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">ELO</div>
        </div>

        {/* Toggle Arrow */}
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-text-muted text-xs select-none shrink-0"
        >
          ▼
        </motion.div>
      </button>

      {/* Expanded Match stats */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden bg-bg-secondary/20"
          >
            <div className="px-5 pb-5 pt-3 border-t border-border/30 grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-sm font-mono font-bold text-text-primary">{battle.duration}</div>
                <div className="text-[9px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Duration</div>
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-text-primary">{battle.turns}</div>
                <div className="text-[9px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Turns</div>
              </div>
              <div>
                <div className="text-xs font-semibold text-text-secondary truncate">{battle.timestamp}</div>
                <div className="text-[9px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Timestamp</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function BattleHistorySkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      {/* Header Skeleton */}
      <div className="border-b border-border/30 pb-4 space-y-2">
        <div className="h-8 w-44 bg-bg-card/85 rounded-lg" />
        <div className="h-4 w-60 bg-bg-card/45 rounded-lg" />
      </div>

      {/* Summary grid Skeleton */}
      <div className="grid sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-bg-card/30 border border-border/40 rounded-2xl" />
        ))}
      </div>

      {/* List cards Skeleton */}
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-bg-card/30 border border-border/30 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

export function BattleHistoryPage() {
  const [filter, setFilter] = useState<"all" | "wins" | "losses">("all");
  const [battleType, setBattleType] = useState<"all" | "ranked" | "casual">("all");

  const { data: historyData, isLoading } = useBattleHistory();
  const battles = historyData?.battles || [];

  const filteredBattles = battles.filter((battle) => {
    // Filter by Win/Loss
    if (filter !== "all") {
      const matchResult = filter === "wins" ? "win" : "loss";
      if (battle.result !== matchResult) return false;
    }
    // Filter by type (ranked battles have non-zero elo change, casuals don't)
    if (battleType === "ranked" && battle.eloChange === 0) return false;
    if (battleType === "casual" && battle.eloChange !== 0) return false;

    return true;
  });

  const winCount = battles.filter((b) => b.result === "win").length;
  const lossCount = battles.filter((b) => b.result === "loss").length;

  if (isLoading) {
    return <BattleHistorySkeleton />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 w-full select-none"
    >
      {/* Header */}
      <div className="border-b border-border/30 pb-4">
        <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-wider text-text-primary uppercase">
          Battle History
        </h1>
        <p className="text-xs text-text-muted mt-1 font-medium">Archived logs of competitive guild duels and ELO allocations</p>
      </div>

      {/* Overview summaries */}
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="relative rounded-2xl bg-bg-card/30 border border-border/50 p-5 text-center overflow-hidden">
          <div className="text-2xl font-mono font-bold text-text-primary">{battles.length}</div>
          <div className="text-[9px] uppercase tracking-widest text-text-muted mt-1 font-bold">Total Matches</div>
        </div>
        <div className="relative rounded-2xl bg-emerald-500/5 border border-emerald-500/25 p-5 text-center overflow-hidden">
          <div className="text-2xl font-mono font-bold text-emerald-400">{winCount}</div>
          <div className="text-[9px] uppercase tracking-widest text-emerald-400 mt-1 font-bold">Wins</div>
        </div>
        <div className="relative rounded-2xl bg-rose-500/5 border border-rose-500/25 p-5 text-center overflow-hidden">
          <div className="text-2xl font-mono font-bold text-rose-400">{lossCount}</div>
          <div className="text-[9px] uppercase tracking-widest text-rose-400 mt-1 font-bold">Losses</div>
        </div>
      </div>

      {/* Filters toolbar */}
      <div className="flex flex-wrap gap-3">
        {/* Win/Loss filter */}
        <div className="flex bg-bg-card/30 rounded-xl border border-border/60 overflow-hidden p-0.5">
          {(["all", "wins", "losses"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer ${
                filter === f
                  ? "bg-accent text-bg-primary"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {f === "all" ? "All" : f === "wins" ? "Wins" : "Losses"}
            </button>
          ))}
        </div>

        {/* Ranked/Casual filter */}
        <div className="flex bg-bg-card/30 rounded-xl border border-border/60 overflow-hidden p-0.5">
          {(["all", "ranked", "casual"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setBattleType(t)}
              className={`px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer ${
                battleType === t
                  ? "bg-accent text-bg-primary"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {t === "all" ? "All Types" : t}
            </button>
          ))}
        </div>
      </div>

      {/* List cards */}
      <div className="space-y-3.5">
        <AnimatePresence mode="popLayout">
          {filteredBattles.map((battle) => (
            <BattleCard key={battle.id} battle={battle} />
          ))}
        </AnimatePresence>

        {filteredBattles.length === 0 && (
          <div className="text-center py-16 rounded-2xl bg-bg-card/10 border border-dashed border-border/40">
            <div className="text-4xl mb-3 select-none">⚔️</div>
            <div className="font-display text-sm font-bold text-text-secondary">No recorded duels match filters</div>
            <div className="text-[10px] mt-1 text-text-muted font-semibold uppercase tracking-wider">
              Play matches in Discord to compile log data
            </div>
          </div>
        )}
      </div>

      {/* Pagination hint */}
      {filteredBattles.length > 0 && (
        <div className="text-center text-[10px] text-text-muted font-bold tracking-widest uppercase">
          End of history log file
        </div>
      )}
    </motion.div>
  );
}

export default BattleHistoryPage;