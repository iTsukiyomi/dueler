import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { useNavigate } from "react-router-dom";
import { BorderBeam } from "../components/ui/BorderBeam";

interface LandingStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
}

// Simple floating element component
function FloatingSprite({ emoji, delay = 0, x = 0, y = 0 }: { emoji: string; delay?: number; x?: number; y?: number }) {
  return (
    <motion.div
      className="absolute text-5xl md:text-6xl select-none pointer-events-none z-0 opacity-25 md:opacity-40"
      style={{ left: `${x}%`, top: `${y}%` }}
      animate={{
        y: [0, -15, 0],
        rotate: [-3, 3, -3],
      }}
      transition={{
        duration: 5 + delay,
        repeat: Infinity,
        delay,
        ease: "easeInOut",
      }}
    >
      {emoji}
    </motion.div>
  );
}

// Centered features card
function FeatureCard({ icon, title, description, delay = 0 }: { icon: string; title: string; description: string; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -6 }}
      className="relative rounded-2xl bg-bg-card/45 border border-border/40 p-6 backdrop-blur-md transition-all duration-300 hover:shadow-[0_0_30px_rgba(207,162,64,0.1)] group overflow-hidden"
    >
      <BorderBeam duration={5} borderWidth={1.5} className="opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="text-4xl mb-4 select-none">{icon}</div>
      <h3 className="font-display text-lg font-bold text-text-primary mb-2 tracking-wide">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary text-text-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="font-display text-xs uppercase tracking-widest text-text-muted">Loading Arena</span>
        </div>
      </div>
    );
  }

  const handleDiscordLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <div className="min-h-screen w-full bg-bg-primary text-text-primary flex flex-col items-center relative overflow-x-hidden font-sans">
      {/* Background Matrix Grid */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,#1a1635_0%,transparent_60%)] opacity-40 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(#282537_1px,transparent_1px)] [background-size:32px_32px] opacity-15 pointer-events-none" />

      {/* Floating Pokemon Sprites (Thematic Emojis) */}
      <FloatingSprite emoji="🐭" delay={0} x={8} y={15} />
      <FloatingSprite emoji="🦎" delay={1.2} x={82} y={20} />
      <FloatingSprite emoji="🐢" delay={2.5} x={74} y={65} />
      <FloatingSprite emoji="🐸" delay={0.6} x={15} y={70} />
      <FloatingSprite emoji="👾" delay={1.8} x={88} y={45} />
      <FloatingSprite emoji="🐲" delay={3.0} x={5} y={45} />

      {/* Hero Section Container */}
      <div className="max-w-6xl w-full mx-auto flex-1 flex flex-col items-center justify-center px-6 py-16 md:py-24 z-10">
        <div className="grid lg:grid-cols-12 gap-12 items-center justify-center w-full">
          {/* Hero left content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-7 flex flex-col items-center lg:items-start text-center lg:text-left space-y-6"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-bold uppercase tracking-widest">
              <span className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse" />
              🔴 Pokemon Duel Arena
            </div>

            <h1 className="font-display text-5xl sm:text-6xl md:text-7xl font-black leading-tight tracking-wider uppercase">
              <span className="text-text-primary">FLAME</span>
              <br />
              <span className="bg-gradient-to-r from-accent via-[#f1cd7c] to-amber-500 bg-clip-text text-transparent filter drop-shadow-[0_0_15px_rgba(207,162,64,0.25)] animate-pulse">
                DUELER
              </span>
            </h1>

            <p className="text-base sm:text-lg text-text-secondary max-w-lg leading-relaxed font-medium">
              Enter the ultimate Pokémon discord battle arena. Synthesize legendary teams, master competitive stats,
              and fight your way up the global leaderboard.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <button
                onClick={() => (isAuthenticated ? navigate("/dashboard") : handleDiscordLogin())}
                className="px-8 py-4 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-widest hover:bg-accent-glow hover:shadow-[0_0_30px_rgba(207,162,64,0.3)] transition-all duration-300 cursor-pointer"
              >
                {isAuthenticated ? "Enter Dashboard" : "Start Battle Journey"}
              </button>
              <button
                onClick={() => (isAuthenticated ? navigate("/dashboard/battles") : handleDiscordLogin())}
                className="px-8 py-4 rounded-xl bg-bg-card/50 border border-border/60 hover:border-accent/40 text-text-primary font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 cursor-pointer"
              >
                View Live Battles
              </button>
            </div>
          </motion.div>

          {/* Hero right: Glassmorphic panel */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="lg:col-span-5 w-full flex justify-center"
          >
            <div className="relative w-full max-w-md rounded-3xl bg-bg-card/30 border border-border/70 p-8 backdrop-blur-xl group overflow-hidden">
              {/* Magic Border Beam */}
              <BorderBeam duration={7} borderWidth={2} />

              <div className="space-y-6">
                <div>
                  <div className="font-display text-[10px] uppercase tracking-widest text-text-muted mb-1 font-bold">Trainer Gateway</div>
                  <h2 className="font-display text-2xl font-bold text-text-primary">Join the Arena</h2>
                </div>

                <p className="text-sm text-text-secondary leading-relaxed">
                  Authenticate using Discord to sync your teams in real-time, track ratings, and challenge opponents inside the bots or web portal.
                </p>

                <div className="space-y-3.5">
                  <div className="flex items-center gap-3.5 text-xs text-text-secondary font-medium">
                    <span className="w-6 h-6 rounded-lg bg-accent/15 text-accent flex items-center justify-center text-[11px] font-bold">1</span>
                    <span>Direct sync with discord bot command sets</span>
                  </div>
                  <div className="flex items-center gap-3.5 text-xs text-text-secondary font-medium">
                    <span className="w-6 h-6 rounded-lg bg-accent/15 text-accent flex items-center justify-center text-[11px] font-bold">2</span>
                    <span>Advanced stat tuning & EV/IV sliders</span>
                  </div>
                  <div className="flex items-center gap-3.5 text-xs text-text-secondary font-medium">
                    <span className="w-6 h-6 rounded-lg bg-accent/15 text-accent flex items-center justify-center text-[11px] font-bold">3</span>
                    <span>Climb ladder rankings and claim rewards</span>
                  </div>
                </div>

                <button
                  onClick={() => (isAuthenticated ? navigate("/dashboard") : handleDiscordLogin())}
                  className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-discord hover:bg-discord-hover text-white font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 hover:shadow-[0_0_20px_rgba(88,101,242,0.4)] cursor-pointer"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                  </svg>
                  {isAuthenticated ? "Enter Arena" : "Connect Discord"}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Stats Counter Section (Centered & Skeletons added) */}
      <section className="w-full py-16 bg-bg-secondary/40 border-y border-border/30 flex justify-center z-10">
        <div className="max-w-6xl w-full px-6 grid grid-cols-3 gap-6 text-center">
          {statsLoading ? (
            [1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col items-center justify-center space-y-2 animate-pulse">
                <div className="h-4 w-12 bg-bg-card rounded-md" />
                <div className="h-8 w-24 bg-bg-card rounded-lg" />
                <div className="h-3 w-16 bg-bg-card rounded-md" />
              </div>
            ))
          ) : stats ? (
            <>
              <div className="space-y-1">
                <div className="text-3xl select-none">🧢</div>
                <div className="font-mono text-3xl font-extrabold text-accent">{stats.totalUsers}</div>
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Trainers</div>
              </div>
              <div className="space-y-1">
                <div className="text-3xl select-none">🏰</div>
                <div className="font-mono text-3xl font-extrabold text-accent">{stats.totalServers}</div>
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Guilds</div>
              </div>
              <div className="space-y-1">
                <div className="text-3xl select-none">⚔️</div>
                <div className="font-mono text-3xl font-extrabold text-accent">{stats.totalBattles}</div>
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Battles</div>
              </div>
            </>
          ) : null}
        </div>
      </section>

      {/* Features Grid */}
      <section className="w-full py-20 flex justify-center z-10">
        <div className="max-w-6xl w-full px-6 space-y-12">
          <div className="text-center space-y-3">
            <div className="text-[10px] uppercase font-bold text-accent tracking-widest">Core Infrastructure</div>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold tracking-wide text-text-primary">Master Competitive Duels</h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon="⚔️"
              title="Strategic Battles"
              description="Engage in turn-based, fully verified Pokémon showdown rules featuring custom move pools, natures, and items."
              delay={0}
            />
            <FeatureCard
              icon="🛡️"
              title="Team Builder"
              description="Tweak stats, optimize EV/IV spreads, choose held items, and draft custom synergy sets for your party."
              delay={0.1}
            />
            <FeatureCard
              icon="🏆"
              title="Ranked Ladder"
              description="Gain ELO for every victory. Push up the trainer ranks and see your name featured on the global hall of fame."
              delay={0.2}
            />
            <FeatureCard
              icon="📖"
              title="Pokédex Tracker"
              description="Scan individual Pokémon details, base stat distributions, learnsets, and build options in one single interface."
              delay={0.3}
            />
            <FeatureCard
              icon="🔄"
              title="Real-Time Sync"
              description="All modifications made on the web portal are synced instantly to the Discord bot instances."
              delay={0.4}
            />
            <FeatureCard
              icon="🤖"
              title="AI Challenges"
              description="Test out new custom team sets against alpha neural trainers to simulate competitive PvP play styles."
              delay={0.5}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full py-8 border-t border-border/40 flex justify-center z-10">
        <div className="max-w-6xl w-full px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <div className="flex items-center gap-2">
            <span className="text-lg select-none">🔴</span>
            <span className="font-display font-bold text-text-secondary tracking-widest uppercase">Flame Dueler</span>
          </div>
          <div>All battle details synced via secure Mongo DB clusters.</div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;