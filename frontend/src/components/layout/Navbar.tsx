import { Link } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export function Navbar() {
  const { user, logout } = useAuthStore();

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-bg-secondary/80 backdrop-blur-xl border-b border-border z-40 flex items-center px-6">
      <Link to="/dashboard" className="flex items-center gap-3 group">
        <span className="text-2xl">⚔️</span>
        <span className="text-lg font-bold bg-gradient-to-r from-accent to-warning bg-clip-text text-transparent">
          Pokemon Dueler
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
