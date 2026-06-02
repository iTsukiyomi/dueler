import { motion } from "framer-motion";
import { spriteUrl } from "../../utils/pokemon";

interface TeamCardProps {
  name: string;
  pokemon: { pokname: string; pokemon_id: number; shiny: boolean }[];
  isActive: boolean;
  onClick: () => void;
}

export function TeamCard({ name, pokemon, isActive, onClick }: TeamCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`card p-6 cursor-pointer flex flex-col justify-between select-none ${
        isActive
          ? "border-[var(--poke-yellow)]/50 bg-[var(--bg-float)] shadow-md"
          : ""
      }`}
    >
      {isActive && (
        <div className="absolute top-4 right-4 px-2 py-0.5 rounded-[var(--radius-sm)] bg-[var(--poke-yellow-glow)] border border-[var(--poke-yellow)]/30 text-[var(--poke-yellow)] text-[9px] font-bold uppercase tracking-widest font-rajdhani">
          Active Squad
        </div>
      )}

      <div>
        <h3 className="font-display text-sm font-bold capitalize text-text-primary mb-5 pr-16 tracking-wide truncate">
          {name}
        </h3>
        <div className="flex items-center gap-2">
          {Array.from({ length: 6 }).map((_, i) => {
            const poke = pokemon[i];
            return (
              <div
                key={i}
                className="w-10 h-10 rounded-full bg-[var(--bg-overlay)] border border-[var(--border-default)] flex items-center justify-center overflow-hidden hover:border-[var(--border-bright)] transition-colors"
              >
                {poke ? (
                  <img
                    src={spriteUrl(poke.pokemon_id, poke.shiny)}
                    alt={poke.pokname}
                    className="w-9 h-9 object-contain"
                    style={{ imageRendering: "pixelated" }}
                    loading="lazy"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%233D5068'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3C/svg%3E";
                    }}
                  />
                ) : (
                  <span className="text-text-muted text-[10px] font-mono select-none font-bold">—</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

export default TeamCard;
