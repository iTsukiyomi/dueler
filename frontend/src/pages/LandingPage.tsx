import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { NeonButton } from '@/components/ui/neon-button';
import { PixelTrail } from '@/components/ui/pixel-trail';
import { GooeyFilter } from '@/components/ui/gooey-filter';
import { apiFetch } from '@/api/client';
import { Swords, Users, ShieldAlert } from 'lucide-react';
import { Navigate } from 'react-router-dom';

interface GlobalStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
}

export default function LandingPage() {
  const { isAuthenticated, login, isLoading } = useAuthStore();
  const [stats, setStats] = useState<GlobalStats | null>(null);

  useEffect(() => {
    apiFetch<GlobalStats>('/api/stats/global')
      .then(res => {
        if (res.totalUsers) setStats(res);
      })
      .catch(err => console.error('Failed to fetch stats', err));
  }, []);

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

  // Redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-hidden flex flex-col justify-between select-none">
      {/* Gooey & Pixel trail background */}
      <div className="absolute inset-0 pointer-events-none z-0 opacity-40">
        <PixelTrail
          pixelSize={30}
          fadeDuration={800}
          delay={50}
          className="bg-transparent"
          pixelClassName="bg-gradient-to-r from-red-500/30 to-orange-500/30 rounded-full blur-[4px]"
        />
        <GooeyFilter id="bg-gooey" strength={15} />
      </div>

      {/* Decorative Grid and Ambient Glows */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(244,63,94,0.08),transparent_50%)] pointer-events-none z-0" />
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="size-9 rounded-lg bg-gradient-to-br from-red-500 via-orange-500 to-yellow-500 flex items-center justify-center font-bold text-white shadow-lg shadow-orange-500/20">
            P
          </div>
          <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400 text-lg tracking-wider uppercase font-sans">
            Darkmew
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-semibold text-slate-400 uppercase tracking-widest">
          <span>v2.4-Beta</span>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-grow flex flex-col items-center justify-center px-6 text-center max-w-4xl mx-auto py-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-orange-500/25 bg-orange-950/20 text-orange-400 text-xs font-semibold uppercase tracking-wider mb-6 animate-pulse">
          <ShieldAlert className="size-3.5" />
          Darkmew PvP Arena
        </div>
        
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold font-sans tracking-tight mb-6 leading-tight">
          Battle Your Friends on{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-orange-500 to-yellow-400">
            Discord
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 font-medium max-w-2xl mb-10 leading-relaxed">
          Form custom teams, manage movesets, import from Showdown, and engage in real-time tactical battles using our state-of-the-art Discord bot.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <NeonButton
            onClick={login}
            variant="solid"
            size="lg"
            className="w-full sm:w-auto bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-500 hover:to-orange-400 font-bold tracking-wide text-sm shadow-xl shadow-orange-600/20 transition duration-300 py-3.5 px-10 rounded-xl"
            neon={true}
          >
            Connect Discord Account
          </NeonButton>
        </div>

        {/* Global Statistics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-3xl mt-6">
          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 text-center flex flex-col items-center shadow-lg transition duration-300 hover:border-slate-700/80">
            <Users className="size-6 text-orange-500 mb-3" />
            <span className="text-3xl font-extrabold text-slate-100 mb-1">
              {stats ? stats.totalUsers.toLocaleString() : '---'}
            </span>
            <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
              Active Trainers
            </span>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 text-center flex flex-col items-center shadow-lg transition duration-300 hover:border-slate-700/80">
            <Swords className="size-6 text-red-500 mb-3" />
            <span className="text-3xl font-extrabold text-slate-100 mb-1">
              {stats ? stats.totalBattles.toLocaleString() : '---'}
            </span>
            <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
              Battles Fought
            </span>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 text-center flex flex-col items-center shadow-lg transition duration-300 hover:border-slate-700/80">
            <svg
              className="size-6 text-yellow-500 mb-3 fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.894.077.077 0 0 1-.008-.128c.126-.093.252-.19.372-.287a.075.075 0 0 1 .077-.011c3.92 1.793 8.18 1.793 12.061 0a.073.073 0 0 1 .078.009c.12.099.246.195.373.289a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.156 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.156 2.418z" />
            </svg>
            <span className="text-3xl font-extrabold text-slate-100 mb-1">
              {stats ? stats.totalServers.toLocaleString() : '---'}
            </span>
            <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
              Discord Servers
            </span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 border-t border-slate-900/60 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-slate-500 font-semibold uppercase tracking-wider">
        <span>© {new Date().getFullYear()} Darkmew. All rights reserved.</span>
        <span>Not affiliated with Nintendo or The Pokémon Company.</span>
      </footer>
    </div>
  );
}
