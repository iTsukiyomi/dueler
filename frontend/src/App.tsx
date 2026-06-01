import { useEffect } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { LandingPage } from "./pages/LandingPage";
import { ProfilePage } from "./pages/ProfilePage";
import { TeamListPage } from "./pages/TeamListPage";
import { TeamEditorPage } from "./pages/TeamEditorPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { BattleHistoryPage } from "./pages/BattleHistoryPage";
import { SettingsPage } from "./pages/SettingsPage";

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary text-text-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="font-display text-xs uppercase tracking-widest text-text-muted">Loading Session</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen bg-bg-primary font-sans text-text-primary relative overflow-hidden">
      {/* Mystical Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e1b4b_1px,transparent_1px)] [background-size:24px_24px] opacity-10 pointer-events-none" />
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] rounded-full bg-accent/[0.03] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] rounded-full bg-emerald-500/[0.03] blur-[120px] pointer-events-none" />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 border-l border-border/40">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6 md:p-10 max-w-7xl mx-auto w-full relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function App() {
  const fetchUser = useAuthStore((s) => s.fetchUser);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />

      {/* Protected dashboard routes */}
      <Route path="/dashboard" element={<ProtectedLayout />}>
        <Route index element={<ProfilePage />} />
        <Route path="teams" element={<TeamListPage />} />
        <Route path="teams/:name" element={<TeamEditorPage />} />
        <Route path="leaderboard" element={<LeaderboardPage />} />
        <Route path="battles" element={<BattleHistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;