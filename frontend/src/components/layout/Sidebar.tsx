import React, { useEffect, useState } from "react";
import { NavLink, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";

interface NavItem {
  to: string;
  label: string;
  type: string; // Pokémon type representation for icons
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Trainer Card", type: "normal", end: true },
  { to: "/dashboard/teams", label: "Squad Editor", type: "fire" },
  { to: "/dashboard/leaderboard", label: "Hall of Fame", type: "electric" },
  { to: "/dashboard/battles", label: "Battle Logs", type: "water" },
  { to: "/dashboard/settings", label: "OS Settings", type: "steel" },
];

export function Sidebar() {
  const { user } = useAuthStore();
  const { data: profile } = usePlayerProfile();
  const [footerSpriteUrl, setFooterSpriteUrl] = useState<string>("");
  const [spriteName, setSpriteName] = useState<string>("");

  // Select a random Pokémon sprite on mount from the manifest
  useEffect(() => {
    fetch("/pokemon-icons/manifest.json")
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Manifest error");
      })
      .then((data) => {
        if (data && data.pokemon && data.pokemon.length > 0) {
          const randPoke = data.pokemon[Math.floor(Math.random() * data.pokemon.length)];
          setFooterSpriteUrl(`/pokemon-icons/${randPoke.id}.png`);
          setSpriteName(randPoke.name);
        }
      })
      .catch((err) => {
        // Fallback to Pikachu
        console.error("Failed to load footer random sprite:", err);
        setFooterSpriteUrl("/pokemon-icons/25.png");
        setSpriteName("pikachu");
      });
  }, []);

  const linkClass = ({ isActive }: { isActive: boolean }) => {
    return `sidebar-item ${isActive ? "active" : ""}`;
  };

  const wins = profile?.wins ?? 0;
  const losses = profile?.losses ?? 0;
  const total = wins + losses;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";

  return (
    <aside className="sidebar select-none">
      {/* Brand Header */}
      <div className="flex items-center gap-3 border-b border-border-subtle pb-4 px-6 mb-6">
        <div className="relative w-8 h-8 rounded-full border border-border-default bg-bg-raised flex items-center justify-center">
          <svg width="16" height="16" viewBox="0 0 32 32" className="text-poke-red">
            <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M 3.05 16 A 13 13 0 0 1 28.95 16 Z" fill="currentColor" />
            <line x1="2" y1="16" x2="30" y2="16" stroke="currentColor" strokeWidth="2" />
            <circle cx="16" cy="16" r="4.5" fill="var(--bg-raised)" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>
        <span className="sidebar-label font-display text-sm font-extrabold text-text-primary tracking-widest uppercase truncate">
          Flame Dueler
        </span>
      </div>

      {/* Navigation Groups */}
      <nav className="flex flex-col gap-0.5">
        <div className="sidebar-group-label sidebar-label">
          Control Panel
        </div>
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
            {/* SVG Pokémon type badge as Nav Icon */}
            <img
              src={`/pokemon-icons/types/${item.type}.svg`}
              alt=""
              className="w-4 h-4 object-contain shrink-0"
              style={{ filter: "brightness(0.85)" }}
            />
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Hollow stats card (Record Card) */}
      <div className="mt-auto px-4 space-y-4 sidebar-label">
        <div className="p-4 rounded-lg bg-bg-raised border border-border-default space-y-3">
          <div className="mono text-[9px] uppercase font-bold text-text-muted tracking-widest">
            Record File
          </div>
          <div className="space-y-1.5 text-xs font-semibold">
            <div className="flex justify-between">
              <span className="text-text-muted">WINS</span>
              <span className="text-emerald-400 font-mono font-bold">{wins}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">LOSSES</span>
              <span className="text-poke-red font-mono font-bold">{losses}</span>
            </div>
            <div className="flex justify-between border-t border-border-subtle pt-2 mt-2">
              <span className="text-text-muted">RATIO</span>
              <span className="text-poke-yellow font-mono font-bold">{winRate}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer random sprite */}
      <div className="px-6 pt-4 mt-4 border-t border-border-subtle flex flex-col items-center gap-2">
        {footerSpriteUrl && (
          <div className="relative group">
            <img
              src={footerSpriteUrl}
              alt={spriteName}
              title={`Silph CO Registry: ${spriteName}`}
              className="w-12 h-12 object-contain filter grayscale opacity-30 select-none pointer-events-none group-hover:opacity-60 transition-opacity duration-300"
              style={{ imageRendering: "pixelated" }}
            />
          </div>
        )}
        <div className="mono text-[8px] text-text-muted text-center tracking-widest leading-normal sidebar-label uppercase">
          <div>DATABASE ACTIVE</div>
          <div className="text-[7px] text-[#57F287] mt-0.5">● ONLINE FREQUENCY</div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;