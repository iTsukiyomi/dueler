import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";
import { BorderBeam } from "../ui/BorderBeam";

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
    `flex items-center gap-3.5 px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
      isActive
        ? "bg-accent/15 text-accent border border-accent/25 shadow-[0_0_15px_rgba(207,162,64,0.1)]"
        : "text-text-secondary hover:text-text-primary hover:bg-bg-card/40 border border-transparent"
    }`;

  const wins = profile?.wins ?? 0;
  const losses = profile?.losses ?? 0;
  const total = wins + losses;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";

  return (
    <aside className="w-64 bg-bg-secondary/15 border-r border-border/40 p-6 flex flex-col gap-8 h-screen sticky top-0 hidden lg:flex shrink-0 backdrop-blur-lg select-none z-20">
      {/* Brand Header */}
      <div className="flex items-center gap-3 border-b border-border/30 pb-4">
        <motion.span
          whileHover={{ rotate: 360 }}
          transition={{ duration: 0.5 }}
          className="text-2xl cursor-default select-none"
        >
          🔴
        </motion.span>
        <span className="font-display text-sm font-extrabold bg-gradient-to-r from-accent to-accent-glow bg-clip-text text-transparent tracking-widest uppercase cursor-default">
          Flame Dueler
        </span>
      </div>

      {/* Profile summary banner */}
      {user && (
        <div className="relative flex flex-col items-center gap-3 py-4 px-4 bg-bg-card/25 rounded-2xl border border-border/50 overflow-hidden group">
          <BorderBeam duration={8} borderWidth={1} className="opacity-40 group-hover:opacity-100 transition-opacity" />
          {user.avatarUrl ? (
            <img
              src={user.avatarUrl}
              alt={user.username}
              className="w-14 h-14 rounded-xl object-cover ring-2 ring-accent/30 shadow-md transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="w-14 h-14 rounded-xl bg-bg-secondary flex items-center justify-center text-2xl">
              🧢
            </div>
          )}
          <div className="text-center w-full min-w-0">
            <div className="font-bold text-sm text-text-primary truncate">{user.username}</div>
            {profile && (
              <div className="flex items-center justify-center gap-2 mt-1.5">
                <span className="text-[10px] font-mono font-bold bg-accent/15 border border-accent/20 px-2 py-0.5 rounded text-accent">
                  {profile.elo} ELO
                </span>
                {profile.rank && (
                  <span className="text-[10px] text-text-muted font-bold">
                    #{profile.rank}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation bar */}
      <nav className="flex flex-col gap-1.5">
        <div className="text-[9px] font-bold uppercase tracking-widest text-text-muted mb-2 px-4">
          Navigation
        </div>
        {navItems.map((item) => (
          <motion.div
            key={item.to}
            whileHover={{ x: 3 }}
            transition={{ duration: 0.15 }}
          >
            <NavLink to={item.to} end={item.end} className={linkClass}>
              <span className="text-lg select-none">{item.icon}</span>
              <span>{item.label}</span>
              {item.label === "Leaderboard" && (
                <span className="ml-auto text-[8px] font-black px-1.5 py-0.5 rounded bg-accent/20 text-accent">
                  TOP
                </span>
              )}
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Hollow stats card */}
      <div className="mt-auto space-y-4">
        <div className="p-4 rounded-2xl bg-bg-card/20 border border-border/40 space-y-3">
          <div className="text-[9px] font-bold uppercase tracking-widest text-text-muted">Record Card</div>
          <div className="space-y-1.5 text-xs font-semibold">
            <div className="flex justify-between">
              <span className="text-text-muted">WINS</span>
              <span className="text-emerald-400 font-mono font-bold">{wins}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">LOSSES</span>
              <span className="text-rose-400 font-mono font-bold">{losses}</span>
            </div>
            <div className="flex justify-between border-t border-border/20 pt-2 mt-2">
              <span className="text-text-muted">WINRATE</span>
              <span className="text-accent font-mono font-bold">{winRate}%</span>
            </div>
          </div>
        </div>

        <div className="text-[9px] text-text-muted font-bold text-center">
          <div className="flex items-center justify-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Arena Database Active
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;