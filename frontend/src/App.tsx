import React, { Component, ErrorInfo, ReactNode, useEffect } from "react";
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

import { ShieldAlert } from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[var(--bg-void)] p-6 text-center text-text-primary">
          <div className="mb-4">
            <ShieldAlert className="w-12 h-12 text-[var(--poke-red)]" />
          </div>
          <h1 className="font-display text-xl font-bold text-text-primary mb-2 uppercase tracking-wider">
            Trainer Terminal Crash
          </h1>
          <p className="text-xs text-text-secondary max-w-md mb-6 leading-relaxed font-sans">
            The Pokédex encountered an unexpected anomaly. Check the logs or reload the terminal interface.
          </p>
          <pre className="text-xs font-mono bg-[var(--bg-input)] p-4 rounded-lg border border-[var(--border-default)] text-[var(--poke-red)] max-w-xl overflow-auto mb-6 text-left w-full">
            {this.state.error?.stack || this.state.error?.message}
          </pre>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.href = "/";
            }}
            className="btn-primary"
          >
            Reboot Terminal
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

import { PokeBallLoader } from "./components/pokemon/PokeBallLoader";

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-void text-text-primary">
        <div className="flex flex-col items-center gap-4">
          <PokeBallLoader size={48} />
          <span className="font-rajdhani text-xs uppercase tracking-widest text-text-muted">Syncing Silph OS Link</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen w-full bg-bg-void font-sans text-text-primary relative overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Workspace with offset for fixed Navbar and Sidebar */}
      <div className="flex-1 flex flex-col min-w-0 w-full ml-[240px] md:ml-[240px] max-md:ml-[48px] mt-[64px]">
        <Navbar />
        <main className="flex-grow p-8 md:p-10 max-w-[1280px] w-full mx-auto relative">
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
    <ErrorBoundary>
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
    </ErrorBoundary>
  );
}

export default App;