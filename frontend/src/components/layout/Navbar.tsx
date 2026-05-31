import { Link } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export function Navbar() {
  const { user, logout } = useAuthStore();

  return (
    <nav className="h-16 bg-bg-secondary/20 backdrop-blur-xl border-b border-border/40 flex items-center justify-between px-6 md:px-8 z-30">
      <Link to="/dashboard" className="flex items-center gap-3 group lg:hidden">
        <span className="text-xl">⚔️</span>
        <span className="font-display text-sm font-bold bg-gradient-to-r from-accent to-warning bg-clip-text text-transparent">
          Flame Dueler
        </span>
      </Link>

      <div className="flex-1" />

      {user && (
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <img
              src={user.avatarUrl}
              alt={user.username}
              className="w-8 h-8 rounded-full ring-2 ring-border"
            />
            <span className="text-sm font-medium text-text-secondary hidden sm:inline">
              {user.username}
            </span>
          </div>
          <button
            onClick={logout}
            className="text-xs px-3 py-1.5 rounded-lg bg-bg-card border border-border text-text-muted hover:text-text-primary hover:border-accent transition-all"
          >
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}
