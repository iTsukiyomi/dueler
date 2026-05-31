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
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
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
    >
      <h1 className="text-2xl font-bold mb-6">Profile</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main card */}
        <div className="lg:col-span-2 rounded-2xl bg-bg-card border border-border p-6">
          <div className="flex items-start gap-5 mb-6">
            <img
              src={user.avatarUrl}
              alt={user.username}
              className="w-24 h-24 rounded-2xl ring-2 ring-accent/30 shadow-lg"
            />
            <div>
              <h2 className="text-xl font-bold">{profile.username}</h2>
              <div className="flex items-center gap-2 mt-2">
                <span className="px-3 py-1 rounded-full bg-accent/20 text-accent font-mono font-bold text-sm">
                  {profile.elo} ELO
                </span>
                {profile.rank && (
                  <span className="px-3 py-1 rounded-full bg-bg-secondary text-text-secondary font-mono text-sm">
                    Rank #{profile.rank}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBox label="Wins" value={profile.wins} color="text-success" />
            <StatBox label="Losses" value={profile.losses} color="text-danger" />
            <StatBox label="Win Rate" value={`${winRate}%`} color="text-warning" />
            <StatBox label="Wallet" value={`₽${profile.wallet.toLocaleString()}`} color="text-text-primary" />
          </div>

          {/* Win rate bar */}
          <div className="mt-6">
            <div className="flex justify-between text-xs text-text-muted mb-1.5">
              <span>Win Rate</span>
              <span>{winRate}%</span>
            </div>
            <div className="h-2 rounded-full bg-bg-secondary overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${winRate}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-accent to-warning"
              />
            </div>
          </div>
        </div>

        {/* Side card */}
        <div className="rounded-2xl bg-bg-card border border-border p-6 flex flex-col gap-4">
          <div>
            <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Active Team</div>
            <div className="text-lg font-semibold capitalize">
              {profile.active_party_name ?? "None"}
            </div>
          </div>
          {profile.active_party_name && (
            <button
              onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(profile.active_party_name!)}`)}
              className="mt-auto px-4 py-2 rounded-xl bg-accent/15 text-accent font-medium text-sm hover:bg-accent/25 transition-colors"
            >
              View Active Team →
            </button>
          )}

          <div className="border-t border-border pt-4">
            <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Theme</div>
            <div className="text-sm capitalize">{profile.theme}</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded-xl bg-bg-secondary p-4 text-center">
      <div className={`text-xl font-bold font-mono ${color}`}>{value}</div>
      <div className="text-xs text-text-muted mt-1">{label}</div>
    </div>
  );
}
