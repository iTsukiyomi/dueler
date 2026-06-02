import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TypeBadge } from "../ui/TypeBadge";

interface SpriteCardProps {
  id: number;
  name: string;
  types: string[];
  shiny?: boolean;
  category?: string;
  stats?: {
    hp: number;
    atk: number;
    def: number;
    spa?: number;
    spd?: number;
    spe?: number;
  };
  onClick?: () => void;
  onScan?: () => void;
  featured?: boolean;
}

const padId = (id: number) => {
  if (id < 10) return `#000${id}`;
  if (id < 100) return `#00${id}`;
  if (id < 1000) return `#0${id}`;
  return `#${id}`;
};

export function SpriteCard({
  id,
  name,
  types,
  shiny = false,
  category = "Pokémon",
  stats,
  onClick,
  onScan,
  featured = false,
}: SpriteCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [sparkling, setSparkling] = useState(false);

  const getSpriteUrl = (pokemonId: number, shinyVariant = false) => {
    return `/pokemon-icons/${shinyVariant ? "shiny-" : ""}${pokemonId}.png`;
  };

  const handleCatchBounce = () => {
    if (shiny) {
      setSparkling(true);
      setTimeout(() => setSparkling(false), 800);
    }
  };

  const displayName = name
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`card p-5 cursor-pointer flex flex-col justify-between select-none relative group h-full ${
        featured ? "featured" : ""
      }`}
    >
      {/* Sparkles for Shiny variants */}
      {shiny && sparkling && (
        <div className="absolute inset-0 pointer-events-none z-10">
          <svg className="absolute w-4 h-4 text-poke-yellow" style={{ left: "15%", top: "20%", animation: "sparkleScale 0.8s ease-in-out" }} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <svg className="absolute w-3 h-3 text-poke-yellow" style={{ right: "15%", top: "30%", animation: "sparkleScale 0.8s ease-in-out 0.1s" }} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <svg className="absolute w-3.5 h-3.5 text-poke-yellow" style={{ left: "20%", bottom: "25%", animation: "sparkleScale 0.8s ease-in-out 0.2s" }} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <svg className="absolute w-4 h-4 text-poke-yellow" style={{ right: "25%", bottom: "20%", animation: "sparkleScale 0.8s ease-in-out 0.3s" }} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
      )}

      {/* Top zone (ID + Badges) */}
      <div className="flex justify-between items-center w-full">
        <span className="mono text-[10px] font-bold text-text-muted">
          {padId(id)}
        </span>
        <div className="flex gap-1">
          {types.map((type) => (
            <TypeBadge key={type} type={type} size="sm" />
          ))}
        </div>
      </div>

      {/* Sprite Zone */}
      <div className="flex justify-center items-center h-24 my-3 relative">
        <motion.img
          src={getSpriteUrl(id, shiny)}
          alt={name}
          className="w-20 h-20 object-contain drop-shadow-[0_4px_8px_rgba(0,0,0,0.5)]"
          style={{ imageRendering: "pixelated" }}
          animate={
            isHovered
              ? { scale: 1.08, y: -4 }
              : { scale: 1, y: 0 }
          }
          transition={{ type: "spring", stiffness: 300, damping: 15 }}
          onClick={(e) => {
            e.stopPropagation();
            handleCatchBounce();
          }}
          onError={(e) => {
            // Fallback to a Poké Ball outline if sprite is missing
            const target = e.target as HTMLImageElement;
            target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%233D5068' stroke-width='1.5'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='2' y1='12' x2='22' y2='12'/%3E%3Ccircle cx='12' cy='12' r='3' fill='%230A0D16'/%3E%3C/svg%3E";
          }}
        />
      </div>

      {/* Pokédex Divider line with centered Poké Ball */}
      <div className="relative w-full my-2 flex items-center justify-center">
        <div className="absolute inset-x-0 h-px bg-border-subtle" />
        <div className="relative w-5 h-5 rounded-full bg-bg-raised border border-border-default flex items-center justify-center text-text-muted group-hover:text-poke-red transition-colors">
          <svg width="10" height="10" viewBox="0 0 32 32" fill="currentColor">
            <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M 3.05 16 A 13 13 0 0 1 28.95 16 Z" fill="currentColor" opacity="0.3" />
            <line x1="2" y1="16" x2="30" y2="16" stroke="currentColor" strokeWidth="2" />
            <circle cx="16" cy="16" r="5" fill="var(--bg-raised)" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>
      </div>

      {/* Info zone */}
      <div className="space-y-1">
        <h4 className="font-display text-sm font-bold text-text-primary tracking-wide leading-tight group-hover:text-poke-yellow transition-colors">
          {displayName}
        </h4>
        <span className="text-[10px] text-text-secondary leading-none block">
          {category}
        </span>
      </div>

      {/* Stats preview zone (Optional) */}
      {stats && (
        <div className="mt-4 pt-3 border-t border-border-subtle space-y-2">
          {stats.hp !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between items-center text-[9px] mono">
                <span className="text-text-muted">HP</span>
                <span className="text-text-secondary">{stats.hp}/255</span>
              </div>
              <div className="stat-bar-track">
                <div
                  className={`stat-bar-fill ${
                    stats.hp >= 100 ? "high" : stats.hp <= 50 ? "low" : "medium"
                  }`}
                  style={{
                    width: `${Math.min(100, (stats.hp / 255) * 100)}%`,
                    "--fill-pct": `${Math.min(100, (stats.hp / 255) * 100)}%`,
                  } as React.CSSProperties}
                />
              </div>
            </div>
          )}
          {stats.atk !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between items-center text-[9px] mono">
                <span className="text-text-muted">ATK</span>
                <span className="text-text-secondary">{stats.atk}/190</span>
              </div>
              <div className="stat-bar-track">
                <div
                  className={`stat-bar-fill ${
                    stats.atk >= 100 ? "high" : stats.atk <= 50 ? "low" : "medium"
                  }`}
                  style={{
                    width: `${Math.min(100, (stats.atk / 190) * 100)}%`,
                    "--fill-pct": `${Math.min(100, (stats.atk / 190) * 100)}%`,
                  } as React.CSSProperties}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scanning HUD Overlay Trigger */}
      {onScan && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onScan();
          }}
          className="mt-4 w-full py-1 rounded bg-border-subtle hover:bg-border-bright text-[10px] font-bold uppercase tracking-widest text-text-secondary hover:text-text-primary border border-transparent hover:border-border-active transition-all cursor-pointer"
        >
          🔍 Pokédex Analysis
        </button>
      )}
    </div>
  );
}

export default SpriteCard;
