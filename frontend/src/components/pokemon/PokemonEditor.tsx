import React, { useState, useCallback } from "react";
import { motion } from "framer-motion";
import type { PokemonSlot, GameDataPokemon, GameDataNature } from "../../types";
import { usePokemonDetail, useNatures } from "../../hooks/usePokemonData";
import { TypeBadge } from "../ui/TypeBadge";
import { StatSlider } from "./StatSlider";
import { MoveSelector } from "./MoveSelector";
import { NatureSelector } from "./NatureSelector";
import { ItemSelector } from "./ItemSelector";
import { spriteUrl, displayName, calcStat, totalEvs } from "../../utils/pokemon";
import { Trash2, Sparkles, AlertCircle, Heart } from "lucide-react";

interface PokemonEditorProps {
  slot: PokemonSlot;
  onChange: (updated: PokemonSlot) => void;
  onChangePokemon: () => void;
  onRemove: () => void;
}

export function PokemonEditor({
  slot,
  onChange,
  onChangePokemon,
  onRemove,
}: PokemonEditorProps) {
  const { data: detail } = usePokemonDetail(slot.pokname || undefined);
  const { data: natures } = useNatures();
  const [activeTab, setActiveTab] = useState<"stats" | "moves" | "info">("stats");

  const currentNature = natures?.find(
    (n) => n.identifier.toLowerCase() === slot.nature.toLowerCase(),
  );

  const updateField = useCallback(
    <K extends keyof PokemonSlot>(field: K, value: PokemonSlot[K]) => {
      onChange({ ...slot, [field]: value });
    },
    [slot, onChange],
  );

  const evTotal = totalEvs(slot);
  const evRemaining = Math.max(0, 510 - evTotal);

  const tabs = ["stats", "moves", "info"] as const;

  return (
    <div className="bg-transparent overflow-hidden">
      {/* Header Info */}
      <div className="p-5 border-b border-border-subtle flex items-start gap-4">
        <div className="relative group cursor-pointer shrink-0" onClick={onChangePokemon}>
          <img
            src={spriteUrl(detail?.pokemon_id ?? 0, slot.shiny)}
            alt={slot.pokname}
            className="w-16 h-16 object-contain drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]"
            style={{ imageRendering: "pixelated" }}
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%233D5068'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3C/svg%3E";
            }}
          />
          <div className="absolute inset-0 bg-black/60 rounded-md opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-[10px] font-bold uppercase tracking-widest text-white">
            Change
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <h3 className="font-display text-sm font-bold text-text-primary uppercase tracking-wide truncate">
              {displayName(slot.pokname)}
            </h3>
            {slot.shiny && <Sparkles className="w-3.5 h-3.5 text-poke-yellow" />}
          </div>
          {detail && (
            <div className="flex gap-1 mb-3">
              {detail.types.map((t) => (
                <TypeBadge key={t} type={t} size="sm" />
              ))}
            </div>
          )}
          <div className="flex items-center gap-3 flex-wrap">
            <input
              type="text"
              value={slot.poknick === "None" ? "" : slot.poknick}
              onChange={(e) => updateField("poknick", e.target.value || "None")}
              placeholder="Enter Nickname"
              className="input py-1 px-2.5 text-xs w-28 uppercase tracking-wide font-semibold"
            />
            <label className="flex items-center gap-1.5 text-xs text-text-secondary cursor-pointer font-semibold select-none font-rajdhani uppercase tracking-wider">
              <input
                type="checkbox"
                checked={slot.shiny}
                onChange={(e) => updateField("shiny", e.target.checked)}
                className="accent-poke-red w-3.5 h-3.5"
              />
              <span>Shiny</span>
            </label>
          </div>
        </div>

        <button
          onClick={onRemove}
          className="btn-icon text-text-muted hover:text-poke-red hover:bg-poke-red/15 hover:border-poke-red/20 transition-all shrink-0"
          title="Remove from squad"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs list layout */}
      <div className="tab-list">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`tab ${activeTab === tab ? "active" : ""}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="pt-5">
        {activeTab === "stats" && (
          <div className="space-y-4">
            {/* EV allocation progress */}
            <div className="bg-bg-overlay/40 border border-border-subtle p-4 rounded">
              <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2 font-rajdhani">
                <span>EV Spread Allocation</span>
                <span className={evRemaining === 0 ? "text-emerald-400 font-mono" : "text-poke-yellow font-mono"}>
                  {evRemaining} / 510 Rem
                </span>
              </div>
              <div className="stat-bar-track">
                <div
                  className={`stat-bar-fill ${evTotal > 510 ? "low" : "high"}`}
                  style={{ 
                    width: `${Math.min(100, (evTotal / 510) * 100)}%`,
                    "--fill-pct": `${Math.min(100, (evTotal / 510) * 100)}%`
                  } as React.CSSProperties}
                />
              </div>
            </div>

            <div className="space-y-3.5">
              {(
                [
                  ["hp", "hpiv", "hpev", "HP"],
                  ["atk", "atkiv", "atkev", "Attack"],
                  ["def", "defiv", "defev", "Defense"],
                  ["spa", "spatkiv", "spatkev", "Sp. Atk"],
                  ["spd", "spdefiv", "spdefev", "Sp. Def"],
                  ["spe", "speediv", "speedev", "Speed"],
                ] as const
              ).map(([statKey, ivKey, evKey, label]) => {
                const baseStat = detail?.base_stats?.[statKey] ?? 0;
                const finalStat = calcStat(
                  statKey,
                  baseStat,
                  slot[ivKey],
                  slot[evKey],
                  slot.pokelevel,
                  currentNature as GameDataNature | undefined,
                );

                return (
                  <StatSlider
                    key={statKey}
                    label={label}
                    baseStat={baseStat}
                    iv={slot[ivKey]}
                    ev={slot[evKey]}
                    finalStat={finalStat}
                    onIvChange={(v) => updateField(ivKey, v)}
                    onEvChange={(v) => {
                      const newTotal = evTotal - slot[evKey] + v;
                      if (newTotal <= 510) updateField(evKey, v);
                    }}
                    nature={currentNature}
                    statKey={statKey}
                  />
                );
              })}
            </div>

            <NatureSelector
              current={slot.nature}
              natures={natures ?? []}
              onChange={(n) => updateField("nature", n)}
            />
          </div>
        )}

        {activeTab === "moves" && (
          <MoveSelector
            pokemonIdentifier={slot.pokname}
            moves={slot.moves}
            onChange={(moves) => updateField("moves", moves)}
          />
        )}

        {activeTab === "info" && (
          <div className="space-y-5">
            <ItemSelector
              current={slot.hitem}
              onChange={(item) => updateField("hitem", item)}
            />

            {detail?.abilities && detail.abilities.length > 0 && (
              <div className="space-y-2">
                <label className="block font-rajdhani text-xs font-bold uppercase tracking-widest text-text-muted">
                  Signature Ability
                </label>
                <div className="grid gap-2">
                  {detail.abilities.map((ab) => (
                    <button
                      key={ab.ability_id}
                      onClick={() => updateField("ability_index", ab.slot)}
                      className={`px-3.5 py-2.5 rounded border text-xs text-left transition-all ${
                        slot.ability_index === ab.slot
                          ? "bg-poke-red-glow border-poke-red text-poke-red font-bold"
                          : "bg-bg-input border-border-subtle text-text-secondary hover:border-border-default"
                      }`}
                    >
                      <span className="font-semibold uppercase font-rajdhani tracking-wider">{ab.display_name}</span>
                      {ab.is_hidden && (
                        <span className="ml-2 text-[9px] text-text-muted uppercase font-mono font-bold">
                          [Hidden]
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-rajdhani text-xs font-bold uppercase tracking-widest text-text-muted mb-2">
                  Level Range
                </label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={slot.pokelevel}
                  onChange={(e) =>
                    updateField(
                      "pokelevel",
                      Math.min(100, Math.max(1, parseInt(e.target.value) || 1)),
                    )
                  }
                  className="input font-mono w-24 text-center"
                />
              </div>

              <div>
                <label className="block font-rajdhani text-xs font-bold uppercase tracking-widest text-text-muted mb-2 flex items-center gap-1">
                  <Heart className="w-3.5 h-3.5 text-poke-red" />
                  <span>Happiness ({slot.happiness})</span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={255}
                  value={slot.happiness}
                  onChange={(e) => updateField("happiness", parseInt(e.target.value))}
                  className="w-full h-1.5 rounded-full bg-border-subtle accent-poke-red outline-none cursor-pointer mt-3"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block font-rajdhani text-xs font-bold uppercase tracking-widest text-text-muted">
                Trainer Gender Registry
              </label>
              <div className="flex gap-2">
                {[
                  ["", "Neutral"],
                  ["Male", "Male"],
                  ["Female", "Female"]
                ].map(([g, label]) => (
                  <button
                    key={g}
                    onClick={() => updateField("gender", g === "Male" ? "-m" : g === "Female" ? "-f" : "")}
                    className={`btn-secondary flex-1 py-2 text-xs ${
                      (slot.gender === "-m" && g === "Male") ||
                      (slot.gender === "-f" && g === "Female") ||
                      ((!slot.gender || slot.gender === "-x" || slot.gender === "None") && g === "")
                        ? "border-poke-blue/40 text-poke-blue bg-poke-blue-glow font-bold"
                        : "text-text-muted border-border-subtle"
                    }`}
                  >
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PokemonEditor;
