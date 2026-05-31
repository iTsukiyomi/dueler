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
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`relative rounded-2xl bg-bg-card/40 border cursor-pointer transition-all duration-300 overflow-hidden ${
        isActive
          ? "border-accent/60 shadow-[0_0_18px_rgba(207,162,64,0.15)] bg-bg-card/60"
          : "border-border/60 hover:border-border-light hover:bg-bg-card/60"
      }`}
    >
      {isActive && (
        <div className="absolute top-4 right-4 px-2.5 py-0.5 rounded bg-accent/20 border border-accent/40 text-accent text-[9px] font-bold uppercase tracking-wider font-display">
          Active Party
        </div>
      )}

      <div className="p-6">
        <h3 className="font-display text-lg font-bold capitalize text-text-primary mb-4 pr-16 tracking-wide">
          {name}
        </h3>
        <div className="flex items-center gap-1.5">
          {Array.from({ length: 6 }).map((_, i) => {
            const poke = pokemon[i];
            return (
              <div
                key={i}
                className="w-10 h-10 rounded-lg bg-bg-secondary/60 border border-border/40 flex items-center justify-center overflow-hidden hover:border-border transition-colors"
              >
                {poke ? (
                  <img
                    src={spriteUrl(poke.pokemon_id, poke.shiny)}
                    alt={poke.pokname}
                    className="w-9 h-9 object-contain"
                    loading="lazy"
                  />
                ) : (
                  <span className="text-text-muted text-xs font-mono">—</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
