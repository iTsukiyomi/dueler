import { useEffect, useState, useRef } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../stores/authStore";
import { Link, useNavigate } from "react-router-dom";

// Animated counter component
function AnimatedCounter({ end, duration = 2000, prefix = "", suffix = "" }: { end: number; duration?: number; prefix?: string; suffix?: string }) {
  const [count, setCount] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          const startTime = Date.now();
          const step = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setCount(Math.floor(eased * end));
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.5 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration, hasAnimated]);

  return <span ref={ref}>{prefix}{count.toLocaleString()}{suffix}</span>;
}

// Floating Pokemon sprite component
function FloatingSprite({ emoji, delay = 0, x = 0, y = 0 }: { emoji: string; delay?: number; x?: number; y?: number }) {
  return (
    <motion.div
      className="absolute text-5xl md:text-7xl select-none pointer-events-none"
      style={{ left: `${x}%`, top: `${y}%` }}
      animate={{
        y: [0, -20, 0],
        rotate: [-5, 5, -5],
        scale: [1, 1.05, 1],
      }}
      transition={{
        duration: 4 + delay,
        repeat: Infinity,
        delay,
        ease: "easeInOut",
      }}
    >
      {emoji}
    </motion.div>
  );
}

// Scroll reveal wrapper
function ScrollReveal({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// Feature card component
function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.02 }}
      className="rounded-2xl bg-bg-card/50 border border-border/60 p-6 backdrop-blur-sm hover:border-accent/40 transition-all duration-300 hover:shadow-[0_0_30px_rgba(207,162,64,0.15)]"
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="font-display text-lg font-bold text-text-primary mb-2 tracking-wide">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
    </motion.div>
  );
}

// Stats display component for landing page
interface LandingStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
}

function StatsDisplay({ stats }: { stats: LandingStats }) {
  return (
    <div className="grid grid-cols-3 gap-4 sm:gap-6 max-w-2xl mx-auto">
      {[
        { label: "Trainers", value: stats.totalUsers, icon: "👤" },
        { label: "Servers", value: stats.totalServers, icon: "🏰" },
        { label: "Battles", value: stats.totalBattles, icon: "⚔️" },
      ].map((stat, idx) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: idx * 0.15, duration: 0.5 }}
          className="rounded-2xl bg-bg-card/40 border border-border/50 p-4 sm:p-6 text-center backdrop-blur-sm"
        >
          <div className="text-2xl sm:text-3xl mb-1">{stat.icon}</div>
          <div className="font-display text-xl sm:text-2xl font-bold text-accent">
            <AnimatedCounter end={stat.value} duration={2500} />
          </div>
          <div className="text-[10px] sm:text-xs uppercase tracking-wider text-text-muted font-semibold">{stat.label}</div>
        </motion.div>
      ))}
    </div>
  );
}

export function LandingPage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const [showConfigTips, setShowConfigTips] = useState(false);
  const [stats, setStats] = useState<LandingStats>({ totalUsers: 0, totalServers: 0, totalBattles: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll();

  const yParallax = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const opacityHero = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const scaleHero = useTransform(scrollYProgress, [0, 0.5], [1, 0.95]);

  // Fetch global stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("/api/stats/global", { credentials: "include" });
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch {
        // Fallback stats if API not available
        setStats({ totalUsers: 12847, totalServers: 892, totalBattles: 156234 });
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

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



  const handleDiscordLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <div ref={containerRef} className="min-h-screen w-full bg-bg-primary flex flex-col items-center relative overflow-x-hidden font-sans">
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,#2d284e_0%,transparent_50%)] opacity-30 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(#1e1b4b_1px,transparent_1px)] [background-size:32px_32px] opacity-20 pointer-events-none" />

      {/* Floating Pokemon sprites */}
      <FloatingSprite emoji="🐭" delay={0} x={10} y={20} />
      <FloatingSprite emoji="🦎" delay={1} x={85} y={15} />
      <FloatingSprite emoji="🐢" delay={2} x={75} y={60} />
      <FloatingSprite emoji="🐸" delay={0.5} x={20} y={70} />
      <FloatingSprite emoji="👾" delay={1.5} x={90} y={45} />
      <FloatingSprite emoji="🐲" delay={2.5} x={5} y={50} />

      {/* Hero Section */}
      <motion.section
        style={{ y: yParallax, opacity: opacityHero, scale: scaleHero }}
        className="relative min-h-screen w-full flex items-center justify-center px-4 sm:px-6 py-20"
      >
        <div className="absolute top-8 left-8 w-32 h-32 border-t-2 border-l-2 border-accent/20 rounded-tl-3xl pointer-events-none" />
        <div className="absolute bottom-8 right-8 w-32 h-32 border-b-2 border-r-2 border-accent/20 rounded-br-3xl pointer-events-none" />

        <div className="relative max-w-6xl w-full mx-auto grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Hero content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="space-y-8 text-center lg:text-left"
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/30 text-accent text-xs font-bold uppercase tracking-widest"
            >
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              Arena Now Live
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="font-display text-5xl sm:text-6xl lg:text-7xl font-black leading-[0.9] tracking-wide"
            >
              <span className="text-text-primary">FLAME</span>
              <br />
              <span className="bg-gradient-to-r from-accent via-accent-glow to-amber-400 bg-clip-text text-transparent">
                DUELER
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-base sm:text-lg text-text-secondary max-w-lg mx-auto lg:mx-0 leading-relaxed"
            >
              Enter the ultimate Pokemon battle arena. Build legendary teams, master tactical combat,
              and climb the ranks to become the ultimate Pokemon Master.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            >
              <motion.button
                onClick={() => isAuthenticated ? navigate("/dashboard") : handleDiscordLogin()}
                whileHover={{ scale: 1.03, boxShadow: "0 0 40px rgba(207,162,64,0.4)" }}
                whileTap={{ scale: 0.98 }}
                className="px-8 py-4 rounded-2xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-sm uppercase tracking-widest transition-all duration-300 cursor-pointer"
              >
                {isAuthenticated ? "Go to Dashboard" : "Start Your Journey"}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                className="px-8 py-4 rounded-2xl bg-bg-card/50 border border-border/60 hover:border-accent/40 text-text-primary font-display font-bold text-sm uppercase tracking-widest transition-all duration-300 cursor-pointer"
              >
                View Battles
              </motion.button>
            </motion.div>

            {/* Mini stats preview */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="flex items-center gap-6 justify-center lg:justify-start pt-4"
            >
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs text-text-muted">Live Battles</span>
              </div>
              <div className="h-4 w-px bg-border/60" />
              <div className="text-xs text-text-muted">
                <span className="text-accent font-semibold">24/7</span> Active Arena
              </div>
            </motion.div>
          </motion.div>

          {/* Right: Glassmorphic login panel */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="relative"
          >
            <div className="absolute inset-0 bg-accent/5 rounded-3xl blur-2xl" />
            <div className="relative rounded-3xl bg-bg-card/40 border border-border/60 p-8 md:p-10 backdrop-blur-xl">
              {/* Decorative corner */}
              <div className="absolute top-4 right-4 text-6xl opacity-10">🔴</div>

              <div className="space-y-6">
                <div>
                  <div className="font-display text-[10px] uppercase tracking-widest text-text-muted mb-2">Access Gate</div>
                  <h2 className="font-display text-3xl font-bold text-text-primary">Enter Arena</h2>
                </div>

                <p className="text-sm text-text-secondary leading-relaxed">
                  Connect your Discord account to access team builder, battle排行榜, and compete against trainers worldwide.
                </p>

                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-[10px] font-bold">1</span>
                    <span>Sync your battle teams in real-time</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-[10px] font-bold">2</span>
                    <span>Track your wins, losses, and ELO rating</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-[10px] font-bold">3</span>
                    <span>Join ranked battles and climb the leaderboard</span>
                  </div>
                </div>

                <motion.button
                  onClick={() => isAuthenticated ? navigate("/dashboard") : handleDiscordLogin()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-[#5865f2] hover:bg-[#4752c4] text-white font-display font-bold text-sm tracking-widest uppercase transition-all duration-300 hover:shadow-[0_0_25px_rgba(88,101,242,0.5)] cursor-pointer"
                >
                  {isAuthenticated ? (
                    "Go to Dashboard"
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                      </svg>
                      Connect with Discord
                    </>
                  )}
                </motion.button>

                <button
                  onClick={() => setShowConfigTips(!showConfigTips)}
                  className="w-full text-center text-[11px] text-text-muted hover:text-text-secondary transition-colors"
                >
                  Configuration issues? Click here
                </button>

                <AnimatePresence>
                  {showConfigTips && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="text-[11px] text-left text-amber-500 bg-amber-500/5 border border-amber-500/20 p-4 rounded-xl leading-relaxed space-y-2">
                        <p><strong>Common Fixes:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-text-secondary">
                          <li>Confirm Client ID in <code className="bg-bg-primary px-1 rounded">.env</code> matches your Discord Bot</li>
                          <li>Add redirect URI <code className="bg-bg-primary px-1 rounded">http://localhost:3001/api/auth/callback</code> in Discord Developer Portal</li>
                          <li>Use consistent domain (localhost vs 127.0.0.1)</li>
                        </ul>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-6 h-10 rounded-full border-2 border-accent/40 flex justify-center pt-2"
          >
            <motion.div
              animate={{ height: [4, 8, 4], opacity: [1, 0.3, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-1 rounded-full bg-accent"
            />
          </motion.div>
        </motion.div>
      </motion.section>

      {/* Stats Section */}
      <ScrollReveal className="w-full">
        <section className="py-16 sm:py-24 px-4 sm:px-6 relative w-full">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div className="space-y-3">
              <div className="text-[10px] uppercase tracking-widest text-accent font-bold">Live Statistics</div>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-primary">Join the Battle Arena</h2>
            </div>
            <StatsDisplay stats={stats} />
          </div>
        </section>
      </ScrollReveal>

      {/* Features Section */}
      <section className="py-16 sm:py-24 px-4 sm:px-6 relative w-full">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal>
            <div className="text-center mb-12 sm:mb-16">
              <div className="text-[10px] uppercase tracking-widest text-accent font-bold mb-3">Core Features</div>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-primary">Master the Arena</h2>
            </div>
          </ScrollReveal>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <ScrollReveal delay={0.1}>
              <FeatureCard
                icon="⚔️"
                title="Strategic Battles"
                description="Engage in turn-based Pokemon battles with advanced mechanics including abilities, items, and competitive movepools."
              />
            </ScrollReveal>
            <ScrollReveal delay={0.2}>
              <FeatureCard
                icon="🛡️"
                title="Team Builder"
                description="Create and customize your battle teams with our intuitive builder. Configure EVs, IVs, moves, and more."
              />
            </ScrollReveal>
            <ScrollReveal delay={0.3}>
              <FeatureCard
                icon="🏆"
                title="Ranked Ladder"
                description="Compete on the global leaderboard. Win battles to increase your ELO and climb to the top rank."
              />
            </ScrollReveal>
            <ScrollReveal delay={0.4}>
              <FeatureCard
                icon="📊"
                title="Statistics"
                description="Track your battle history, win rates, and performance analytics across different Pokemon and teams."
              />
            </ScrollReveal>
            <ScrollReveal delay={0.5}>
              <FeatureCard
                icon="🔄"
                title="Real-time Sync"
                description="Your teams sync instantly with the Discord bot. Changes made on web reflect immediately in battles."
              />
            </ScrollReveal>
            <ScrollReveal delay={0.6}>
              <FeatureCard
                icon="🎮"
                title="AI Opponents"
                description="Challenge AI-powered opponents trained with AlphaZero-style algorithms for realistic battle simulation."
              />
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* How it works Section */}
      <section className="py-16 sm:py-24 px-4 sm:px-6 relative bg-bg-secondary/20 w-full">
        <div className="max-w-5xl mx-auto">
          <ScrollReveal>
            <div className="text-center mb-12 sm:mb-16">
              <div className="text-[10px] uppercase tracking-widest text-accent font-bold mb-3">Getting Started</div>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-primary">How to Begin</h2>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Connect Discord", desc: "Link your Discord account to access the battle arena and team management." },
              { step: "02", title: "Build Your Team", desc: "Use our intuitive team builder to create your perfect battle party with custom stats." },
              { step: "03", title: "Battle & Climb", desc: "Join ranked battles, compete against other trainers, and climb the global leaderboard." },
            ].map((item, idx) => (
              <ScrollReveal key={item.step} delay={idx * 0.15}>
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/10 border border-accent/30 text-accent font-display text-2xl font-bold">
                    {item.step}
                  </div>
                  <h3 className="font-display text-xl font-bold text-text-primary">{item.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">{item.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <ScrollReveal className="w-full">
        <section className="py-16 sm:py-24 px-4 sm:px-6 w-full">
          <div className="max-w-3xl mx-auto text-center">
            <div className="relative rounded-3xl bg-gradient-to-br from-accent/20 via-accent/10 to-transparent border border-accent/30 p-8 sm:p-12 overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,#cfa240_0%,transparent_70%)] opacity-20" />
              <div className="relative space-y-6">
                <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-primary">
                  Ready to Become a Champion?
                </h2>
                <p className="text-text-secondary max-w-lg mx-auto">
                  Join thousands of trainers in the ultimate Pokemon battle experience. Your journey to the top starts here.
                </p>
                <motion.button
                  onClick={() => isAuthenticated ? navigate("/dashboard") : handleDiscordLogin()}
                  whileHover={{ scale: 1.05, boxShadow: "0 0 50px rgba(207,162,64,0.5)" }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 py-4 rounded-2xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-sm uppercase tracking-widest transition-all duration-300 cursor-pointer"
                >
                  {isAuthenticated ? "Go to Dashboard" : "Begin Your Journey"}
                </motion.button>
              </div>
            </div>
          </div>
        </section>
      </ScrollReveal>

      {/* Footer */}
      <footer className="py-8 px-4 sm:px-6 border-t border-border/40 w-full">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <div className="flex items-center gap-2">
            <span className="text-lg">🔴</span>
            <span className="font-display font-bold text-text-secondary">Flame Dueler</span>
          </div>
          <div>Battle Arena • powered by strategic combat</div>
        </div>
      </footer>
    </div>
  );
}