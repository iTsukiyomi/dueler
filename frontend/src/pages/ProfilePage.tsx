import React from "react";
import { motion } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";
import { useBattleHistory } from "../api/stats";
import { useNavigate } from "react-router-dom";
import { 
  Trophy, 
  Swords, 
  TrendingUp, 
  Coins, 
  User, 
  Sparkles, 
  Layers, 
  AlertTriangle,
  History,
  Edit,
  ArrowUpRight
} from "lucide-react";

function StatWidget({ 
  value, 
  label, 
  icon: Icon, 
  colorClass = "text-text-brand" 
}: { 
  value: string | number; 
  label: string; 
  icon: React.ComponentType<{ className?: string }>; 
  colorClass?: string;
}) {
  return (
    <div className="card p-5 text-center flex flex-col items-center justify-center relative group">
      <div className="w-10 h-10 rounded bg-bg-overlay border border-border-subtle flex items-center justify-center text-text-secondary group-hover:text-poke-yellow group-hover:border-border-default transition-colors mb-3">
        <Icon className="w-5 h-5" />
      </div>
      <div className={`font-mono text-2xl font-bold ${colorClass}`}>
        {value}
      </div>
      <div className="font-rajdhani text-[9px] uppercase tracking-widest text-text-muted mt-1.5 font-bold">
        {label}
      </div>
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-8 animate-pulse w-full">
      <div className="border-b border-border-subtle pb-4 flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-4 w-28 bg-bg-raised rounded" />
          <div className="h-8 w-44 bg-bg-raised rounded" />
        </div>
        <div className="w-12 h-12 rounded bg-bg-raised" />
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          <div className="card p-6 md:p-8 space-y-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded bg-bg-overlay" />
              <div className="space-y-2 flex-1">
                <div className="h-6 w-36 bg-bg-overlay rounded" />
                <div className="h-4 w-24 bg-bg-overlay rounded" />
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-24 bg-bg-overlay rounded border border-border-subtle" />
              ))}
            </div>
          </div>
        </div>
        <div className="lg:col-span-4 space-y-6">
          <div className="h-48 bg-bg-raised rounded border border-border-subtle" />
          <div className="h-64 bg-bg-raised rounded border border-border-subtle" />
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
        <AlertTriangle className="w-12 h-12 text-poke-red animate-bounce" />
        <h2 className="font-rajdhani text-lg font-bold text-text-primary uppercase tracking-wide">
          Sync Status Offline
        </h2>
        <p className="text-xs text-text-secondary max-w-xs leading-relaxed font-sans">
          Could not establish frequency synchronization link with central databases.
        </p>
        <button
          onClick={() => refetch()}
          className="btn-primary mt-2"
        >
          Force Retry link
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8 w-full"
    >
      {/* Page Header (secondary fixed zone skeleton) */}
      <div className="border-b border-border-subtle pb-4 flex items-center justify-between">
        <div>
          <div className="mono text-[10px] text-text-muted uppercase tracking-widest mb-1">
            Terminal / Trainer Card
          </div>
          <h1 className="font-display text-2xl font-bold text-text-primary uppercase tracking-tight">
            Trainer ID Profile
          </h1>
        </div>
        {profile.rank && (
          <div className="w-12 h-12 rounded border border-poke-yellow/30 bg-poke-yellow-glow flex flex-col items-center justify-center">
            <span className="font-rajdhani text-[8px] font-bold text-text-muted uppercase">Rank</span>
            <span className="mono text-sm font-bold text-poke-yellow">#{profile.rank}</span>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-12 gap-6 items-start">
        {/* Main Info Card */}
        <div className="lg:col-span-8 space-y-6">
          <div className="card p-6 md:p-8">
            {/* Profile Hero Block */}
            <div className="flex flex-col sm:flex-row items-center gap-6 mb-8 text-center sm:text-left">
              <div className="relative">
                {user?.avatarUrl ? (
                  <img
                    src={user.avatarUrl}
                    alt={user.username}
                    className="w-20 h-20 rounded object-cover ring-2 ring-border-default border border-bg-void"
                  />
                ) : (
                  <div className="w-20 h-20 rounded bg-bg-overlay border border-border-default flex items-center justify-center text-3xl select-none">
                    <User className="w-10 h-10 text-text-muted" />
                  </div>
                )}
                <div className="absolute -bottom-2 -right-2 px-1.5 py-0.5 rounded bg-poke-red border border-border-brand text-white font-mono text-[9px] uppercase tracking-wider font-bold">
                  LV100
                </div>
              </div>

              <div className="space-y-2 flex-1">
                <div>
                  <h2 className="font-display text-xl font-bold text-text-primary uppercase tracking-wide">
                    {profile.username}
                  </h2>
                  <div className="font-rajdhani text-[10px] text-text-muted uppercase tracking-wider font-bold">
                    League Competitor Registered
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
                  <span className="px-3 py-1 rounded bg-poke-red-glow border border-poke-red/20 text-poke-red font-mono text-xs font-bold">
                    {elo} ELO Rating
                  </span>
                  <span className="px-3 py-1 rounded bg-bg-overlay border border-border-subtle text-text-secondary font-mono text-xs font-bold">
                    ₽{wallet.toLocaleString()} Credits
                  </span>
                </div>
              </div>
            </div>

            {/* Performance Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatWidget value={wins} label="Victories" icon={Trophy} colorClass="text-emerald-400" />
              <StatWidget value={losses} label="Defeats" icon={Swords} colorClass="text-poke-red" />
              <StatWidget value={`${winRate}%`} label="Win Ratio" icon={TrendingUp} colorClass="text-poke-yellow" />
              <StatWidget value={`₽${wallet}`} label="Wallet Bal" icon={Coins} colorClass="text-poke-blue" />
            </div>

            {/* Win Rate Progress Meter */}
            <div className="mt-8 bg-bg-base border border-border-subtle p-5 rounded-lg">
              <div className="flex justify-between text-[9px] font-bold uppercase tracking-widest text-text-muted mb-3 font-rajdhani">
                <span>Battle Victory Ratio Vector</span>
                <span className="text-poke-yellow font-mono font-bold">{winRate}%</span>
              </div>
              <div className="stat-bar-track relative">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${winRate}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="h-full rounded bg-gradient-to-r from-poke-red/70 to-poke-yellow shadow-[0_0_12px_var(--poke-red-glow)]"
                />
              </div>
              <div className="flex justify-between mt-2.5 mono text-[9px] text-text-muted tracking-wide">
                <span>{wins} VICTORIES</span>
                <span>{losses} DEFEATS</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Overview Panel */}
        <div className="lg:col-span-4 space-y-6">
          {/* Active Battle Team */}
          <div className="card p-6">
            <div className="space-y-4">
              <div>
                <div className="mono text-[9px] font-bold uppercase tracking-widest text-text-muted mb-1">
                  Active Battle Squad
                </div>
                <h3 className="text-base font-display font-extrabold capitalize text-text-primary tracking-wide">
                  {profile.active_party_name ?? "No Squad Active"}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-bg-overlay rounded p-3 border border-border-subtle flex flex-col items-center">
                  <span className="mono text-[8px] uppercase tracking-wider text-text-muted mb-1">Theme</span>
                  <div className="text-xs font-bold capitalize text-text-secondary flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-poke-yellow" />
                    <span>{profile.theme}</span>
                  </div>
                </div>
                <div className="bg-bg-overlay rounded p-3 border border-border-subtle flex flex-col items-center">
                  <span className="mono text-[8px] uppercase tracking-wider text-text-muted mb-1">Limit</span>
                  <div className="text-xs font-bold font-mono text-text-secondary flex items-center gap-1">
                    <Layers className="w-3 h-3 text-poke-blue" />
                    <span>Gen {profile.gen}</span>
                  </div>
                </div>
              </div>

              {profile.active_party_name ? (
                <button
                  onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(profile.active_party_name!)}`)}
                  className="btn-primary w-full py-2.5"
                >
                  <Edit className="w-3.5 h-3.5" />
                  <span>Configure Squad Attributes</span>
                </button>
              ) : (
                <button
                  onClick={() => navigate("/dashboard/teams")}
                  className="btn-secondary w-full py-2.5"
                >
                  <span>Build Battle Squad</span>
                </button>
              )}
            </div>
          </div>

          {/* Performance Tier Rating */}
          <div className="card p-5 flex items-center gap-4 border-l-2 border-poke-yellow">
            <div className="w-12 h-12 rounded bg-bg-overlay border border-poke-yellow/30 flex items-center justify-center text-xl font-display font-black text-poke-yellow shadow-[0_0_12px_var(--poke-yellow-glow)] select-none">
              {ratingTier}
            </div>
            <div>
              <div className="font-rajdhani text-[9px] font-bold uppercase tracking-widest text-poke-yellow">
                Performance Rating Index
              </div>
              <div className="text-xs font-bold text-text-primary mt-0.5 uppercase tracking-wide font-rajdhani">
                {ratingTitle}
              </div>
              <div className="mono text-[9px] text-text-muted mt-0.5">
                Computed over {total} active logs
              </div>
            </div>
          </div>

          {/* Recent Activity Mini-Feed */}
          <div className="card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <span className="mono text-[9px] font-bold uppercase tracking-widest text-text-muted">
                Frequency Feed
              </span>
              <button
                onClick={() => navigate("/dashboard/battles")}
                className="font-rajdhani text-[9px] uppercase font-bold text-text-link hover:text-poke-blue transition-colors cursor-pointer flex items-center gap-0.5"
              >
                <span>Logs</span>
                <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-3">
              {recentBattles.length > 0 ? (
                recentBattles.map((battle) => {
                  const isWin = battle.result === "win";
                  return (
                    <div key={battle.id} className="flex items-center justify-between text-xs py-1">
                      <div className="flex items-center gap-2.5 min-w-0">
                        {isWin ? (
                          <Trophy className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                          <Swords className="w-4 h-4 text-poke-red shrink-0" />
                        )}
                        <div className="min-w-0">
                          <div className="font-semibold text-text-primary truncate uppercase font-rajdhani tracking-wide text-xs">
                            {isWin ? "Vict" : "Defe"} vs {battle.opponent}
                          </div>
                          <div className="mono text-[8px] text-text-muted mt-0.5">{battle.timestamp}</div>
                        </div>
                      </div>
                      <span className={`font-mono text-xs font-bold shrink-0 ${isWin ? "text-emerald-400" : "text-poke-red"}`}>
                        {isWin ? "+" : ""}{battle.eloChange} ELO
                      </span>
                    </div>
                  );
                })
              ) : (
                <div className="mono text-[9px] text-text-muted py-2 text-center uppercase">
                  No battle frequency records found
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default ProfilePage;