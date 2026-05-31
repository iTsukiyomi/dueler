import { useState } from "react";
import { useMoveSearch } from "../../hooks/usePokemonData";
import { SearchInput } from "../ui/SearchInput";
import { TypeBadge } from "../ui/TypeBadge";
import { displayName } from "../../utils/pokemon";
import type { GameDataMove } from "../../types";

interface MoveSelectorProps {
  pokemonIdentifier: string;
  moves: string[];
  onChange: (moves: string[]) => void;
}

const DAMAGE_CLASS_ICONS: Record<string, string> = {
  physical: "⚔️",
  special: "🌀",
  status: "🛡️",
};

export function MoveSelector({
  pokemonIdentifier,
  moves,
  onChange,
}: MoveSelectorProps) {
  const [activeSlot, setActiveSlot] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { data: results, isLoading } = useMoveSearch(searchQuery, pokemonIdentifier);

  const handleSelectMove = (move: GameDataMove) => {
    if (activeSlot === null) return;
    const newMoves = [...moves];
    newMoves[activeSlot] = move.identifier;
    onChange(newMoves);
    setActiveSlot(null);
    setSearchQuery("");
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-text-muted mb-3">
          Movesets
        </label>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, idx) => {
            const moveName = moves[idx] || "tackle";
            const isEditing = activeSlot === idx;

            return (
              <button
                key={idx}
                onClick={() => {
                  setActiveSlot(isEditing ? null : idx);
                  setSearchQuery("");
                }}
                className={`flex flex-col items-start gap-1 p-4 rounded-xl border text-left transition-all relative overflow-hidden ${
                  isEditing
                    ? "bg-accent/10 border-accent shadow-[0_0_12px_rgba(16,185,129,0.15)] text-text-primary"
                    : "bg-bg-secondary/40 border-border/60 hover:border-border text-text-secondary hover:text-text-primary"
                }`}
              >
                <div className="text-[10px] uppercase font-semibold text-text-muted">
                  Slot {idx + 1}
                </div>
                <div className="text-sm font-bold capitalize mt-1">
                  {moveName.replace(/-/g, " ")}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {activeSlot !== null && (
        <div className="border border-border/80 rounded-2xl bg-bg-secondary/30 p-4 transition-all animate-fadeIn">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase">
              Choose Move for Slot {activeSlot + 1}
            </span>
            <button
              onClick={() => setActiveSlot(null)}
              className="text-[10px] text-text-muted hover:text-text-primary uppercase tracking-wider font-semibold"
            >
              Close
            </button>
          </div>

          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search moves..."
            autoFocus
            isLoading={isLoading}
          />

          <div className="mt-4 space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {results?.map((move) => (
              <button
                key={move.id}
                onClick={() => handleSelectMove(move)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-bg-card/40 hover:bg-bg-card border border-border/40 hover:border-border/85 transition-all text-left group"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="text-lg"
                    title={move.damage_class}
                  >
                    {DAMAGE_CLASS_ICONS[move.damage_class.toLowerCase()] || "❓"}
                  </span>
                  <div>
                    <span className="text-sm font-bold text-text-primary group-hover:text-accent transition-colors">
                      {displayName(move.identifier)}
                    </span>
                    <div className="flex items-center gap-3 mt-1 text-[10px] text-text-muted">
                      {move.power && <span>Power: {move.power}</span>}
                      <span>PP: {move.pp}</span>
                      {move.accuracy && <span>Acc: {move.accuracy}%</span>}
                    </div>
                  </div>
                </div>
                <TypeBadge type={move.type_name} size="sm" />
              </button>
            ))}

            {results?.length === 0 && !isLoading && (
              <div className="text-center py-6 text-text-muted text-xs">
                No learnable moves found matching "{searchQuery}"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
