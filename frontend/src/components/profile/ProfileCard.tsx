import { motion } from "framer-motion";
import { usePlayerProfile } from "../../hooks/usePokemonData";
import { useAuthStore } from "../../stores/authStore";
import { useNavigate } from "react-router-dom";

export function ProfileCard() {
  const { user } = useAuthStore();
  const { data: profile, isLoading } = usePlayerProfile();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="border-b border-border/40 pb-3 flex justify-between">
          <div className="h-8 w-48 bg-bg-secondary/40 rounded-xl" />
          <div className="h-4 w-24 bg-bg-secondary/40 rounded-md" />
        </div>
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 rounded-2xl bg-bg-card/40 border border-border/70 p-6 md:p-8 h-96" />
          <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6 h-96" />
        </div>
      </div>
    );
  }

  if (!profile || !user) return null;

  const winRate = profile.wins + profile.losses > 0
    ? ((profile.wins / (profile.wins + profile.losses)) * 100).toFixed(1)
    : "0.0";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 select-none"
    >
      {/* Title */}
      <div className="border-b border-border/40 pb-3 flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">
          Trainer Card
        </h1>
        <div className="text-[10px] uppercase font-bold tracking-widest text-accent">
          Rank Status
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Card */}
        <div className="lg:col-span-2 rounded-2xl bg-bg-card/40 border border-border/70 p-6 md:p-8 backdrop-blur-md relative overflow-hidden group hover:border-accent/30 transition-all duration-300">
          {/* Subtle gold line highlights at the top */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
          
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
            <div className="relative">
              <img
                src={user.avatarUrl}
                alt={user.username}
                className="w-24 h-24 rounded-2xl border-2 border-border/80 shadow-lg object-cover ring-4 ring-bg-secondary"
              />
              <div className="absolute -bottom-2 -right-2 bg-accent text-bg-primary text-[10px] font-bold px-2 py-0.5 rounded-full font-display">
                LV100
              </div>
            </div>
            
            <div className="text-center sm:text-left space-y-2">
              <h2 className="font-display text-2xl font-bold text-text-primary uppercase tracking-wide">
                {profile.username}
              </h2>
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3">
                <span className="px-3 py-1 rounded bg-accent/10 border border-accent/30 text-accent font-mono font-bold text-sm tracking-wide">
                  {profile.elo} ELO
                </span>
                {profile.rank && (
                  <span className="px-3 py-1 rounded bg-bg-secondary border border-border/60 text-text-secondary font-mono text-sm">
                    Rank #{profile.rank}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBox label="Wins" value={profile.wins} color="text-emerald-400" />
            <StatBox label="Losses" value={profile.losses} color="text-rose-400" />
            <StatBox label="Win Ratio" value={`${winRate}%`} color="text-accent" />
            <StatBox label="Wallet" value={`₽${profile.wallet.toLocaleString()}`} color="text-text-primary" />
          </div>

          {/* Win Rate Progress Bar */}
          <div className="mt-8 bg-bg-secondary/40 border border-border/30 p-4 rounded-xl">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2">
              <span>Victory Ratio</span>
              <span className="text-text-primary font-mono">{winRate}%</span>
            </div>
            <div className="h-2 rounded-full bg-bg-primary overflow-hidden border border-border/60">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${winRate}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-accent-soft to-accent shadow-[0_0_8px_rgba(207,162,64,0.4)]"
              />
            </div>
          </div>
        </div>

        {/* Side Card: Active Status */}
        <div className="rounded-2xl bg-bg-card/40 border border-border/70 p-6 backdrop-blur-md flex flex-col justify-between relative overflow-hidden group hover:border-accent/30 transition-all duration-300">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
          
          <div className="space-y-6">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2">Active Battle Party</div>
              <div className="text-xl font-display font-bold capitalize text-text-primary tracking-wide">
                {profile.active_party_name ?? "No Active Team"}
              </div>
            </div>

            <div className="border-t border-border/40 pt-4">
              <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2">Visual Theme</div>
              <div className="text-sm font-semibold capitalize text-text-secondary">
                🔮 {profile.theme}
              </div>
            </div>

            <div className="border-t border-border/40 pt-4">
              <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2">Supported Gen</div>
              <div className="text-sm font-semibold text-text-secondary font-mono">
                Generation {profile.gen}
              </div>
            </div>
          </div>

          {profile.active_party_name && (
            <button
              onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(profile.active_party_name!)}`)}
              className="mt-8 w-full py-3.5 rounded-xl bg-accent/10 border border-accent/25 hover:bg-accent hover:text-bg-primary text-accent font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 hover:shadow-[0_0_12px_rgba(207,162,64,0.2)] active:scale-[0.98] cursor-pointer"
            >
              View Active Party →
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface StatBoxProps {
  label: string;
  value: string | number;
  color: string;
}

function StatBox({ label, value, color }: StatBoxProps) {
  return (
    <div className="rounded-xl bg-bg-secondary/40 border border-border/40 p-4 text-center transition-colors group-hover:border-border/60">
      <div className={`text-2xl font-bold font-mono tracking-wide ${color}`}>
        {value}
      </div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-muted mt-1">
        {label}
      </div>
    </div>
  );
}
