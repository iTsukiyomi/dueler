import { spriteUrl, displayName } from "../../utils/pokemon";
import type { PokemonSlot } from "../../types";

interface PokemonSlotCardProps {
  slot?: PokemonSlot;
  pokemonId?: number;
  onClick: () => void;
  isSelected?: boolean;
  index: number;
}

export function PokemonSlotCard({
  slot,
  pokemonId,
  onClick,
  isSelected,
  index,
}: PokemonSlotCardProps) {
  if (!slot || !slot.pokname) {
    return (
      <button
        onClick={onClick}
        className="w-full aspect-square rounded-2xl bg-bg-card border-2 border-dashed border-border hover:border-accent/50 flex flex-col items-center justify-center gap-2 transition-all group"
      >
        <span className="text-3xl text-text-muted group-hover:text-accent transition-colors">
          +
        </span>
        <span className="text-xs text-text-muted">Slot {index + 1}</span>
      </button>
    );
  }

  const id = pokemonId ?? 0;

  return (
    <button
      onClick={onClick}
      className={`w-full rounded-2xl bg-bg-card border-2 p-3 flex flex-col items-center gap-2 transition-all ${
        isSelected
          ? "border-accent shadow-[0_0_15px_rgba(230,57,70,0.2)]"
          : "border-border hover:border-border-light"
      }`}
    >
      <div className="relative">
        <img
          src={spriteUrl(id, slot.shiny)}
          alt={slot.pokname}
          className="w-16 h-16 object-contain"
          loading="lazy"
        />
        {slot.shiny && (
          <span className="absolute -top-1 -right-1 text-xs">✨</span>
        )}
      </div>
      <div className="text-center">
        <div className="text-xs font-semibold truncate w-full">
          {displayName(slot.pokname)}
        </div>
        {slot.poknick && slot.poknick !== "None" && (
          <div className="text-[10px] text-text-muted truncate w-full">
            "{slot.poknick}"
          </div>
        )}
      </div>
    </button>
  );
}
