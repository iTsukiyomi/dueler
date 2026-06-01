import { motion } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { useLeaderboard, LeaderboardEntry } from "../api/stats";

function RankMedal({ rank }: { rank: number }) {
  const medals: Record<number, { emoji: string; class: string }> = {
    1: { emoji: "🏆", class: "text-yellow-400" },
    2: { emoji: "⭐", class: "text-gray-300" },
    3: { emoji: "🌟", class: "text-amber-600" },
  };

  if (medals[rank]) {
    return <span className={`text-xl ${medals[rank].class}`}>{medals[rank].emoji}</span>;
  }

  return <span className="w-8 text-center font-mono text-sm text-text-muted">#{rank}</span>;
}

function LeaderboardRow({ entry, index, isCurrentUser }: { entry: LeaderboardEntry; index: number; isCurrentUser: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`flex items-center gap-4 py-4 px-4 rounded-xl transition-all duration-300 ${
        isCurrentUser
          ? "bg-accent/10 border border-accent/30"
          : "hover:bg-bg-card/50 border border-transparent"
      }`}
    >
      <div className="w-10 flex justify-center">
        <RankMedal rank={entry.rank} />
      </div>

      <div className="flex items-center gap-3 flex-1 min-w-0">
        <img
          src={entry.avatarUrl}
          alt={entry.username}
          className="w-10 h-10 rounded-xl ring-2 ring-border object-cover"
        />
        <div className="min-w-0">
          <div className="font-semibold text-text-primary truncate">
            {entry.username}
            {isCurrentUser && <span className="ml-2 text-[10px] text-accent">(You)</span>}
          </div>
        </div>
      </div>

      <div className="text-right">
        <div className="font-display font-bold text-accent">{entry.elo}</div>
        <div className="text-[10px] text-text-muted">ELO</div>
      </div>

      <div className="text-right hidden sm:block">
        <div className="font-mono text-sm text-emerald-400">{entry.wins}W</div>
        <div className="text-[10px] text-text-muted">{entry.winRate}% WR</div>
      </div>
    </motion.div>
  );
}

export function LeaderboardPage() {
  const { data, isLoading } = useLeaderboard(10);
  const leaderboard = data?.leaderboard;

  const { user } = useAuthStore();

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
      className="space-y-6 select-none"
    >
      {/* Header */}
      <div className="border-b border-border/40 pb-4">
        <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">Leaderboard</h1>
        <p className="text-xs text-text-muted mt-1">Top trainers in the battle arena</p>
      </div>

      {/* Top 3 Cards */}
      {leaderboard && leaderboard.length >= 3 && (
        <div className="grid sm:grid-cols-3 gap-4">
          {[1, 0, 2].map((idx) => {
            const entry = leaderboard[idx];
            const isFirst = idx === 1;
            return (
              <motion.div
                key={entry.rank}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`rounded-2xl p-6 relative overflow-hidden ${
                  isFirst
                    ? "bg-gradient-to-br from-accent/20 to-accent/5 border-2 border-accent/50 sm:order-2"
                    : "bg-bg-card/40 border border-border/60"
                }`}
              >
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/50 to-transparent" />

                <div className="text-center relative">
                  <RankMedal rank={entry.rank} />

                  <img
                    src={entry.avatarUrl}
                    alt={entry.username}
                    className={`w-20 h-20 rounded-2xl mx-auto mt-3 ring-4 ${
                      isFirst ? "ring-accent shadow-lg shadow-accent/30" : "ring-border"
                    } object-cover`}
                  />

                  <h3 className="font-display text-lg font-bold text-text-primary mt-3">
                    {entry.username}
                  </h3>

                  <div className="mt-2 space-y-1">
                    <div className="font-display text-2xl font-bold text-accent">{entry.elo}</div>
                    <div className="text-[10px] uppercase tracking-widest text-text-muted">ELO Rating</div>
                  </div>

                  {isFirst && (
                    <div className="absolute -top-2 -right-2 text-4xl">👑</div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Leaderboard List */}
      <div className="rounded-2xl bg-bg-card/30 border border-border/60 overflow-hidden">
        {/* Header row */}
        <div className="flex items-center gap-4 py-3 px-4 border-b border-border/40 text-[10px] uppercase tracking-widest text-text-muted font-semibold">
          <div className="w-10 text-center">Rank</div>
          <div className="flex-1">Trainer</div>
          <div className="text-right">ELO</div>
          <div className="text-right hidden sm:block">Record</div>
        </div>

        {/* List rows */}
        <div className="divide-y divide-border/20">
          {leaderboard?.map((entry, index) => (
            <LeaderboardRow
              key={entry.rank}
              entry={entry}
              index={index}
              isCurrentUser={user?.username === entry.username}
            />
          ))}
        </div>
      </div>

      {/* Pagination hint */}
      <div className="text-center text-xs text-text-muted">
        Showing top 10 trainers • Updates every minute
      </div>
    </motion.div>
  );
}

export default LeaderboardPage;