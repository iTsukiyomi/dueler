import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBattleHistory, BattleEntry } from "../api/stats";
import { 
  Swords, 
  User, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  RotateCcw, 
  Calendar
} from "lucide-react";

function BattleCard({ battle }: { battle: BattleEntry }) {
  const [expanded, setExpanded] = useState(false);
  const isWin = battle.result === "win";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`card p-4 transition-all duration-200 overflow-hidden relative group ${
        isWin
          ? "border-emerald-500/20 hover:border-emerald-500/40 bg-[var(--bg-raised)]/40"
          : "border-[var(--poke-red)]/20 hover:border-[var(--poke-red)]/40 bg-[var(--bg-raised)]/40"
      }`}
    >
      {/* Header Block */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 text-left cursor-pointer select-none bg-transparent border-none p-0 outline-none"
      >
        {/* Result Indicator Badge */}
        <div
          className={`w-14 h-12 rounded-[var(--radius-sm)] flex flex-col items-center justify-center text-[10px] font-black border transition-transform duration-200 group-hover:scale-105 font-rajdhani tracking-wider ${
            isWin
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-[var(--poke-red-dim)]/15 border-[var(--poke-red)]/20 text-[var(--poke-red)]"
          }`}
        >
          {isWin ? "VICT" : "DEFE"}
        </div>

        {/* Rival and Team Data */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            {battle.opponentAvatar ? (
              <img
                src={battle.opponentAvatar}
                alt={battle.opponent}
                className="w-8 h-8 rounded object-cover shrink-0 border border-[var(--border-default)]"
              />
            ) : (
              <div className="w-8 h-8 rounded bg-[var(--bg-overlay)] border border-[var(--border-default)] flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-text-secondary" />
              </div>
            )}
            <div className="min-w-0">
              <div className="font-bold text-xs text-text-primary truncate uppercase font-rajdhani tracking-wider">
                Rival: {battle.opponent}
              </div>
              <div className="text-[10px] text-text-muted mt-0.5 truncate font-mono uppercase">
                {battle.myTeam.replace("-", " ")} vs {battle.opponentTeam.replace("-", " ")}
              </div>
            </div>
          </div>
        </div>

        {/* ELO Changes */}
        <div className="text-right shrink-0">
          <div className={`font-mono text-sm font-bold ${isWin ? "text-emerald-400" : "text-[var(--poke-red)]"}`}>
            {isWin ? "+" : ""}{battle.eloChange}
          </div>
          <div className="font-rajdhani text-[8px] font-bold text-text-muted uppercase tracking-widest">ELO Points</div>
        </div>

        {/* Toggle Arrow */}
        <div className="text-text-muted shrink-0 pl-2">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Match stats */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-1 pb-2 pt-4 border-t border-[var(--border-default)] mt-3 grid grid-cols-3 gap-4 text-center">
              <div className="flex flex-col items-center">
                <Clock className="w-4.5 h-4.5 text-text-muted mb-1" />
                <span className="mono text-xs font-bold text-text-primary">{battle.duration}</span>
                <span className="font-rajdhani text-[8px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Duration</span>
              </div>
              <div className="flex flex-col items-center">
                <RotateCcw className="w-4.5 h-4.5 text-text-muted mb-1" />
                <span className="mono text-xs font-bold text-text-primary">{battle.turns}</span>
                <span className="font-rajdhani text-[8px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Turns</span>
              </div>
              <div className="flex flex-col items-center">
                <Calendar className="w-4.5 h-4.5 text-text-muted mb-1" />
                <span className="mono text-[10px] text-text-secondary truncate max-w-full px-2">{battle.timestamp}</span>
                <span className="font-rajdhani text-[8px] uppercase font-bold tracking-widest text-text-muted mt-0.5">Timestamp</span>
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
      <div className="border-b border-[var(--border-default)] pb-4 space-y-2">
        <div className="h-3 w-28 bg-[var(--bg-raised)] rounded" />
        <div className="h-8 w-44 bg-[var(--bg-raised)] rounded" />
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded" />
        ))}
      </div>

      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded" />
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
    if (filter !== "all") {
      const matchResult = filter === "wins" ? "win" : "loss";
      if (battle.result !== matchResult) return false;
    }
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8 w-full select-none"
    >
      {/* Page Header */}
      <div className="border-b border-[var(--border-default)] pb-4">
        <div className="mono text-[10px] text-text-muted uppercase tracking-widest mb-1">
          Terminal / Battle Logs
        </div>
        <h1 className="font-display text-2xl font-bold text-text-primary uppercase tracking-tight">
          Session History
        </h1>
      </div>

      {/* Overview summaries */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-5 text-center flex flex-col items-center justify-center">
          <div className="mono text-2xl font-bold text-text-primary">{battles.length}</div>
          <div className="font-rajdhani text-[9px] uppercase tracking-widest text-text-muted mt-1 font-bold">Total Logs</div>
        </div>
        <div className="card p-5 text-center flex flex-col items-center justify-center border-l-2 border-emerald-500 bg-emerald-500/[0.02]">
          <div className="mono text-2xl font-bold text-emerald-400">{winCount}</div>
          <div className="font-rajdhani text-[9px] uppercase tracking-widest text-emerald-400 mt-1 font-bold">Victories</div>
        </div>
        <div className="card p-5 text-center flex flex-col items-center justify-center border-l-2 border-[var(--poke-red)] bg-[var(--poke-red-glow)]">
          <div className="mono text-2xl font-bold text-[var(--poke-red)]">{lossCount}</div>
          <div className="font-rajdhani text-[9px] uppercase tracking-widest text-[var(--poke-red)] mt-1 font-bold">Defeats</div>
        </div>
      </div>

      {/* Filters toolbar */}
      <div className="flex flex-wrap gap-4 items-center">
        {/* Win/Loss filter */}
        <div className="flex bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-sm)] p-0.5">
          {(["all", "wins", "losses"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3.5 py-1.5 rounded-[var(--radius-sm)] text-[10px] font-bold uppercase tracking-wider font-rajdhani transition-all cursor-pointer ${
                filter === f
                  ? "bg-[var(--poke-red)] text-white"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {f === "all" ? "All Results" : f === "wins" ? "Wins" : "Losses"}
            </button>
          ))}
        </div>

        {/* Ranked/Casual filter */}
        <div className="flex bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-sm)] p-0.5">
          {(["all", "ranked", "casual"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setBattleType(t)}
              className={`px-3.5 py-1.5 rounded-[var(--radius-sm)] text-[10px] font-bold uppercase tracking-wider font-rajdhani transition-all cursor-pointer ${
                battleType === t
                  ? "bg-[var(--poke-red)] text-white"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {t === "all" ? "All Modes" : t === "ranked" ? "Ranked Arena" : "Casual Arena"}
            </button>
          ))}
        </div>
      </div>

      {/* List cards */}
      <div className="space-y-4">
        <AnimatePresence mode="popLayout">
          {filteredBattles.map((battle) => (
            <BattleCard key={battle.id} battle={battle} />
          ))}
        </AnimatePresence>

        {filteredBattles.length === 0 && (
          <div className="card p-12 text-center flex flex-col items-center justify-center border-dashed">
            <Swords className="w-10 h-10 text-text-muted mb-3" />
            <h3 className="font-display text-sm font-bold text-text-secondary uppercase tracking-wide">
              No History Matches
            </h3>
            <div className="mono text-[9px] mt-1 text-text-muted tracking-widest uppercase">
              Challenge other trainers inside Discord servers to populate log data
            </div>
          </div>
        )}
      </div>

      {/* Pagination hint */}
      {filteredBattles.length > 0 && (
        <div className="text-center mono text-[8px] text-text-muted tracking-widest uppercase pb-4">
          Terminal Frequency Index Complete
        </div>
      )}
    </motion.div>
  );
}

export default BattleHistoryPage;