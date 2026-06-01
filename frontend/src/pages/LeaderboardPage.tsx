import { motion } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { useLeaderboard, LeaderboardEntry } from "../api/stats";
import { BorderBeam } from "../components/ui/BorderBeam";

function RankMedal({ rank }: { rank: number }) {
  const medals: Record<number, { emoji: string; class: string }> = {
    1: { emoji: "🏆", class: "text-yellow-400" },
    2: { emoji: "⭐", class: "text-gray-300" },
    3: { emoji: "🌟", class: "text-amber-600" },
  };

  if (medals[rank]) {
    return <span className={`text-xl ${medals[rank].class} select-none`}>{medals[rank].emoji}</span>;
  }

  return <span className="w-8 text-center font-mono text-xs font-bold text-text-muted">#{rank}</span>;
}

function LeaderboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      {/* Header Skeleton */}
      <div className="border-b border-border/30 pb-4 space-y-2">
        <div className="h-8 w-44 bg-bg-card/85 rounded-lg" />
        <div className="h-4 w-60 bg-bg-card/45 rounded-lg" />
      </div>

      {/* Top 3 Skeleton */}
      <div className="grid sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-48 bg-bg-card/30 border border-border/40 rounded-2xl" />
        ))}
      </div>

      {/* List Skeleton */}
      <div className="rounded-2xl bg-bg-card/20 border border-border/40 p-4 space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-14 bg-bg-card/40 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

function LeaderboardRow({ entry, index, isCurrentUser }: { entry: LeaderboardEntry; index: number; isCurrentUser: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -15 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className={`flex items-center gap-4 py-4 px-4 rounded-xl transition-all duration-300 ${
        isCurrentUser
          ? "bg-accent/15 border border-accent/30 shadow-[0_0_12px_rgba(207,162,64,0.1)]"
          : "hover:bg-bg-card/30 border border-transparent"
      }`}
    >
      <div className="w-10 flex justify-center">
        <RankMedal rank={entry.rank} />
      </div>

      <div className="flex items-center gap-3.5 flex-1 min-w-0">
        {entry.avatarUrl ? (
          <img
            src={entry.avatarUrl}
            alt={entry.username}
            className="w-10 h-10 rounded-xl ring-2 ring-border/80 object-cover"
          />
        ) : (
          <div className="w-10 h-10 rounded-xl bg-bg-secondary flex items-center justify-center text-xl select-none">
            🧢
          </div>
        )}
        <div className="min-w-0">
          <div className="text-sm font-bold text-text-primary truncate flex items-center gap-1.5">
            {entry.username}
            {isCurrentUser && <span className="text-[9px] uppercase font-black text-accent tracking-widest">(You)</span>}
          </div>
        </div>
      </div>

      <div className="text-right">
        <div className="font-mono text-sm font-bold text-accent">{entry.elo}</div>
        <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">ELO</div>
      </div>

      <div className="text-right hidden sm:block w-24">
        <div className="font-mono text-xs font-bold text-emerald-400">{entry.wins}W - {entry.losses}L</div>
        <div className="text-[8px] font-bold text-text-muted uppercase tracking-widest">{entry.winRate}% WR</div>
      </div>
    </motion.div>
  );
}

export function LeaderboardPage() {
  const { data, isLoading } = useLeaderboard(10);
  const leaderboard = data?.leaderboard || [];
  const { user } = useAuthStore();

  if (isLoading) {
    return <LeaderboardSkeleton />;
  }

  // Slice leaderboard to get top 3 safely
  const topThree = leaderboard.slice(0, 3);
  // Sort them so rank 1 is in center [Rank 2, Rank 1, Rank 3]
  const sortedTopThree = [...topThree];
  if (sortedTopThree.length === 3) {
    const temp = sortedTopThree[0];
    sortedTopThree[0] = sortedTopThree[1]; // Rank 2 to left
    sortedTopThree[1] = temp;             // Rank 1 in center
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
          Leaderboard
        </h1>
        <p className="text-xs text-text-muted mt-1 font-medium">Top arena trainers sorted by calculated ELO metrics</p>
      </div>

      {/* Top 3 Podiums */}
      {topThree.length > 0 && (
        <div className="grid sm:grid-cols-3 gap-4 items-end">
          {sortedTopThree.map((entry, idx) => {
            const isRank1 = entry.rank === 1;
            return (
              <motion.div
                key={entry.rank}
                initial={{ opacity: 0, y: 25 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`relative rounded-3xl p-6 overflow-hidden ${
                  isRank1
                    ? "bg-gradient-to-br from-accent/15 to-accent/5 border-2 border-accent/50 sm:order-2 sm:py-10"
                    : "bg-bg-card/25 border border-border/60"
                }`}
              >
                {isRank1 && <BorderBeam duration={5} borderWidth={2} />}

                <div className="text-center relative">
                  <div className="absolute -top-1 left-1/2 -translate-x-1/2">
                    <RankMedal rank={entry.rank} />
                  </div>

                  {entry.avatarUrl ? (
                    <img
                      src={entry.avatarUrl}
                      alt={entry.username}
                      className={`w-16 h-16 rounded-2xl mx-auto mt-6 ring-4 ${
                        isRank1 ? "ring-accent shadow-lg shadow-accent/25" : "ring-border/80"
                      } object-cover`}
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-2xl bg-bg-secondary flex items-center justify-center text-3xl mx-auto mt-6">
                      🧢
                    </div>
                  )}

                  <h3 className="font-display text-base font-bold text-text-primary mt-4 truncate">
                    {entry.username}
                  </h3>

                  <div className="mt-2 space-y-1">
                    <div className="font-mono text-2xl font-black text-accent">{entry.elo}</div>
                    <div className="text-[8px] uppercase font-bold tracking-widest text-text-muted">ELO Rating</div>
                  </div>

                  {isRank1 && (
                    <div className="absolute -top-4 right-0 text-3xl animate-bounce select-none">👑</div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Leaderboard List container */}
      <div className="rounded-3xl bg-bg-card/25 border border-border/70 overflow-hidden">
        {/* Header row */}
        <div className="flex items-center gap-4 py-3 px-5 border-b border-border/30 text-[9px] uppercase tracking-widest text-text-muted font-bold">
          <div className="w-10 text-center">Rank</div>
          <div className="flex-1">Trainer</div>
          <div className="text-right">ELO</div>
          <div className="text-right hidden sm:block w-24">Record</div>
        </div>

        {/* List rows */}
        <div className="divide-y divide-border/20 px-1">
          {leaderboard.map((entry, index) => (
            <LeaderboardRow
              key={entry.rank}
              entry={entry}
              index={index}
              isCurrentUser={user?.username === entry.username}
            />
          ))}
        </div>
      </div>

      {/* Footer message */}
      <div className="text-center text-[10px] text-text-muted font-bold tracking-wider uppercase">
        Leaderboard updates in real-time • Syncs with bot matches
      </div>
    </motion.div>
  );
}

export default LeaderboardPage;