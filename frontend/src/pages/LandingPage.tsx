import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { 
  ArrowRight,
  ShieldAlert,
  ChevronRight
} from "lucide-react";
import { PixelTrail } from "../components/ui/pixel-trail";
import { GooeyFilter } from "../components/ui/gooey-filter";
import { CyberneticBentoGrid } from "../components/ui/cybernetic-bento-grid";
import { ContainerScroll } from "../components/ui/container-scroll-animation";
import { CardStack, CardStackItem } from "../components/ui/card-stack";
import { useScreenSize } from "../hooks/use-screen-size";
import { NeonButton } from "../components/ui/neon-button";

interface LandingStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
}

const cardItems: CardStackItem[] = [
  {
    id: 1,
    title: "Charizard Blitz-Core",
    description: "EVs: Atk 252 / Spe 252 / HP 4. Adamant. Life Orb. Moves: Flare Blitz, Dragon Claw, Roost, Earthquake.",
    imageSrc: "https://images.unsplash.com/photo-1613771404724-11d204e4de2b?w=600&auto=format&fit=crop&q=80",
  },
  {
    id: 2,
    title: "Blastoise Torrent-Shell",
    description: "EVs: HP 252 / Def 252 / SpD 4. Bold. Leftovers. Moves: Hydro Pump, Rapid Spin, Scald, Ice Beam.",
    imageSrc: "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
  },
  {
    id: 3,
    title: "Pikachu Spark-Drive",
    description: "EVs: SpA 252 / Spe 252 / HP 4. Timid. Light Ball. Moves: Thunderbolt, Volt Switch, Grass Knot, Surf.",
    imageSrc: "https://images.unsplash.com/photo-1605973029521-815475d98f3f?w=600&auto=format&fit=crop&q=80",
  },
  {
    id: 4,
    title: "Mewtwo Psychic-Nova",
    description: "EVs: SpA 252 / Spe 252 / SpD 4. Timid. Choice Specs. Moves: Psystrike, Aura Sphere, Shadow Ball, Ice Beam.",
    imageSrc: "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&auto=format&fit=crop&q=80",
  }
];

export function LandingPage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<LandingStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const screenSize = useScreenSize();

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
      
      {/* 1. Interactive Mouse-Move Pixel Trail Background with SVG Gooey filter */}
      <GooeyFilter id="gooey-filter-pixel-trail" strength={6} />
      <div
        className="absolute inset-0 z-0 pointer-events-none opacity-20"
        style={{ filter: "url(#gooey-filter-pixel-trail)" }}
      >
        <PixelTrail
          pixelSize={screenSize.lessThan("md") ? 24 : 32}
          fadeDuration={750}
          delay={100}
          pixelClassName="bg-[var(--poke-blue)]"
        />
      </div>

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

      {/* Hero Content Section */}
      <div className="max-w-6xl w-full mx-auto px-8 pt-20 pb-10 z-10 relative">
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
              <NeonButton
                onClick={() => (isAuthenticated ? navigate("/dashboard") : handleDiscordLogin())}
                variant="solid"
                size="lg"
                className="w-fit"
              >
                <span>{isAuthenticated ? "Enter Arena Dashboard" : "Initiate Connect Hook"}</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </NeonButton>
            </div>
          </motion.div>

          {/* Right Card Stack Showcase */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-5 flex justify-center lg:justify-end overflow-hidden py-10"
          >
            <CardStack
              items={cardItems}
              cardWidth={280}
              cardHeight={380}
              autoAdvance
              intervalMs={2500}
              pauseOnHover
              showDots
            />
          </motion.div>
        </div>
      </div>

      {/* 2. Container Scroll 3D Tilt View around Terminal battle simulator */}
      <section className="w-full relative z-10 py-10">
        <ContainerScroll
          titleComponent={
            <div className="mb-4">
              <h2 className="font-display text-2xl sm:text-3xl font-extrabold uppercase text-text-primary tracking-wider mb-2">
                Simulate Showdown Battles
              </h2>
              <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">
                Experience full turn-based battles directly embedded within our interactive console control system.
              </p>
            </div>
          }
        >
          <div className="w-full h-full rounded-2xl border border-[var(--border-default)] bg-[var(--bg-raised)] p-6 font-mono text-[11px] overflow-hidden text-left flex flex-col justify-between">
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
            <div className="space-y-2.5 flex-1 overflow-y-auto">
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
            </div>
            <div className="text-text-secondary pt-3 border-t border-[var(--border-subtle)] flex items-center gap-2 mt-4 shrink-0">
              <span className="animate-pulse">_</span>
              <span className="text-[9px] text-text-muted">Awaiting Trainer Action...</span>
            </div>
          </div>
        </ContainerScroll>
      </section>

      {/* 3. Cybernetic Bento Grid Core Features */}
      <section className="w-full py-16 flex justify-center z-10 border-t border-[var(--border-default)]">
        <div className="max-w-6xl w-full px-8">
          <CyberneticBentoGrid />
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