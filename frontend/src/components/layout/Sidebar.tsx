import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Profile", icon: "🧢", end: true },
  { to: "/dashboard/teams", label: "Teams", icon: "🦖" },
  { to: "/dashboard/leaderboard", label: "Leaderboard", icon: "🏆" },
  { to: "/dashboard/battles", label: "Battle History", icon: "📖" },
  { to: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const { user } = useAuthStore();
  const { data: profile } = usePlayerProfile();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
      isActive
        ? "bg-accent/15 text-accent border border-accent/30 shadow-[0_0_12px_rgba(207,162,64,0.15)]"
        : "text-text-secondary hover:text-text-primary hover:bg-bg-card border border-transparent"
    }`;

  return (
    <aside className="w-64 bg-bg-secondary/20 border-r border-border/40 p-6 flex flex-col gap-8 h-screen sticky top-0 hidden lg:flex shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-border/30 pb-4">
        <motion.span
          whileHover={{ rotate: 15 }}
          className="text-2xl"
        >
          🔴
        </motion.span>
        <span className="font-display text-sm font-bold bg-gradient-to-r from-accent to-accent-glow bg-clip-text text-transparent tracking-widest uppercase">
          Flame Dueler
        </span>
      </div>

      {/* User info */}
      {user && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-3 py-3 px-4 bg-bg-card/30 rounded-2xl border border-border/50"
        >
          <motion.img
            whileHover={{ scale: 1.05 }}
            src={user.avatarUrl}
            alt={user.username}
            className="w-16 h-16 rounded-2xl ring-2 ring-accent/40 shadow-lg"
          />
          <div className="text-center">
            <div className="font-bold text-text-primary truncate max-w-[140px]">{user.username}</div>
            {profile && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="flex items-center justify-center gap-2 mt-1.5"
              >
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-accent/20 text-accent font-mono font-semibold">
                  {profile.elo} ELO
                </span>
                {profile.rank && (
                  <span className="text-xs text-text-muted">
                    #{profile.rank}
                  </span>
                )}
              </motion.div>
            )}
          </div>
        </motion.div>
      )}

      {/* Navigation */}
      <nav className="flex flex-col gap-1">
        <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2 px-4">
          Navigation
        </div>
        {navItems.map((item) => (
          <motion.div
            key={item.to}
            whileHover={{ x: 4 }}
            transition={{ duration: 0.15 }}
          >
            <NavLink to={item.to} end={item.end} className={linkClass}>
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
              {item.label === "Leaderboard" && (
                <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded bg-accent/20 text-accent font-semibold">
                  TOP
                </span>
              )}
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Quick stats */}
      <div className="mt-auto space-y-4">
        <div className="p-4 rounded-2xl bg-bg-card/30 border border-border/50">
          <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-3">Battle Record</div>
          {profile ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Victories</span>
                <span className="text-emerald-400 font-mono font-semibold">{profile.wins}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Defeats</span>
                <span className="text-rose-400 font-mono font-semibold">{profile.losses}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-border/30 pt-2 mt-2">
                <span className="text-text-muted">Win Rate</span>
                <span className="text-accent font-mono font-semibold">
                  {profile.wins + profile.losses > 0
                    ? ((profile.wins / (profile.wins + profile.losses)) * 100).toFixed(1)
                    : "0.0"}%
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-text-muted">Loading...</div>
          )}
        </div>

        <div className="text-[10px] text-text-muted text-center">
          <div className="flex items-center justify-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Synced with Discord in real-time
          </div>
        </div>
      </div>
    </aside>
  );
}