import { spriteUrl, displayName } from "../../utils/pokemon";
import { usePokemonDetail } from "../../hooks/usePokemonData";
import { TypeBadge } from "../ui/TypeBadge";
import type { PokemonSlot } from "../../types";

interface PokemonSlotCardProps {
  slot?: PokemonSlot;
  pokemonId?: number;
  onClick: () => void;
  isSelected?: boolean;
  index: number;
}

// Type color border helpers
const TYPE_GLOWS: Record<string, string> = {
  normal: "hover:border-type-normal/50 hover:shadow-[0_0_12px_rgba(168,168,120,0.15)]",
  fire: "hover:border-type-fire/50 hover:shadow-[0_0_12px_rgba(240,128,48,0.15)]",
  water: "hover:border-type-water/50 hover:shadow-[0_0_12px_rgba(104,144,240,0.15)]",
  electric: "hover:border-type-electric/50 hover:shadow-[0_0_12px_rgba(248,208,48,0.15)]",
  grass: "hover:border-type-grass/50 hover:shadow-[0_0_12px_rgba(120,200,80,0.15)]",
  ice: "hover:border-type-ice/50 hover:shadow-[0_0_12px_rgba(152,216,216,0.15)]",
  fighting: "hover:border-type-fighting/50 hover:shadow-[0_0_12px_rgba(192,48,40,0.15)]",
  poison: "hover:border-type-poison/50 hover:shadow-[0_0_12px_rgba(160,64,160,0.15)]",
  ground: "hover:border-type-ground/50 hover:shadow-[0_0_12px_rgba(224,192,104,0.15)]",
  flying: "hover:border-type-flying/50 hover:shadow-[0_0_12px_rgba(168,144,240,0.15)]",
  psychic: "hover:border-type-psychic/50 hover:shadow-[0_0_12px_rgba(248,88,136,0.15)]",
  bug: "hover:border-type-bug/50 hover:shadow-[0_0_12px_rgba(168,184,32,0.15)]",
  rock: "hover:border-type-rock/50 hover:shadow-[0_0_12px_rgba(184,160,56,0.15)]",
  ghost: "hover:border-type-ghost/50 hover:shadow-[0_0_12px_rgba(112,88,152,0.15)]",
  dragon: "hover:border-type-dragon/50 hover:shadow-[0_0_12px_rgba(112,56,248,0.15)]",
  dark: "hover:border-type-dark/50 hover:shadow-[0_0_12px_rgba(112,88,72,0.15)]",
  steel: "hover:border-type-steel/50 hover:shadow-[0_0_12px_rgba(184,184,208,0.15)]",
  fairy: "hover:border-type-fairy/50 hover:shadow-[0_0_12px_rgba(238,153,172,0.15)]",
};

export function PokemonSlotCard({
  slot,
  pokemonId,
  onClick,
  isSelected,
  index,
}: PokemonSlotCardProps) {
  // Query Pokemon details to retrieve the correct ID (bypassing default 0) and types
  const { data: detail } = usePokemonDetail(slot?.pokname || undefined);
  const id = detail?.pokemon_id ?? pokemonId ?? 0;
  const primaryType = detail?.types?.[0]?.toLowerCase() ?? "normal";
  const typeGlow = TYPE_GLOWS[primaryType] || TYPE_GLOWS.normal;

  if (!slot || !slot.pokname) {
    return (
      <button
        onClick={onClick}
        type="button"
        aria-label={`Add Pokémon to slot ${index + 1}`}
        className="w-full aspect-square rounded-2xl bg-bg-card/25 border-2 border-dashed border-border/50 hover:border-accent/60 focus-visible:ring-2 focus-visible:ring-accent flex flex-col items-center justify-center gap-2 transition-all duration-300 group cursor-pointer"
      >
        <span className="font-display text-2xl text-text-muted group-hover:text-accent transition-colors">
          +
        </span>
        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Slot {index + 1}</span>
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      type="button"
      aria-label={`Edit ${displayName(slot.pokname)} in slot ${index + 1}`}
      className={`w-full rounded-2xl bg-bg-card/45 border-2 p-4 flex flex-col items-center gap-3 transition-all duration-300 cursor-pointer focus-visible:ring-2 focus-visible:ring-accent outline-none ${
        isSelected
          ? "border-accent shadow-[0_0_18px_rgba(207,162,64,0.18)] bg-bg-card/75"
          : `border-border/60 ${typeGlow}`
      }`}
    >
      <div className="relative">
        {id !== 0 ? (
          <img
            src={spriteUrl(id, slot.shiny)}
            alt={slot.pokname}
            className="w-16 h-16 object-contain"
            loading="lazy"
          />
        ) : (
          <div className="w-16 h-16 flex items-center justify-center text-text-muted">
            ❓
          </div>
        )}
        {slot.shiny && (
          <span className="absolute -top-2 -right-2 text-xs" title="Shiny">✨</span>
        )}
      </div>

      <div className="text-center w-full min-w-0">
        <div className="font-display text-xs font-bold truncate text-text-primary capitalize tracking-wide">
          {displayName(slot.pokname)}
        </div>
        {slot.poknick && slot.poknick !== "None" ? (
          <div className="text-[10px] text-text-muted truncate mt-0.5 italic">
            "{slot.poknick}"
          </div>
        ) : (
          <div className="text-[9px] text-text-muted/60 uppercase tracking-wider mt-0.5 font-bold">
            Level {slot.pokelevel}
          </div>
        )}
      </div>

      {detail?.types && (
        <div className="flex gap-1 justify-center mt-1">
          {detail.types.map((t) => (
            <TypeBadge key={t} type={t} size="sm" />
          ))}
        </div>
      )}
    </button>
  );
}
