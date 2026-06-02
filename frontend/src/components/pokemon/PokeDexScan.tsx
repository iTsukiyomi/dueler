import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TypeBadge } from "../ui/TypeBadge";

interface PokeDexScanProps {
  pokemonName: string | null;
  onClose: () => void;
}

interface PokemonData {
  id: number;
  name: string;
  types: string[];
  stats: { hp: number; atk: number; def: number; spa: number; spd: number; spe: number };
  abilities: string[];
  height: number;
  weight: number;
  description: string;
}

export function PokeDexScan({ pokemonName, onClose }: PokeDexScanProps) {
  const [data, setData] = useState<PokemonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanActive, setScanActive] = useState(false);

  useEffect(() => {
    if (!pokemonName) {
      setData(null);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      setScanActive(true);
      try {
        const res = await fetch(`/api/gamedata/pokemon/${encodeURIComponent(pokemonName.toLowerCase())}`);
        if (res.ok) {
          const detail = await res.json();
          
          // Map to custom layout
          const stats = detail.base_stats || { hp: 50, atk: 50, def: 50, spa: 50, spd: 50, spe: 50 };
          const abilities = detail.abilities ? detail.abilities.map((a: any) => a.display_name) : [];
          
          setData({
            id: detail.pokemon_id,
            name: detail.identifier,
            types: detail.types || ["Normal"],
            stats: {
              hp: stats.hp,
              atk: stats.atk,
              def: stats.def,
              spa: stats.spa,
              spd: stats.spd,
              spe: stats.spe,
            },
            abilities,
            height: detail.height || 10,
            weight: detail.weight || 100,
            description: detail.description || `Data records for #${detail.pokemon_id} are currently encrypted. Initiating backup retrieval...`
          });
        }
      } catch (err) {
        console.error("Failed to load scan details:", err);
      } finally {
        setLoading(false);
        // Keep scan active for 1.2s to show animation
        setTimeout(() => setScanActive(false), 1200);
      }
    };

    fetchDetails();
  }, [pokemonName]);

  if (!pokemonName) return null;

  const displayName = pokemonName
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-modal flex justify-start select-none">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-bg-void/80 backdrop-blur-sm"
        />

        {/* Pokédex cover/drawer panel */}
        <motion.div
          initial={{ x: "-100%" }}
          animate={{ x: 0 }}
          exit={{ x: "-100%" }}
          transition={{ type: "spring", stiffness: 260, damping: 25 }}
          className="relative w-full max-w-[420px] h-full bg-bg-void/95 flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.8)] border-l-4 border-poke-red border-r-4 border-poke-blue z-raised overflow-hidden"
        >
          {/* Scanning laser sweep line */}
          {scanActive && (
            <div
              className="absolute left-0 right-0 h-1.5 bg-poke-blue shadow-[0_0_12px_rgba(0,191,255,0.8),_0_0_24px_rgba(0,191,255,0.4)] pointer-events-none"
              style={{
                top: 0,
                animation: "scanLine 1.2s cubic-bezier(0.16, 1, 0.3, 1) infinite"
              }}
            />
          )}

          {/* Top Header */}
          <div className="h-14 bg-poke-red flex items-center justify-between px-6 border-b border-border-brand relative shrink-0">
            <h3 className="font-display font-black text-sm text-white tracking-widest uppercase">
              Pokédex Analysis
            </h3>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded bg-black/25 flex items-center justify-center text-white font-bold hover:bg-black/40 transition-colors cursor-pointer"
            >
              ✕
            </button>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-poke-yellow opacity-40" />
          </div>

          {/* Scrollable details panel */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-64 space-y-4">
                <div className="w-10 h-10 border-2 border-poke-blue border-t-transparent rounded-full animate-spin-pokeball" />
                <span className="mono text-[10px] text-text-secondary tracking-widest uppercase">
                  Decoding Encrypted Frequencies
                </span>
              </div>
            ) : data ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                {/* Visual Avatar */}
                <div className="flex flex-col items-center justify-center p-6 bg-bg-raised border border-border-default rounded-xl relative overflow-hidden group">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,191,255,0.06)_0%,transparent_70%)]" />
                  <img
                    src={`/pokemon-icons/${data.id}.png`}
                    alt={data.name}
                    className="w-28 h-28 object-contain drop-shadow-[0_10px_20px_rgba(0,0,0,0.6)]"
                    style={{ imageRendering: "pixelated" }}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%233D5068' stroke-width='1.5'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='2' y1='12' x2='22' y2='12'/%3E%3Ccircle cx='12' cy='12' r='3' fill='%230A0D16'/%3E%3C/svg%3E";
                    }}
                  />
                  <div className="mt-4 flex items-center justify-between w-full">
                    <span className="mono text-xs font-bold text-text-muted">
                      INDEX #{data.id.toString().padStart(4, "0")}
                    </span>
                    <div className="flex gap-1">
                      {data.types.map((type) => (
                        <TypeBadge key={type} type={type} size="sm" />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Identity info */}
                <div className="space-y-1">
                  <h2 className="font-display text-2xl font-black tracking-wide text-text-primary uppercase">
                    {displayName}
                  </h2>
                  <span className="text-xs text-text-brand mono block">
                    HT: {(data.height / 10).toFixed(1)}m | WT: {(data.weight / 10).toFixed(1)}kg
                  </span>
                </div>

                {/* Database Description */}
                <div className="p-4 bg-bg-input border border-border-subtle rounded-lg text-xs leading-relaxed text-text-secondary relative">
                  <div className="absolute top-1 left-2 mono text-[8px] text-text-muted uppercase">
                    Trainer Bio Records
                  </div>
                  <p className="mt-2 font-mono text-[11px] leading-relaxed">
                    {data.description}
                  </p>
                </div>

                {/* Stats Table */}
                <div className="space-y-3">
                  <h4 className="font-rajdhani text-xs font-bold tracking-widest text-text-muted uppercase border-b border-border-subtle pb-1">
                    Base Stat Vectors
                  </h4>
                  <div className="space-y-2">
                    {[
                      ["HP", data.stats.hp, 255, "hp"],
                      ["Attack", data.stats.atk, 190, "atk"],
                      ["Defense", data.stats.def, 230, "def"],
                      ["Sp. Atk", data.stats.spa, 194, "spa"],
                      ["Sp. Def", data.stats.spd, 230, "spd"],
                      ["Speed", data.stats.spe, 180, "spe"],
                    ].map(([label, val, max, key]) => {
                      const pct = Math.min(100, ((val as number) / (max as number)) * 100);
                      return (
                        <div key={label as string} className="space-y-0.5">
                          <div className="flex justify-between items-center text-[10px] mono">
                            <span className="text-text-secondary uppercase">{label as string}</span>
                            <span className="text-text-primary">{val as number}/{max as number}</span>
                          </div>
                          <div className="stat-bar-track">
                            <div
                              className={`stat-bar-fill ${
                                (val as number) >= 100 ? "high" : (val as number) <= 50 ? "low" : "medium"
                              }`}
                              style={{
                                width: `${pct}%`,
                                "--fill-pct": `${pct}%`,
                              } as React.CSSProperties}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Abilities */}
                <div className="space-y-2">
                  <h4 className="font-rajdhani text-xs font-bold tracking-widest text-text-muted uppercase border-b border-border-subtle pb-1">
                    Signature Abilities
                  </h4>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {data.abilities.map((ability) => (
                      <span
                        key={ability}
                        className="px-2.5 py-1 rounded bg-bg-raised border border-border-default text-xs font-mono text-text-primary"
                      >
                        {ability}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="flex items-center justify-center h-64 text-text-muted text-xs mono uppercase">
                Offline or Unregistered Terminal
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default PokeDexScan;
