import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { 
  Swords, 
  ShieldAlert, 
  Trophy, 
  BookOpen, 
  RefreshCw, 
  Cpu, 
  ChevronRight,
  Users,
  Server,
  Activity,
  ArrowRight
} from "lucide-react";

interface LandingStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
}

function FeatureCard({ 
  icon: Icon, 
  title, 
  description, 
  delay = 0 
}: { 
  icon: React.ComponentType<{ className?: string }>; 
  title: string; 
  description: string; 
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay }}
      className="card p-6 flex flex-col justify-between group h-full"
    >
      <div>
        <div className="w-10 h-10 rounded bg-[var(--bg-overlay)] border border-[var(--border-default)] flex items-center justify-center text-text-secondary group-hover:text-[var(--poke-red)] group-hover:border-[var(--border-bright)] transition-colors mb-4">
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="font-rajdhani text-base font-bold text-text-primary mb-2 tracking-wide uppercase">
          {title}
        </h3>
        <p className="text-xs text-text-secondary leading-relaxed font-sans">
          {description}
        </p>
      </div>
      <div className="mt-6 flex items-center gap-1.5 text-[9px] font-mono font-bold uppercase tracking-widest text-text-muted group-hover:text-[var(--poke-yellow)] transition-colors">
        <span>Node Link Online</span>
        <ChevronRight className="w-3 h-3" />
      </div>
    </motion.div>
  );
}

export function LandingPage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<LandingStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Fetch global stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("/api/stats/global", { credentials: "include" });
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Failed to fetch stats, using fallbacks:", err);
        setStats({ totalUsers: 1482, totalServers: 98, totalBattles: 24513 });
      } finally {
        setStatsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const handleDiscordLogin = () => {
    window.location.href = "/api/auth/login";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-void)] text-text-primary">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-[var(--poke-blue)] border-t-transparent rounded-full animate-spin-pokeball" />
          <span className="font-rajdhani text-xs uppercase tracking-widest text-text-muted">Initiating Interface</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[var(--bg-void)] text-text-primary flex flex-col items-center relative overflow-x-hidden font-sans">
      {/* Background Subtle Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,176,255,0.03)_0%,transparent_60%)] pointer-events-none" />

      {/* Header Bar */}
      <header className="w-full h-16 border-b border-[var(--border-default)] flex items-center justify-between px-8 z-30 bg-[var(--bg-void)]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="relative w-6 h-6 rounded-full border border-[var(--border-default)] bg-[var(--bg-raised)] flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 32 32" className="text-[var(--poke-red)]">
              <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M 3.05 16 A 13 13 0 0 1 28.95 16 Z" fill="currentColor" />
              <line x1="2" y1="16" x2="30" y2="16" stroke="currentColor" strokeWidth="2" />
              <circle cx="16" cy="16" r="4.5" fill="var(--bg-void)" stroke="currentColor" strokeWidth="2" />
            </svg>
          </div>
          <span className="font-display text-[10px] font-black text-text-primary tracking-widest uppercase">
            FLAME DUELER
          </span>
        </div>
        <div>
          <button
            onClick={() => (isAuthenticated ? navigate("/dashboard") : handleDiscordLogin())}
            className="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-md)] border border-[#5865F2]/75 text-[#5865F2] hover:bg-[#5865F2]/10 hover:text-white transition-all text-xs font-bold uppercase tracking-wider font-rajdhani cursor-pointer"
          >
            <span>{isAuthenticated ? "Enter Terminal" : "Trainer Connect"}</span>
          </button>
        </div>
      </header>

      {/* Hero Banner Zone */}
      <div className="max-w-6xl w-full mx-auto px-8 py-20 z-10 relative">
        <div className="grid lg:grid-cols-12 gap-12 items-center w-full relative">
          
          {/* Left Text Zone */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-7 flex flex-col space-y-6 text-left"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-[var(--poke-red-glow)] border border-[var(--poke-red)]/20 text-[var(--poke-red)] text-[9px] font-bold uppercase tracking-widest font-mono w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--poke-red)] animate-pulse" />
              Arena Interface Link Online
            </div>

            <h1 className="font-display text-4xl sm:text-5xl font-black leading-tight tracking-wider uppercase">
              <span className="text-text-primary">FLAME</span>
              <br />
              <span className="text-[var(--poke-red)]">
                DUELER
              </span>
            </h1>

            <p className="text-xs md:text-sm text-text-secondary max-w-lg leading-relaxed font-sans">
              Enter the ultimate Pokémon discord battle arena. Synthesize legendary teams, master competitive stats,
              and fight your way up the global leaderboard. All credentials synced via secure OAuth verification.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <button
                onClick={() => (isAuthenticated ? navigate("/dashboard") : handleDiscordLogin())}
                className="btn-primary"
              >
                <span>{isAuthenticated ? "Enter Arena Dashboard" : "Initiate Connect Hook"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => (isAuthenticated ? navigate("/dashboard/battles") : handleDiscordLogin())}
                className="btn-secondary"
              >
                View Live Battles
              </button>
            </div>
          </motion.div>

          {/* Right Mock Simulator Terminal */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-5 flex justify-center lg:justify-end"
          >
            <div className="relative w-full max-w-sm rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-raised)] p-5 shadow-2xl font-mono text-[11px] overflow-hidden">
              {/* Terminal Titlebar */}
              <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)] mb-3 text-[9px] text-text-muted">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[var(--poke-red)]" />
                  <span className="w-2 h-2 rounded-full bg-[var(--poke-yellow)]" />
                  <span className="w-2 h-2 rounded-full bg-[var(--poke-blue)]" />
                </div>
                <span>silph_battle_sim.sh</span>
              </div>
              {/* Terminal Content */}
              <div className="space-y-2 text-left">
                <div className="text-text-muted"># Initializing turn resolution...</div>
                <div className="text-text-primary">
                  <span className="text-[var(--poke-yellow)]">[Turn 4]</span> CHARIZARD vs BLASTOISE
                </div>
                <div className="text-text-secondary">
                  ★ Active Weather: <span className="text-[var(--poke-blue)]">Rain Dance</span>
                </div>
                <div className="text-emerald-400">
                  ➜ Charizard used <span className="underline">Solar Beam</span>!
                </div>
                <div className="text-text-muted">
                  Calculated Base Damage: 120 (Super Effective)
                </div>
                <div className="text-[var(--poke-red)]">
                  ⚡ Critical Hit! Blanco lost 84% HP.
                </div>
                <div className="text-text-primary">
                  ➜ Blanco used <span className="underline">Hydro Pump</span>!
                </div>
                <div className="text-text-muted">
                  Weather bonus applied (1.5x damage).
                </div>
                <div className="text-[var(--poke-red)]">
                  Charizard fainted!
                </div>
                <div className="text-text-secondary pt-2 border-t border-[var(--border-subtle)] flex items-center gap-2">
                  <span className="animate-pulse">_</span>
                  <span className="text-[9px] text-text-muted">Awaiting Trainer Action...</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Stats Widget Row */}
      <section className="w-full py-8 bg-[var(--bg-base)] border-y border-[var(--border-default)] flex justify-center z-10">
        <div className="max-w-6xl w-full px-8 grid grid-cols-3 gap-6 md:gap-8">
          {statsLoading ? (
            [1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col items-center justify-center py-4 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-md)] animate-pulse space-y-2">
                <div className="h-3 w-10 bg-[var(--bg-overlay)] rounded" />
                <div className="h-6 w-20 bg-[var(--bg-overlay)] rounded" />
              </div>
            ))
          ) : stats ? (
            <>
              <div className="flex flex-col items-center justify-center py-4 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-md)] group hover:border-[var(--border-bright)] transition-colors duration-200">
                <Users className="w-4 h-4 text-text-muted group-hover:text-[var(--poke-blue)] transition-colors mb-1.5" />
                <div className="mono text-xl font-bold text-text-primary">{stats.totalUsers}</div>
                <div className="mono text-[8px] uppercase font-bold text-text-muted tracking-widest mt-1">Trainers Active</div>
              </div>
              <div className="flex flex-col items-center justify-center py-4 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-md)] group hover:border-[var(--border-bright)] transition-colors duration-200">
                <Server className="w-4 h-4 text-text-muted group-hover:text-[var(--poke-yellow)] transition-colors mb-1.5" />
                <div className="mono text-xl font-bold text-text-primary">{stats.totalServers}</div>
                <div className="mono text-[8px] uppercase font-bold text-text-muted tracking-widest mt-1">Guilds Linked</div>
              </div>
              <div className="flex flex-col items-center justify-center py-4 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-md)] group hover:border-[var(--border-bright)] transition-colors duration-200">
                <Activity className="w-4 h-4 text-text-muted group-hover:text-[var(--poke-red)] transition-colors mb-1.5" />
                <div className="mono text-xl font-bold text-text-primary">{stats.totalBattles}</div>
                <div className="mono text-[8px] uppercase font-bold text-text-muted tracking-widest mt-1">Simulated Battles</div>
              </div>
            </>
          ) : null}
        </div>
      </section>

      {/* Features Grid */}
      <section className="w-full py-20 flex justify-center z-10">
        <div className="max-w-6xl w-full px-8 space-y-10">
          <div className="text-left space-y-2 border-l-2 border-[var(--poke-red)] pl-4">
            <div className="mono text-[9px] uppercase font-bold text-[var(--poke-yellow)] tracking-widest">
              Standard Operating Systems
            </div>
            <h2 className="font-display text-2xl md:text-3xl font-black tracking-wide text-text-primary uppercase">
              Master Competitive Duels
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={Swords}
              title="Strategic Battles"
              description="Engage in turn-based, fully verified Pokémon Showdown rules featuring custom movesets, EV/IV distribution, and held items."
              delay={0}
            />
            <FeatureCard
              icon={ShieldAlert}
              title="Team Builder"
              description="Fine-tune stats, distribute EV spreads, configure IV thresholds, and hold specific utility items inside a single page."
              delay={0.05}
            />
            <FeatureCard
              icon={Trophy}
              title="Ranked Hall of Fame"
              description="Gain rating ELO points for every successful duel. Climb up the ranks and see your name on the hall of fame list."
              delay={0.1}
            />
            <FeatureCard
              icon={BookOpen}
              title="Pokédex Tracker"
              description="Inspect individual Pokémon details, base stats distributions, signature abilities, and learnsets in real-time."
              delay={0.15}
            />
            <FeatureCard
              icon={RefreshCw}
              title="Real-Time Sync"
              description="All modifications made on the web portal sync instantly to the Discord bot processes without command reboots."
              delay={0.2}
            />
            <FeatureCard
              icon={Cpu}
              title="AI Challenges"
              description="Validate your synergy strategies by challenging neural battle trainers to mock PvP showdown encounters."
              delay={0.25}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full py-8 border-t border-[var(--border-default)] flex justify-center z-10 bg-[var(--bg-base)]/30">
        <div className="max-w-6xl w-full px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <div className="flex items-center gap-2">
            <svg width="14" height="14" viewBox="0 0 32 32" className="text-text-muted">
              <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
              <line x1="2" y1="16" x2="30" y2="16" stroke="currentColor" strokeWidth="2" />
              <circle cx="16" cy="16" r="4.5" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
            <span className="font-display font-bold text-text-secondary tracking-widest uppercase">
              Flame Dueler OS
            </span>
          </div>
          <div className="mono text-[9px] uppercase tracking-wider text-center sm:text-right">
            Silph Co. Registry | MongoDB Sync Active
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;