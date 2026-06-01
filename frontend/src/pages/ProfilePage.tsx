import { useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";
import { useBattleHistory } from "../api/stats";
import { useNavigate } from "react-router-dom";

// Animated counter with scroll trigger
function AnimatedStat({ value, label, icon }: { value: string | number; label: string; icon: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="rounded-2xl bg-bg-secondary/40 border border-border/50 p-5 text-center group hover:border-accent/30 transition-all duration-300"
    >
      <div className="text-3xl mb-2">{icon}</div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : {}}
        transition={{ delay: 0.3 }}
        className="font-display text-3xl font-bold text-accent group-hover:text-accent-glow transition-colors"
      >
        {value}
      </motion.div>
      <div className="text-[10px] uppercase tracking-widest text-text-muted font-semibold mt-1">{label}</div>
    </motion.div>
  );
}

// Activity item component
function ActivityItem({ icon, text, time, type }: { icon: string; text: string; time: string; type: "win" | "loss" | "info" }) {
  const colors = {
    win: "text-emerald-400",
    loss: "text-rose-400",
    info: "text-accent",
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 py-3 border-b border-border/30 last:border-0"
    >
      <div className={`text-lg ${colors[type]}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary truncate">{text}</p>
        <p className="text-[10px] text-text-muted mt-0.5">{time}</p>
      </div>
    </motion.div>
  );
}

// Level badge component
function LevelBadge({ level }: { level: number }) {
  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 10 }}
      className="absolute -bottom-1 -right-1 bg-gradient-to-br from-accent to-amber-600 text-bg-primary text-[9px] font-bold px-2 py-0.5 rounded-full font-display shadow-lg"
    >
      LV{level}
    </motion.div>
  );
}

// Rank badge component
function RankBadge({ rank }: { rank: number }) {
  const getRankStyle = (r: number) => {
    if (r === 1) return "from-yellow-400 to-amber-500 bg-gradient-to-br";
    if (r === 2) return "from-gray-300 to-gray-400 bg-gradient-to-br";
    if (r === 3) return "from-amber-600 to-amber-800 bg-gradient-to-br";
    return "";
  };

  return (
    <div className={`w-10 h-10 rounded-xl ${getRankStyle(rank)} bg-bg-card border border-border flex items-center justify-center ${rank <= 3 ? "text-bg-primary" : "text-text-secondary"} font-display font-bold text-sm`}>
      #{rank}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-8 select-none animate-pulse">
      {/* Header Skeleton */}
      <div className="border-b border-border/40 pb-4 flex items-center justify-between">
        <div>
          <div className="h-9 w-48 bg-bg-secondary/60 rounded-lg mb-2" />
          <div className="h-4 w-64 bg-bg-secondary/40 rounded-lg" />
        </div>
        <div className="w-10 h-10 rounded-xl bg-bg-secondary/50 border border-border" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Profile Card Skeleton */}
        <div className="lg:col-span-2 rounded-2xl bg-bg-card/40 border border-border/70 p-6 md:p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/20 to-transparent" />
          
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
            {/* Avatar Skeleton */}
            <div className="w-28 h-28 rounded-2xl bg-bg-secondary/60 border-2 border-border/80 shadow-lg" />
            
            {/* User Info Skeleton */}
            <div className="text-center sm:text-left space-y-3 flex-1">
              <div className="space-y-2">
                <div className="h-8 w-40 bg-bg-secondary/60 rounded-lg mx-auto sm:mx-0" />
                <div className="h-4 w-24 bg-bg-secondary/40 rounded-lg mx-auto sm:mx-0" />
              </div>
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3">
                <div className="h-8 w-24 bg-bg-secondary/50 rounded-xl" />
                <div className="h-8 w-24 bg-bg-secondary/50 rounded-xl" />
              </div>
            </div>
          </div>

          {/* Stats Grid Skeleton */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-2xl bg-bg-secondary/30 border border-border/50 p-5 flex flex-col items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-bg-secondary/50" />
                <div className="h-8 w-16 bg-bg-secondary/60 rounded-lg" />
                <div className="h-3 w-12 bg-bg-secondary/40 rounded-lg" />
              </div>
            ))}
          </div>

          {/* Win Rate Progress Skeleton */}
          <div className="bg-bg-secondary/30 border border-border/30 p-5 rounded-xl space-y-3">
            <div className="flex justify-between">
              <div className="h-3 w-28 bg-bg-secondary/50 rounded-lg" />
              <div className="h-3 w-10 bg-bg-secondary/50 rounded-lg" />
            </div>
            <div className="h-3 rounded-full bg-bg-secondary/40 border border-border/60" />
            <div className="flex justify-between">
              <div className="h-3 w-12 bg-bg-secondary/40 rounded-lg" />
              <div className="h-3 w-12 bg-bg-secondary/40 rounded-lg" />
            </div>
          </div>
        </div>

        {/* Side Panel Skeleton */}
        <div className="space-y-6">
          {/* Active Party Card Skeleton */}
          <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/20 to-transparent" />
            <div className="space-y-4">
              <div>
                <div className="h-3 w-28 bg-bg-secondary/50 rounded-lg mb-2" />
                <div className="h-6 w-36 bg-bg-secondary/60 rounded-lg" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-bg-secondary/30 rounded-xl p-3 flex flex-col items-center gap-1">
                  <div className="h-3 w-10 bg-bg-secondary/40 rounded-lg" />
                  <div className="h-4 w-16 bg-bg-secondary/50 rounded-lg" />
                </div>
                <div className="bg-bg-secondary/30 rounded-xl p-3 flex flex-col items-center gap-1">
                  <div className="h-3 w-10 bg-bg-secondary/40 rounded-lg" />
                  <div className="h-4 w-12 bg-bg-secondary/50 rounded-lg" />
                </div>
              </div>
              <div className="h-11 w-full bg-bg-secondary/50 rounded-xl" />
            </div>
          </div>

          {/* Recent Activity Skeleton */}
          <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="h-3 w-24 bg-bg-secondary/50 rounded-lg" />
              <div className="h-3 w-12 bg-bg-secondary/50 rounded-lg" />
            </div>
            <div className="space-y-3 divide-y divide-border/20">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center gap-3 pt-3 first:pt-0">
                  <div className="w-5 h-5 rounded-full bg-bg-secondary/50 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-full bg-bg-secondary/50 rounded-lg" />
                    <div className="h-3 w-16 bg-bg-secondary/40 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats Skeleton */}
          <div className="rounded-2xl bg-bg-secondary/30 border border-border/40 p-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-bg-secondary/50 flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-24 bg-bg-secondary/50 rounded-lg" />
              <div className="h-3 w-32 bg-bg-secondary/40 rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ProfilePage() {
  const { user } = useAuthStore();
  const { data: profile, isLoading, error, refetch } = usePlayerProfile();
  const navigate = useNavigate();

  if (isLoading) {
    return <ProfileSkeleton />;
  }

  if (error || (!isLoading && !profile)) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] space-y-4 text-center">
        <div className="text-4xl animate-bounce">⚠️</div>
        <h2 className="font-display text-xl font-bold text-text-primary">Failed to load Trainer profile</h2>
        <p className="text-sm text-text-muted max-w-xs">Could not retrieve your data. Please check your connection or try again.</p>
        <button
          onClick={() => refetch()}
          className="px-6 py-2.5 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-widest hover:bg-accent-glow hover:shadow-[0_0_12px_rgba(207,162,64,0.3)] transition-all cursor-pointer"
        >
          Retry Fetch
        </button>
      </div>
    );
  }

  if (!user || !profile) return null;

  const profileWins = profile?.wins ?? 0;
  const profileLosses = profile?.losses ?? 0;
  const profileElo = profile?.elo ?? 1000;
  const profileWallet = profile?.wallet ?? 0;

  const winRate = profileWins + profileLosses > 0
    ? ((profileWins / (profileWins + profileLosses)) * 100).toFixed(1)
    : "0.0";

  const { data: historyData } = useBattleHistory();
  const battles = historyData?.battles || [];

  const recentActivity = battles.slice(0, 4).map((battle) => {
    const isWin = battle.result === "win";
    return {
      icon: "💥",
      text: `${isWin ? "Victory against" : "Defeat by"} ${battle.opponent}`,
      time: battle.timestamp,
      type: isWin ? ("win" as const) : ("loss" as const),
    };
  });

  const eligibleBattles = profileWins + profileLosses >= 10;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 select-none w-full"
    >
      {/* Header */}
      <div className="border-b border-border/40 pb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">Trainer Profile</h1>
          <p className="text-xs text-text-muted mt-1">Your battle statistics and activity</p>
        </div>
        {profile?.rank && <RankBadge rank={profile.rank} />}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 rounded-2xl bg-bg-card/40 border border-border/70 p-6 md:p-8 relative overflow-hidden group"
        >
          {/* Gold accent line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/40 to-transparent" />

          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
            {/* Avatar */}
            <div className="relative">
              <motion.img
                src={user.avatarUrl}
                alt={user.username}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="w-28 h-28 rounded-2xl border-2 border-border/80 shadow-lg object-cover ring-4 ring-bg-secondary"
              />
              <LevelBadge level={100} />

              {/* Online indicator */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.4 }}
                className="absolute -top-1 -left-1 w-5 h-5 bg-emerald-500 rounded-full border-2 border-bg-primary"
              />
            </div>

            {/* User info */}
            <div className="text-center sm:text-left space-y-3 flex-1">
              <div>
                <h2 className="font-display text-2xl font-bold text-text-primary uppercase tracking-wide">
                  {profile?.username}
                </h2>
                <p className="text-sm text-text-muted">Discord Trainer</p>
              </div>

              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3">
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="px-4 py-1.5 rounded-xl bg-accent/15 border border-accent/30 text-accent font-mono font-bold text-base tracking-wide"
                >
                  {profileElo} ELO
                </motion.span>
                {profile?.rank && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="px-4 py-1.5 rounded-xl bg-bg-secondary border border-border/60 text-text-secondary font-mono text-base"
                  >
                    Rank #{profile?.rank}
                  </motion.span>
                )}
                {eligibleBattles && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="px-4 py-1.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-bold uppercase tracking-wider"
                  >
                    Ranked Eligible
                  </motion.span>
                )}
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <AnimatedStat value={profileWins} label="Victories" icon="🏆" />
            <AnimatedStat value={profileLosses} label="Defeats" icon="💀" />
            <AnimatedStat value={`${winRate}%`} label="Win Rate" icon="📈" />
            <AnimatedStat value={`₽${profileWallet.toLocaleString()}`} label="Credits" icon="🪙" />
          </div>

          {/* Win Rate Progress */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="bg-bg-secondary/40 border border-border/30 p-5 rounded-xl"
          >
            <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
              <span>Victory Progress</span>
              <span className="text-accent font-mono">{winRate}%</span>
            </div>
            <div className="h-3 rounded-full bg-bg-primary overflow-hidden border border-border/60">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${winRate}%` }}
                transition={{ duration: 1.2, delay: 0.5, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-accent-soft via-accent to-accent-glow shadow-[0_0_12px_rgba(207,162,64,0.5)]"
              />
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-text-muted">
              <span>{profileWins} wins</span>
              <span>{profileLosses} losses</span>
            </div>
          </motion.div>
        </motion.div>

        {/* Side Panel */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          {/* Active Party Card */}
          <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6 relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/40 to-transparent" />

            <div className="space-y-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-1">Active Battle Party</div>
                <div className="text-xl font-display font-bold capitalize text-text-primary tracking-wide">
                  {profile?.active_party_name ?? "No Team Active"}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-bg-secondary/40 rounded-xl p-3">
                  <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Theme</div>
                  <div className="text-sm font-semibold capitalize">🔮 {profile?.theme}</div>
                </div>
                <div className="bg-bg-secondary/40 rounded-xl p-3">
                  <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Gen</div>
                  <div className="text-sm font-semibold font-mono">Gen {profile?.gen}</div>
                </div>
              </div>

              {profile?.active_party_name && (
                <motion.button
                  onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(profile.active_party_name!)}`)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-3.5 rounded-xl bg-accent/10 border border-accent/25 hover:bg-accent hover:text-bg-primary text-accent font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 cursor-pointer"
                >
                  Manage Team →
                </motion.button>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Recent Activity</div>
              <button className="text-[10px] text-accent hover:text-accent-glow transition-colors">View All</button>
            </div>

            <div className="divide-y divide-border/20">
              {recentActivity.length > 0 ? (
                recentActivity.map((activity, idx) => (
                  <ActivityItem key={idx} {...activity} />
                ))
              ) : (
                <div className="text-xs text-text-muted py-4 text-center">No recent activity</div>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="rounded-2xl bg-gradient-to-br from-accent/10 to-transparent border border-accent/20 p-5">
            <div className="text-[10px] font-bold uppercase tracking-widest text-accent mb-3">Performance Rating</div>
            <div className="flex items-center gap-3">
              <div className="text-4xl font-display font-bold text-accent">
                {parseFloat(winRate) >= 60 ? "S" : parseFloat(winRate) >= 50 ? "A" : parseFloat(winRate) >= 40 ? "B" : "C"}
              </div>
              <div className="flex-1">
                <div className="text-xs text-text-secondary">
                  {parseFloat(winRate) >= 60 ? "Elite Trainer" :
                   parseFloat(winRate) >= 50 ? "Skilled Fighter" :
                   parseFloat(winRate) >= 40 ? "Developing Skill" : "Keep Practicing"}
                </div>
                <div className="text-[10px] text-text-muted mt-0.5">
                  Based on {profileWins + profileLosses} battles
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

// Keep ProfileCard as alias for backwards compatibility
export { ProfilePage as ProfileCard };
export default ProfilePage;