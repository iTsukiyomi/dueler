import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { motion } from "framer-motion";
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
      {/* Mystical Background Grid & Glows */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e1b4b_1px,transparent_1px)] [background-size:24px_24px] opacity-10 pointer-events-none" />
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] rounded-full bg-accent/3 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] rounded-full bg-emerald-500/3 blur-[120px] pointer-events-none" />

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

function LandingPage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const [showConfigTips, setShowConfigTips] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="font-display text-xs uppercase tracking-widest text-text-muted">Loading</span>
        </div>
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
    <div className="min-h-screen flex items-center justify-center bg-bg-primary relative overflow-hidden p-6 font-sans select-none">
      {/* Deep Mystical Atmosphere */}
      <div className="absolute inset-0 bg-[radial-gradient(#2d284e_1px,transparent_1px)] [background-size:32px_32px] opacity-20 pointer-events-none" />
      <div className="absolute top-[-20%] right-[-10%] w-[60vw] h-[60vw] rounded-full bg-accent/5 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[60vw] h-[60vw] rounded-full bg-emerald-500/5 blur-[150px] pointer-events-none" />

      {/* Decorative Corner Notch Lines */}
      <div className="absolute top-10 left-10 w-24 h-24 border-t-2 border-l-2 border-accent/20 rounded-tl-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-24 h-24 border-b-2 border-r-2 border-accent/20 rounded-br-3xl pointer-events-none" />

      {/* Asymmetric Overlapping Layout */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative max-w-5xl w-full grid grid-cols-1 md:grid-cols-12 gap-8 items-center z-10"
      >
        {/* Left Side: Mystic Emblem & Game Details */}
        <div className="md:col-span-7 space-y-6 text-left p-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-bold uppercase tracking-widest">
            🛡️ Ancient Battle Ground
          </div>
          <h1 className="font-display text-4xl md:text-6xl font-black text-text-primary leading-tight tracking-wide">
            FLAME <br />
            <span className="bg-gradient-to-r from-accent via-accent-glow to-amber-500 bg-clip-text text-transparent">
              DUELER
            </span>
          </h1>
          <p className="text-base text-text-secondary max-w-lg leading-relaxed">
            Unleash the ultimate team configuration. Craft perfect statistics, design movesets, and sync directly with the bot databases. Your next tactical match awaits.
          </p>

          <div className="flex gap-4 pt-4 border-t border-border/30 max-w-md">
            <div>
              <div className="text-xl font-display font-bold text-accent">1.4k+</div>
              <div className="text-[10px] uppercase tracking-wider text-text-muted mt-0.5">Forms Tracked</div>
            </div>
            <div className="border-l border-border/30 pl-4">
              <div className="text-xl font-display font-bold text-emerald-400">Realtime</div>
              <div className="text-[10px] uppercase tracking-wider text-text-muted mt-0.5">Database Sync</div>
            </div>
            <div className="border-l border-border/30 pl-4">
              <div className="text-xl font-display font-bold text-amber-500">Fastify V5</div>
              <div className="text-[10px] uppercase tracking-wider text-text-muted mt-0.5">High Performance</div>
            </div>
          </div>
        </div>

        {/* Right Side: Glassmorphic Panel with Discord Button */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="md:col-span-5 relative"
        >
          <div className="absolute inset-0 bg-accent/5 rounded-3xl blur-2xl pointer-events-none" />
          <div className="relative rounded-3xl bg-bg-card/30 border border-border/60 p-8 md:p-10 backdrop-blur-xl shadow-2xl flex flex-col justify-between min-h-[420px] transition-all hover:border-accent/40">
            <div className="space-y-6">
              <div className="flex justify-between items-start">
                <div className="font-display text-xs uppercase tracking-widest text-text-muted">Access Gate</div>
                <span className="text-lg">⚔️</span>
              </div>
              <div className="space-y-2">
                <h2 className="font-display text-2xl font-bold text-text-primary">Authenticate</h2>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Sign in using your Discord account. This connects your profile, wins, losses, ELO rating, and active battle party.
                </p>
              </div>
            </div>

            <div className="space-y-4 mt-8">
              <button
                onClick={handleDiscordLogin}
                aria-label="Connect with Discord"
                className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-sm tracking-widest uppercase transition-all duration-300 hover:shadow-[0_0_20px_rgba(207,162,64,0.3)] hover:scale-[1.01] active:scale-[0.99] cursor-pointer focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-card focus-visible:ring-accent outline-none"
              >
                Connect With Discord
              </button>

              <button
                onClick={() => setShowConfigTips(!showConfigTips)}
                className="w-full text-center text-[10px] text-text-muted hover:text-text-secondary transition-colors underline"
              >
                Getting "Invalid OAuth URL" or configuration errors?
              </button>

              {showConfigTips && (
                <div className="text-[10px] text-left text-amber-500 bg-amber-500/5 border border-amber-500/20 p-3 rounded-lg leading-normal space-y-1">
                  <p><strong>Common Fixes:</strong></p>
                  <ul className="list-disc list-inside space-y-0.5">
                    <li>Confirm that the Client ID in <code>.env</code> matches your Discord Bot's Client ID (or specific OAuth2 app ID).</li>
                    <li>Ensure you have added the Redirect URI <code>http://localhost:3001/api/auth/callback</code> to your application redirects in the Discord Developer Portal and saved changes.</li>
                    <li>If you access the site via <code>127.0.0.1</code> instead of <code>localhost</code>, update the redirects accordingly.</li>
                  </ul>
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-border/30 text-[9px] text-text-muted">
              By authenticating, you authorize secure reading/writing of your trainer party and teams.
            </div>
          </div>
        </motion.div>
      </motion.div>
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
