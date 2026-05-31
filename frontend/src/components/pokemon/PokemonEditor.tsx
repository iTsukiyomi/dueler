import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import type { PokemonSlot, GameDataPokemon, GameDataNature } from "../../types";
import { usePokemonDetail, useNatures } from "../../hooks/usePokemonData";
import { TypeBadge } from "../ui/TypeBadge";
import { StatSlider } from "./StatSlider";
import { MoveSelector } from "./MoveSelector";
import { NatureSelector } from "./NatureSelector";
import { ItemSelector } from "./ItemSelector";
import { spriteUrl, displayName, calcStat, totalEvs } from "../../utils/pokemon";

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
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl bg-bg-card border border-border overflow-hidden"
    >
      {/* Header */}
      <div className="p-5 border-b border-border flex items-start gap-4">
        <div className="relative group cursor-pointer" onClick={onChangePokemon}>
          <img
            src={spriteUrl(detail?.pokemon_id ?? 0, slot.shiny)}
            alt={slot.pokname}
            className="w-20 h-20 object-contain"
          />
          <div className="absolute inset-0 bg-black/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-xs font-medium">
            Change
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold">{displayName(slot.pokname)}</h3>
            {slot.shiny && <span>✨</span>}
          </div>
          {detail && (
            <div className="flex gap-1 mb-2">
              {detail.types.map((t) => (
                <TypeBadge key={t} type={t} size="md" />
              ))}
            </div>
          )}
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={slot.poknick === "None" ? "" : slot.poknick}
              onChange={(e) => updateField("poknick", e.target.value || "None")}
              placeholder="Nickname"
              className="px-2 py-1 rounded-lg bg-bg-secondary border border-border text-xs text-text-primary w-28 outline-none focus:border-accent transition-colors"
            />
            <label className="flex items-center gap-1.5 text-xs text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={slot.shiny}
                onChange={(e) => updateField("shiny", e.target.checked)}
                className="accent-accent"
              />
              Shiny
            </label>
          </div>
        </div>
        <button
          onClick={onRemove}
          className="text-text-muted hover:text-danger text-sm transition-colors"
          title="Remove from team"
        >
          🗑️
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors ${
              activeTab === tab
                ? "text-accent border-b-2 border-accent"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-5">
        {activeTab === "stats" && (
          <div className="space-y-4">
            {/* EV total bar */}
            <div className="flex items-center justify-between text-xs text-text-muted mb-2">
              <span>EVs: {evTotal}/510</span>
              <span className={evRemaining === 0 ? "text-success" : "text-warning"}>
                {evRemaining} remaining
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-bg-secondary overflow-hidden mb-4">
              <div
                className={`h-full rounded-full transition-all ${evTotal > 510 ? "bg-danger" : "bg-accent"}`}
                style={{ width: `${Math.min(100, (evTotal / 510) * 100)}%` }}
              />
            </div>

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
          <div className="space-y-4">
            <ItemSelector
              current={slot.hitem}
              onChange={(item) => updateField("hitem", item)}
            />

            {detail?.abilities && detail.abilities.length > 0 && (
              <div>
                <label className="block text-xs text-text-muted mb-2">
                  Ability
                </label>
                <div className="grid gap-2">
                  {detail.abilities.map((ab, i) => (
                    <button
                      key={ab.ability_id}
                      onClick={() => updateField("ability_index", ab.slot)}
                      className={`px-3 py-2 rounded-xl text-sm text-left transition-all ${
                        slot.ability_index === ab.slot
                          ? "bg-accent/15 border border-accent/30 text-accent"
                          : "bg-bg-secondary border border-border text-text-secondary hover:border-border-light"
                      }`}
                    >
                      <span className="font-medium">{ab.display_name}</span>
                      {ab.is_hidden && (
                        <span className="ml-2 text-[10px] text-text-muted uppercase">
                          Hidden
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs text-text-muted mb-2">Level</label>
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
                className="w-20 px-3 py-2 rounded-xl bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent font-mono"
              />
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-2">
                Happiness ({slot.happiness})
              </label>
              <input
                type="range"
                min={0}
                max={255}
                value={slot.happiness}
                onChange={(e) => updateField("happiness", parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-2">Gender</label>
              <div className="flex gap-2">
                {["", "Male", "Female"].map((g) => (
                  <button
                    key={g}
                    onClick={() => updateField("gender", g)}
                    className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                      slot.gender === g
                        ? "bg-accent/15 border border-accent/30 text-accent"
                        : "bg-bg-secondary border border-border text-text-muted hover:text-text-secondary"
                    }`}
                  >
                    {g || "None"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
