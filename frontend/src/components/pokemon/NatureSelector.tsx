import { useState } from "react";
import type { GameDataNature } from "../../types";

interface NatureSelectorProps {
  current: string;
  natures: GameDataNature[];
  onChange: (nature: string) => void;
}

const STAT_LABELS: Record<string, string> = {
  hp: "HP",
  atk: "Atk",
  def: "Def",
  spa: "SpA",
  spd: "SpD",
  spe: "Spe",
};

export function NatureSelector({
  current,
  natures,
  onChange,
}: NatureSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedNature = natures.find(
    (n) => n.identifier.toLowerCase() === current.toLowerCase(),
  );

  const getStatChangeText = (nature: GameDataNature) => {
    if (!nature.increases_stat || !nature.decreases_stat) return "Neutral";
    return `+${STAT_LABELS[nature.increases_stat]} / -${STAT_LABELS[nature.decreases_stat]}`;
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-bold uppercase tracking-wider text-text-muted">
        Nature
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-3.5 rounded-xl bg-bg-secondary/40 border border-border/60 hover:border-border text-left transition-all"
        >
          <div>
            <span className="text-sm font-bold capitalize text-text-primary">
              {selectedNature ? selectedNature.display_name : current}
            </span>
            <span className="ml-3 text-[10px] font-semibold text-text-muted">
              {selectedNature ? getStatChangeText(selectedNature) : ""}
            </span>
          </div>
          <span className="text-text-muted">{isOpen ? "▲" : "▼"}</span>
        </button>

        {isOpen && (
          <div className="absolute z-30 mt-2 w-full max-h-72 overflow-y-auto rounded-2xl bg-bg-card border border-border p-2 shadow-2xl backdrop-blur-xl animate-fadeIn">
            <div className="grid grid-cols-2 gap-1.5">
              {natures.map((nature) => {
                const isCurrent =
                  nature.identifier.toLowerCase() === current.toLowerCase();
                const isNeutral = !nature.increases_stat || !nature.decreases_stat;

                return (
                  <button
                    key={nature.identifier}
                    type="button"
                    onClick={() => {
                      onChange(nature.identifier);
                      setIsOpen(false);
                    }}
                    className={`flex flex-col items-start p-2.5 rounded-xl border text-left transition-all ${
                      isCurrent
                        ? "bg-accent/15 border-accent text-accent"
                        : "bg-bg-secondary/20 border-border/30 hover:border-border/80 text-text-secondary hover:text-text-primary"
                    }`}
                  >
                    <span className="text-xs font-bold capitalize">
                      {nature.display_name}
                    </span>
                    <span
                      className={`text-[9px] font-semibold mt-0.5 ${
                        isCurrent
                          ? "text-accent-glow"
                          : isNeutral
                            ? "text-text-muted"
                            : "text-text-secondary"
                      }`}
                    >
                      {isNeutral ? (
                        "Neutral"
                      ) : (
                        <>
                          <span className="text-emerald-400">
                            +{STAT_LABELS[nature.increases_stat!]}
                          </span>
                          {" / "}
                          <span className="text-rose-400">
                            -{STAT_LABELS[nature.decreases_stat!]}
                          </span>
                        </>
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
