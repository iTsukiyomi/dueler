import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import toast from "react-hot-toast";

export function Navbar() {
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Signed out successfully");
    } catch {
      toast.error("Failed to sign out");
    }
  };

  return (
    <nav className="h-16 bg-bg-secondary/20 backdrop-blur-xl border-b border-border/40 flex items-center justify-between px-6 md:px-8 z-30 sticky top-0">
      {/* Mobile logo */}
      <Link to="/dashboard" className="flex items-center gap-3 lg:hidden">
        <motion.span
          whileHover={{ rotate: 15 }}
          className="text-xl"
        >
          🔴
        </motion.span>
        <span className="font-display text-sm font-bold bg-gradient-to-r from-accent to-warning bg-clip-text text-transparent">
          Flame Dueler
        </span>
      </Link>

      <div className="flex-1 lg:flex hidden" />

      {user && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-4"
        >
          {/* Quick actions */}
          <Link
            to="/dashboard/teams"
            className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl bg-accent/10 border border-accent/30 text-accent hover:bg-accent hover:text-bg-primary text-sm font-semibold transition-all duration-200"
          >
            <span>+</span>
            <span>New Team</span>
          </Link>

          {/* Divider */}
          <div className="h-8 w-px bg-border/60 hidden sm:block" />

          {/* User menu */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex flex-col items-end">
              <span className="text-sm font-medium text-text-primary">{user.username}</span>
              <span className="text-[10px] text-text-muted">Trainer</span>
            </div>

            <motion.img
              whileHover={{ scale: 1.05 }}
              src={user.avatarUrl}
              alt={user.username}
              className="w-9 h-9 rounded-xl ring-2 ring-border"
            />
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-bg-card border border-border/60 text-text-muted hover:text-rose-400 hover:border-rose-500/30 text-xs font-medium transition-all"
            title="Sign out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="hidden sm:inline">Logout</span>
          </button>
        </motion.div>
      )}
    </nav>
  );
}