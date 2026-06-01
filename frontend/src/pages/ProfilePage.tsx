import { useEffect } from "react";
import { motion } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";
import { useBattleHistory } from "../api/stats";
import { useNavigate } from "react-router-dom";
import { BorderBeam } from "../components/ui/BorderBeam";

function StatCard({ value, label, icon, delay = 0 }: { value: string | number; label: string; icon: string; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay }}
      className="relative rounded-2xl bg-bg-card/40 border border-border/50 p-5 text-center group hover:border-accent/40 transition-all duration-300 overflow-hidden"
    >
      <BorderBeam duration={4} borderWidth={1.2} className="opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="text-3xl mb-2 select-none">{icon}</div>
      <div className="font-mono text-2xl font-extrabold text-accent group-hover:text-accent-glow transition-colors">
        {value}
      </div>
      <div className="text-[9px] uppercase tracking-widest text-text-muted font-bold mt-1.5">{label}</div>
    </motion.div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-8 animate-pulse w-full">
      {/* Header Skeleton */}
      <div className="border-b border-border/30 pb-4 flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-8 w-44 bg-bg-card/80 rounded-lg" />
          <div className="h-4 w-56 bg-bg-card/45 rounded-lg" />
        </div>
        <div className="w-10 h-10 rounded-xl bg-bg-card/60" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Main Card Skeleton */}
          <div className="rounded-2xl bg-bg-card/30 border border-border/50 p-6 md:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="w-24 h-24 rounded-2xl bg-bg-card/80" />
              <div className="space-y-2 flex-1 text-center sm:text-left">
                <div className="h-6 w-36 bg-bg-card/80 rounded-md mx-auto sm:mx-0" />
                <div className="h-4 w-24 bg-bg-card/45 rounded-md mx-auto sm:mx-0" />
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-24 bg-bg-card/30 border border-border/30 rounded-xl" />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Panel Skeleton */}
        <div className="space-y-6">
          <div className="h-48 bg-bg-card/30 border border-border/50 rounded-2xl" />
          <div className="h-64 bg-bg-card/30 border border-border/50 rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

export function ProfilePage() {
  const { user } = useAuthStore();
  const { data: profile, isLoading, error, refetch } = usePlayerProfile();
  const { data: historyData, isLoading: historyLoading } = useBattleHistory();
  const navigate = useNavigate();

  if (isLoading || historyLoading) {
    return <ProfileSkeleton />;
  }

  if (error || !profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 text-center">
        <div className="text-4xl animate-bounce">⚠️</div>
        <h2 className="font-display text-lg font-bold text-text-primary">Failed to sync Trainer Data</h2>
        <p className="text-xs text-text-secondary max-w-xs leading-relaxed">Could not load profile statistics from server databases.</p>
        <button
          onClick={() => refetch()}
          className="px-5 py-2 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-widest hover:bg-accent-glow transition-all cursor-pointer"
        >
          Force Retry
        </button>
      </div>
    );
  }

  const wins = profile.wins ?? 0;
  const losses = profile.losses ?? 0;
  const total = wins + losses;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";
  const elo = profile.elo ?? 1000;
  const wallet = profile.wallet ?? 0;

  const battles = historyData?.battles || [];
  const recentBattles = battles.slice(0, 4);

  // Performance Rating tier
  const ratingTier = parseFloat(winRate) >= 65 ? "S" : parseFloat(winRate) >= 50 ? "A" : parseFloat(winRate) >= 40 ? "B" : "C";
  const ratingTitle = parseFloat(winRate) >= 65 ? "Elite Master" : parseFloat(winRate) >= 50 ? "Expert Dueler" : parseFloat(winRate) >= 40 ? "Challenger" : "Apprentice";

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 w-full"
    >
      {/* Page Header */}
      <div className="border-b border-border/30 pb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-wider text-text-primary uppercase">
            Trainer ID Card
          </h1>
          <p className="text-xs text-text-muted mt-1 font-medium">Verify your registered bot battle attributes and league ratings</p>
        </div>
        {profile.rank && (
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/10 border border-accent/40 flex flex-col items-center justify-center">
            <span className="text-[9px] uppercase font-bold text-text-muted">Rank</span>
            <span className="font-mono text-sm font-black text-accent">#{profile.rank}</span>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-12 gap-6 items-start">
        {/* Main Info Card */}
        <div className="lg:col-span-8 space-y-6">
          <div className="relative rounded-3xl bg-bg-card/30 border border-border/70 p-6 md:p-8 overflow-hidden group">
            <BorderBeam duration={8} borderWidth={1.5} />

            {/* Profile Hero Block */}
            <div className="flex flex-col sm:flex-row items-center gap-6 mb-8 text-center sm:text-left">
              <div className="relative">
                {user?.avatarUrl ? (
                  <img
                    src={user.avatarUrl}
                    alt={user.username}
                    className="w-24 h-24 rounded-2xl object-cover ring-4 ring-bg-secondary border border-border/50"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-2xl bg-bg-secondary flex items-center justify-center text-4xl select-none">
                    🧢
                  </div>
                )}
                <div className="absolute -bottom-2 -right-2 px-2 py-0.5 rounded bg-accent text-bg-primary font-display font-black text-[9px] uppercase tracking-widest shadow-md">
                  LV100
                </div>
              </div>

              <div className="space-y-2 flex-1">
                <div>
                  <h2 className="font-display text-2xl font-bold text-text-primary tracking-wide">
                    {profile.username}
                  </h2>
                  <div className="text-xs text-text-muted font-medium mt-0.5">League Competitor</div>
                </div>

                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                  <span className="px-3 py-1 rounded-lg bg-accent/15 border border-accent/30 text-accent font-mono text-xs font-bold">
                    {elo} ELO
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-bg-secondary border border-border/60 text-text-secondary font-mono text-xs font-semibold">
                    ₽{wallet.toLocaleString()} Credits
                  </span>
                </div>
              </div>
            </div>

            {/* Performance Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatCard value={wins} label="Victories" icon="🏆" delay={0.05} />
              <StatCard value={losses} label="Defeats" icon="💀" delay={0.1} />
              <StatCard value={`${winRate}%`} label="Win Rate" icon="📈" delay={0.15} />
              <StatCard value={`₽${wallet}`} label="Wallet" icon="🪙" delay={0.2} />
            </div>

            {/* Win Rate Progress Meter */}
            <div className="mt-8 bg-bg-secondary/40 border border-border/30 p-5 rounded-2xl">
              <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-text-muted mb-3">
                <span>Battle Victory Ratio</span>
                <span className="text-accent font-mono font-bold">{winRate}%</span>
              </div>
              <div className="h-3 rounded-full bg-bg-primary overflow-hidden border border-border/60 relative">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${winRate}%` }}
                  transition={{ duration: 1.0, ease: "easeOut" }}
                  className="h-full rounded-full bg-gradient-to-r from-accent/70 to-accent shadow-[0_0_12px_rgba(207,162,64,0.3)]"
                />
              </div>
              <div className="flex justify-between mt-2.5 text-[9px] font-bold text-text-muted tracking-wide">
                <span>{wins} WINS</span>
                <span>{losses} LOSSES</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Overview Panel */}
        <div className="lg:col-span-4 space-y-6">
          {/* Active Battle Team */}
          <div className="relative rounded-3xl bg-bg-card/30 border border-border/70 p-6 overflow-hidden group">
            <BorderBeam duration={6} borderWidth={1.5} />
            <div className="space-y-4">
              <div>
                <div className="text-[9px] font-bold uppercase tracking-widest text-text-muted mb-1">Active Squad</div>
                <h3 className="text-lg font-display font-extrabold capitalize text-text-primary tracking-wide">
                  {profile.active_party_name ?? "No Squad Active"}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-bg-secondary/40 rounded-xl p-3 border border-border/20">
                  <div className="text-[9px] uppercase tracking-wider text-text-muted mb-1 font-bold">Theme</div>
                  <div className="text-xs font-bold capitalize text-text-secondary">🔮 {profile.theme}</div>
                </div>
                <div className="bg-bg-secondary/40 rounded-xl p-3 border border-border/20">
                  <div className="text-[9px] uppercase tracking-wider text-text-muted mb-1 font-bold">Limit</div>
                  <div className="text-xs font-bold font-mono text-text-secondary">Gen {profile.gen}</div>
                </div>
              </div>

              {profile.active_party_name && (
                <button
                  onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(profile.active_party_name!)}`)}
                  className="w-full py-3 rounded-xl bg-accent/10 border border-accent/20 hover:bg-accent hover:text-bg-primary text-accent font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 cursor-pointer"
                >
                  Manage Squad Attributes
                </button>
              )}
            </div>
          </div>

          {/* Performance Tier Rating */}
          <div className="rounded-3xl bg-gradient-to-br from-accent/15 to-transparent border border-accent/35 p-5 flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-bg-card border-2 border-accent flex items-center justify-center text-3xl font-display font-black text-accent shadow-[0_0_15px_rgba(207,162,64,0.2)] select-none">
              {ratingTier}
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-accent">Performance Tier</div>
              <div className="text-sm font-bold text-text-primary mt-0.5">{ratingTitle}</div>
              <div className="text-[9px] text-text-muted mt-0.5 font-medium">Ranked over {total} completed duels</div>
            </div>
          </div>

          {/* Recent Activity Mini-Feed */}
          <div className="rounded-3xl bg-bg-card/20 border border-border/50 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border/20 pb-3">
              <span className="text-[9px] font-bold uppercase tracking-widest text-text-muted">Recent Activity</span>
              <button
                onClick={() => navigate("/dashboard/battles")}
                className="text-[9px] uppercase font-bold text-accent hover:text-accent-glow transition-colors cursor-pointer"
              >
                Log Info
              </button>
            </div>

            <div className="space-y-3">
              {recentBattles.length > 0 ? (
                recentBattles.map((battle) => {
                  const isWin = battle.result === "win";
                  return (
                    <div key={battle.id} className="flex items-center justify-between text-xs py-1">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className="text-base select-none">{isWin ? "🏆" : "💀"}</span>
                        <div className="min-w-0">
                          <div className="font-semibold text-text-primary truncate">
                            {isWin ? "Beat" : "Lost to"} {battle.opponent}
                          </div>
                          <div className="text-[9px] text-text-muted mt-0.5 font-medium">{battle.timestamp}</div>
                        </div>
                      </div>
                      <span className={`font-mono font-bold shrink-0 ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
                        {isWin ? "+" : ""}{battle.eloChange} ELO
                      </span>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-text-muted py-2 text-center font-medium">No recent battles log found</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default ProfilePage;