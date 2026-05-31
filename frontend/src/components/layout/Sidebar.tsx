import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";

export function Sidebar() {
  const { user } = useAuthStore();
  const { data: profile } = usePlayerProfile();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
      isActive
        ? "bg-accent/15 text-accent border border-accent/30"
        : "text-text-secondary hover:text-text-primary hover:bg-bg-card"
    }`;

  return (
    <aside className="w-64 bg-bg-secondary/20 border-r border-border/40 p-6 flex flex-col gap-8 h-screen sticky top-0 hidden lg:flex shrink-0">
      <div className="flex items-center gap-3 border-b border-border/30 pb-4">
        <span className="text-xl">🛡️</span>
        <span className="font-display text-base font-bold bg-gradient-to-r from-accent to-accent-glow bg-clip-text text-transparent tracking-widest uppercase">
          Flame Dueler
        </span>
      </div>
      {user && (
        <div className="flex flex-col items-center gap-3 py-2">
          <img
            src={user.avatarUrl}
            alt={user.username}
            className="w-20 h-20 rounded-2xl ring-2 ring-accent/40 shadow-lg"
          />
          <div className="text-center">
            <div className="font-bold text-text-primary">{user.username}</div>
            {profile && (
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent font-mono font-semibold">
                  {profile.elo} ELO
                </span>
                {profile.rank && (
                  <span className="text-xs text-text-muted">
                    #{profile.rank}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <nav className="flex flex-col gap-1">
        <NavLink to="/dashboard" end className={linkClass}>
          <span>📊</span>
          <span>Profile</span>
        </NavLink>
        <NavLink to="/dashboard/teams" className={linkClass}>
          <span>⚔️</span>
          <span>Teams</span>
        </NavLink>
      </nav>

      <div className="mt-auto pt-4 border-t border-border">
        <div className="text-[10px] text-text-muted text-center">
          Synced with Discord bot in real time
        </div>
      </div>
    </aside>
  );
}
