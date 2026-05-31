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
      className={`relative rounded-2xl bg-bg-card border cursor-pointer transition-colors overflow-hidden ${
        isActive
          ? "border-accent/50 shadow-[0_0_15px_rgba(230,57,70,0.15)]"
          : "border-border hover:border-border-light"
      }`}
    >
      {isActive && (
        <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-accent/20 text-accent text-[10px] font-bold uppercase tracking-wider">
          Active
        </div>
      )}

      <div className="p-5">
        <h3 className="font-semibold capitalize text-text-primary mb-4 pr-14">
          {name}
        </h3>
        <div className="flex items-center gap-1">
          {Array.from({ length: 6 }).map((_, i) => {
            const poke = pokemon[i];
            return (
              <div
                key={i}
                className="w-10 h-10 rounded-lg bg-bg-secondary flex items-center justify-center overflow-hidden"
              >
                {poke ? (
                  <img
                    src={spriteUrl(poke.pokemon_id, poke.shiny)}
                    alt={poke.pokname}
                    className="w-9 h-9 object-contain"
                    loading="lazy"
                  />
                ) : (
                  <span className="text-text-muted text-xs">—</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
