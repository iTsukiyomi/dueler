import React from "react";
import { motion } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { useLeaderboard, LeaderboardEntry } from "../api/stats";
import { 
  Award, 
  Crown, 
  User, 
  HelpCircle,
  TrendingUp,
  ShieldCheck,
  ChevronRight
} from "lucide-react";

function RankMedal({ rank }: { rank: number }) {
  if (rank === 1) {
    return <Award className="w-5 h-5 text-poke-yellow" />;
  }
  if (rank === 2) {
    return <Award className="w-5 h-5 text-text-secondary" />;
  }
  if (rank === 3) {
    return <Award className="w-5 h-5 text-amber-600" />;
  }
  return <span className="mono text-[11px] font-bold text-text-muted">#{rank}</span>;
}

function LeaderboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      <div className="border-b border-border-subtle pb-4 space-y-2">
        <div className="h-3 w-28 bg-bg-raised rounded" />
        <div className="h-8 w-44 bg-bg-raised rounded" />
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-48 bg-bg-raised border border-border-subtle rounded" />
        ))}
      </div>

      <div className="h-48 bg-bg-raised border border-border-subtle rounded" />
    </div>
  );
}

export function LeaderboardPage() {
  const { data, isLoading } = useLeaderboard(10);
  const leaderboard = data?.leaderboard || [];
  const { user } = useAuthStore();

  if (isLoading) {
    return <LeaderboardSkeleton />;
  }

  const topThree = leaderboard.slice(0, 3);
  const sortedTopThree = [...topThree];
  if (sortedTopThree.length === 3) {
    const temp = sortedTopThree[0];
    sortedTopThree[0] = sortedTopThree[1]; // Rank 2 to left
    sortedTopThree[1] = temp;             // Rank 1 in center
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8 w-full select-none"
    >
      {/* Page Header */}
      <div className="border-b border-border-subtle pb-4">
        <div className="mono text-[10px] text-text-muted uppercase tracking-widest mb-1">
          Terminal / Hall of Fame
        </div>
        <h1 className="font-display text-2xl font-bold text-text-primary uppercase tracking-tight">
          League Standings
        </h1>
      </div>

      {/* Top 3 Podiums */}
      {topThree.length > 0 && (
        <div className="grid sm:grid-cols-3 gap-6 items-end">
          {sortedTopThree.map((entry, idx) => {
            const isRank1 = entry.rank === 1;
            return (
              <motion.div
                key={entry.rank}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08 }}
                className={`card p-6 flex flex-col justify-between ${
                  isRank1
                    ? "border-poke-yellow bg-bg-float sm:py-8 shadow-[0_0_24px_var(--poke-yellow-glow)] sm:order-2"
                    : "sm:order-1"
                }`}
              >
                <div className="text-center relative">
                  <div className="flex justify-center mb-2">
                    <RankMedal rank={entry.rank} />
                  </div>

                  {entry.avatarUrl ? (
                    <img
                      src={entry.avatarUrl}
                      alt={entry.username}
                      className={`w-14 h-14 rounded mx-auto mt-2 object-cover ${
                        isRank1 ? "ring-2 ring-poke-yellow" : "ring-1 ring-border-default"
                      }`}
                    />
                  ) : (
                    <div className="w-14 h-14 rounded bg-bg-overlay border border-border-subtle flex items-center justify-center mx-auto mt-2">
                      <User className="w-7 h-7 text-text-muted" />
                    </div>
                  )}

                  <h3 className="font-rajdhani text-sm font-bold text-text-primary mt-4 truncate uppercase tracking-wider">
                    {entry.username}
                  </h3>

                  <div className="mt-3 space-y-1">
                    <div className="mono text-2xl font-bold text-poke-yellow">{entry.elo}</div>
                    <div className="font-rajdhani text-[8px] uppercase font-bold tracking-widest text-text-muted">ELO Rating</div>
                  </div>

                  {isRank1 && (
                    <div className="absolute -top-3 right-0 text-poke-yellow animate-bounce">
                      <Crown className="w-5 h-5" />
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Leaderboard List container using pokedex-table */}
      <div className="overflow-x-auto">
        <table className="pokedex-table">
          <thead>
            <tr>
              <th className="w-16 text-center">Rank</th>
              <th>Trainer</th>
              <th className="text-right">ELO</th>
              <th className="text-right hidden sm:table-cell">Battles</th>
              <th className="text-right hidden sm:table-cell">Win Rate</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((entry, index) => {
              const isCurrentUser = user?.username === entry.username;
              return (
                <tr 
                  key={entry.rank}
                  className={isCurrentUser ? "bg-poke-yellow-glow" : ""}
                >
                  <td className="text-center">
                    <div className="flex justify-center items-center">
                      <RankMedal rank={entry.rank} />
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-3">
                      {entry.avatarUrl ? (
                        <img
                          src={entry.avatarUrl}
                          alt=""
                          className="w-8 h-8 rounded object-cover"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded bg-bg-overlay border border-border-subtle flex items-center justify-center">
                          <User className="w-4 h-4 text-text-muted" />
                        </div>
                      )}
                      <span className="font-rajdhani font-bold uppercase tracking-wide text-xs">
                        {entry.username}
                        {isCurrentUser && (
                          <span className="ml-2 font-mono text-[8px] text-poke-yellow uppercase font-bold">
                            [Self]
                          </span>
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="text-right mono font-bold text-poke-yellow">
                    {entry.elo}
                  </td>
                  <td className="text-right hidden sm:table-cell mono text-xs text-text-secondary">
                    {entry.wins}W - {entry.losses}L
                  </td>
                  <td className="text-right hidden sm:table-cell mono text-xs text-text-secondary">
                    {entry.winRate}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer message */}
      <div className="text-center mono text-[8px] text-text-muted tracking-widest uppercase">
        Silph Database Registry active • Updates on battle session close
      </div>
    </motion.div>
  );
}

export default LeaderboardPage;