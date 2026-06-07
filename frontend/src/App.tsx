import React, { useEffect } from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { SessionNavBar } from '@/components/ui/sidebar';
import LandingPage from '@/pages/LandingPage';
import ProfilePage from '@/pages/ProfilePage';
import TeamListPage from '@/pages/TeamListPage';
import TeamEditorPage from '@/pages/TeamEditorPage';
import ChatPage from '@/pages/ChatPage';
import LeaderboardPage from '@/pages/LeaderboardPage';
import BattleHistoryPage from '@/pages/BattleHistoryPage';
import { NotFoundPage } from '@/components/ui/not-found-page';

// Auth Guard component
function AuthGuard() {
  const { isAuthenticated, isLoading, fetchUser } = useAuthStore();

  useEffect(() => {
    // Only run fetchUser if not authenticated
    fetchUser();
  }, [fetchUser]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-100">
        <div className="relative size-12">
          <div className="absolute inset-0 rounded-full border-4 border-orange-500/20 animate-pulse" />
          <div className="absolute inset-0 rounded-full border-4 border-t-orange-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

// Layout wrapper for dashboard pages
function DashboardLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-row">
      {/* Sidebar Navigation */}
      <SessionNavBar />
      
      {/* Main Content Area */}
      <main className="grow min-w-0 pl-[3.75rem] md:pl-[3.75rem] transition-all duration-300">
        <div className="p-6 md:p-8 min-h-screen flex flex-col">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default function App() {
  const { fetchUser } = useAuthStore();

  useEffect(() => {
    // Try to fetch session at the root level on boot
    fetchUser();
  }, [fetchUser]);

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />

      {/* Protected Dashboard Routes */}
      <Route element={<AuthGuard />}>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<ProfilePage />} />
          <Route path="teams" element={<TeamListPage />} />
          <Route path="teams/:name" element={<TeamEditorPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="leaderboard" element={<LeaderboardPage />} />
          <Route path="battles" element={<BattleHistoryPage />} />
        </Route>
      </Route>

      {/* 404 Route */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
