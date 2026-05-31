import { useId } from "react";
import type { GameDataNature } from "../../types";

interface StatSliderProps {
  label: string;
  baseStat: number;
  iv: number;
  ev: number;
  finalStat: number;
  onIvChange: (v: number) => void;
  onEvChange: (v: number) => void;
  nature?: GameDataNature;
  statKey: "hp" | "atk" | "def" | "spa" | "spd" | "spe";
}

const STAT_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  hp: { bar: "bg-emerald-500", text: "text-emerald-400", bg: "bg-emerald-500/10" },
  atk: { bar: "bg-amber-500", text: "text-amber-400", bg: "bg-amber-500/10" },
  def: { bar: "bg-blue-500", text: "text-blue-400", bg: "bg-blue-500/10" },
  spa: { bar: "bg-purple-500", text: "text-purple-400", bg: "bg-purple-500/10" },
  spd: { bar: "bg-pink-500", text: "text-pink-400", bg: "bg-pink-500/10" },
  spe: { bar: "bg-cyan-500", text: "text-cyan-400", bg: "bg-cyan-500/10" },
};

export function StatSlider({
  label,
  baseStat,
  iv,
  ev,
  finalStat,
  onIvChange,
  onEvChange,
  nature,
  statKey,
}: StatSliderProps) {
  const ivId = useId();
  const evId = useId();

  // Check nature changes
  const isBoosted = nature?.increases_stat === statKey;
  const isHindered = nature?.decreases_stat === statKey;

  const colors = STAT_COLORS[statKey] || STAT_COLORS.hp;

  const handleEvSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Math.min(252, Math.max(0, parseInt(e.target.value) || 0));
    onEvChange(val);
  };

  const handleIvInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Math.min(31, Math.max(0, parseInt(e.target.value) || 0));
    onIvChange(val);
  };

  const handleEvInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Math.min(252, Math.max(0, parseInt(e.target.value) || 0));
    onEvChange(val);
  };

  return (
    <div className="group/stat bg-bg-secondary/40 border border-border/40 hover:border-border/80 p-4 rounded-xl transition-all duration-300">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold uppercase tracking-wider ${colors.text}`}>
            {label}
          </span>
          {isBoosted && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 flex items-center gap-0.5">
              ▲ +10%
            </span>
          )}
          {isHindered && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 flex items-center gap-0.5">
              ▼ -10%
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-text-muted">Base: {baseStat}</span>
          <span className="text-sm font-extrabold font-mono text-text-primary">
            {finalStat}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* EV Range Slider & bar representation */}
        <div className="md:col-span-8 flex items-center gap-3">
          <span className="text-[10px] font-semibold text-text-muted w-6">EV</span>
          <div className="flex-1 relative flex items-center">
            <input
              type="range"
              id={evId}
              min={0}
              max={252}
              value={ev}
              onChange={handleEvSliderChange}
              className="w-full cursor-pointer h-1.5 rounded bg-bg-primary outline-none accent-accent"
              style={{
                background: `linear-gradient(to right, var(--color-accent) 0%, var(--color-accent) ${(ev / 252) * 100}%, var(--color-bg-primary) ${(ev / 252) * 100}%, var(--color-bg-primary) 100%)`,
              }}
            />
          </div>
          <input
            type="number"
            min={0}
            max={252}
            value={ev}
            aria-label={`${label} EV value`}
            onChange={handleEvInputChange}
            className="w-14 px-2 py-1 rounded bg-bg-primary border border-border/80 text-text-primary text-xs text-center font-mono outline-none focus:border-accent"
          />
        </div>

        {/* IV numerical control */}
        <div className="md:col-span-4 flex items-center justify-end gap-2">
          <span className="text-[10px] font-semibold text-text-muted">IV</span>
          <input
            type="number"
            id={ivId}
            min={0}
            max={31}
            value={iv}
            onChange={handleIvInputChange}
            className="w-12 px-2 py-1 rounded bg-bg-primary border border-border/80 text-text-primary text-xs text-center font-mono outline-none focus:border-accent"
          />
        </div>
      </div>
    </div>
  );
}
