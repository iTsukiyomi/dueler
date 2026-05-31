import { useEffect } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { ProfileCard } from "./components/profile/ProfileCard";
import { TeamList } from "./components/teams/TeamList";
import { TeamEditor } from "./components/teams/TeamEditor";

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary text-text-primary">
        <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen bg-bg-primary">
      {/* Sidebar for desktop */}
      <Sidebar />
      
      {/* Main workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function LandingPage() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleDiscordLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary relative overflow-hidden p-6">
      {/* Graphic background highlights */}
      <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-accent/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none" />

      {/* Login Card */}
      <div className="relative max-w-md w-full rounded-3xl bg-bg-card/40 border border-border/60 p-8 md:p-10 backdrop-blur-xl shadow-2xl text-center space-y-8 animate-float">
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-accent/25 to-emerald-500/25 border border-accent/30 text-3xl mb-2">
            ⚔️
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-text-primary via-emerald-400 to-accent bg-clip-text text-transparent">
            Flame Bot Dueler
          </h1>
          <p className="text-sm text-text-secondary">
            Sync your Pokémon teams with Flame Bot in real-time. Log in via Discord to edit details, customize stats, and prepare for battle.
          </p>
        </div>

        <button
          onClick={handleDiscordLogin}
          className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-[#5865f2] hover:bg-[#4752c4] text-white font-bold text-base shadow-[0_4px_20px_rgba(88,101,242,0.3)] hover:shadow-[0_6px_24px_rgba(88,101,242,0.45)] transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
        >
          <svg
            className="w-6 h-6 fill-current"
            viewBox="0 0 127.14 96.36"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,53.22,6.83,77.19,77.19,0,0,0,49.88,0,105.15,105.15,0,0,0,19.44,8.07C3.66,31.58-1.86,54.65,1,77.53A105.73,105.73,0,0,0,32,96.36a77.7,77.7,0,0,0,6.63-10.85,68.43,68.43,0,0,1-10.5-5c.9-.65,1.76-1.34,2.58-2a75.58,75.58,0,0,0,73,0c.83.68,1.69,1.37,2.58,2a68.43,68.43,0,0,1-10.5,5,77.7,77.7,0,0,0,6.63,10.85,105.73,105.73,0,0,0,31-18.83C129.87,50.31,123.63,27.57,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.83,46,53.83,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.07,46,96.07,53,91,65.69,84.69,65.69Z" />
          </svg>
          Connect with Discord
        </button>

        <div className="text-[10px] text-text-muted">
          By logging in, you authorize accessing your Flame Bot profile and teams data.
        </div>
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
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<ProtectedLayout />}>
        <Route index element={<ProfileCard />} />
        <Route path="teams" element={<TeamList />} />
        <Route path="teams/:name" element={<TeamEditor />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
