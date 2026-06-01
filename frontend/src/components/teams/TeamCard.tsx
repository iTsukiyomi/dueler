import { motion } from "framer-motion";
import { spriteUrl } from "../../utils/pokemon";
import { BorderBeam } from "../ui/BorderBeam";

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
      className={`relative rounded-2xl bg-bg-card/45 border cursor-pointer transition-all duration-300 overflow-hidden group ${
        isActive
          ? "border-accent/60 shadow-[0_0_20px_rgba(207,162,64,0.15)] bg-bg-card/60"
          : "border-border/60 hover:border-accent/40"
      }`}
    >
      {/* Laser glow beam */}
      <BorderBeam
        duration={5}
        borderWidth={1.5}
        colorFrom={isActive ? "#cfa240" : "#3e3a55"}
        colorTo={isActive ? "#f1cd7c" : "#282537"}
        className={isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100 transition-opacity duration-300"}
      />

      {isActive && (
        <div className="absolute top-4 right-4 px-2.5 py-0.5 rounded bg-accent/20 border border-accent/40 text-accent text-[9px] font-bold uppercase tracking-widest font-display">
          Active Squad
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
                className="w-10 h-10 rounded-lg bg-bg-secondary/70 border border-border/40 flex items-center justify-center overflow-hidden hover:border-accent/30 transition-all duration-300"
              >
                {poke ? (
                  <img
                    src={spriteUrl(poke.pokemon_id, poke.shiny)}
                    alt={poke.pokname}
                    className="w-9 h-9 object-contain"
                    loading="lazy"
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
