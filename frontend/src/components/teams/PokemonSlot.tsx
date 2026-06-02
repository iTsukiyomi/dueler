import React from "react";
import { spriteUrl, displayName } from "../../utils/pokemon";
import { usePokemonDetail } from "../../hooks/usePokemonData";
import { TypeBadge } from "../ui/TypeBadge";
import type { PokemonSlot } from "../../types";
import { Sparkles, HelpCircle, Plus } from "lucide-react";

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
  const { data: detail } = usePokemonDetail(slot?.pokname || undefined);
  const id = detail?.pokemon_id ?? pokemonId ?? 0;
  const primaryType = detail?.types?.[0]?.toLowerCase() ?? "normal";

  if (!slot || !slot.pokname) {
    return (
      <button
        onClick={onClick}
        type="button"
        className={`w-full aspect-square bg-bg-raised border border-dashed border-border-default hover:border-poke-yellow hover:bg-bg-float flex flex-col items-center justify-center gap-2 transition-all duration-200 group cursor-pointer`}
        style={{ borderRadius: "var(--radius-lg)" }}
      >
        <div className="w-8 h-8 rounded-full bg-bg-overlay border border-border-subtle flex items-center justify-center text-text-secondary group-hover:text-poke-yellow group-hover:border-border-default transition-colors">
          <Plus className="w-4 h-4" />
        </div>
        <span className="font-rajdhani text-[10px] font-bold uppercase tracking-widest text-text-muted">
          Slot {index + 1}
        </span>
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      type="button"
      className={`w-full bg-bg-raised border p-4 flex flex-col items-center gap-3 transition-all duration-200 cursor-pointer ${
        isSelected
          ? "border-poke-yellow shadow-[0_0_18px_var(--poke-yellow-glow)] bg-bg-float"
          : "border-border-default hover:border-border-bright"
      }`}
      style={{
        borderRadius: "var(--radius-lg)",
        "--type-color": `var(--type-${primaryType})`
      } as React.CSSProperties}
    >
      <div className="relative w-16 h-16 flex items-center justify-center">
        {id !== 0 ? (
          <img
            src={spriteUrl(id, slot.shiny)}
            alt={slot.pokname}
            className="w-16 h-16 object-contain drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]"
            style={{ imageRendering: "pixelated" }}
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%233D5068'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3C/svg%3E";
            }}
          />
        ) : (
          <HelpCircle className="w-10 h-10 text-text-muted" />
        )}
        {slot.shiny && (
          <span title="Shiny Variant" className="absolute -top-1 -right-1 flex">
            <Sparkles className="w-4 h-4 text-poke-yellow" />
          </span>
        )}
      </div>

      <div className="text-center w-full min-w-0">
        <div className="font-rajdhani text-xs font-bold truncate text-text-primary capitalize tracking-wide">
          {displayName(slot.pokname)}
        </div>
        {slot.poknick && slot.poknick !== "None" ? (
          <div className="font-sans text-[10px] text-text-secondary truncate mt-0.5 italic">
            "{slot.poknick}"
          </div>
        ) : (
          <div className="mono text-[9px] text-text-muted uppercase tracking-wider mt-0.5">
            Level {slot.pokelevel}
          </div>
        )}
      </div>

      {detail?.types && (
        <div className="flex gap-1 justify-center mt-1 flex-wrap">
          {detail.types.map((t) => (
            <TypeBadge key={t} type={t} size="sm" />
          ))}
        </div>
      )}
    </button>
  );
}

export default PokemonSlotCard;
