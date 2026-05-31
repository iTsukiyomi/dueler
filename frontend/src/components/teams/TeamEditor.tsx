import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeamStore } from "../../stores/teamStore";
import { useTeamDetail, useActivateTeam, useDeleteTeam, useRenameTeam } from "../../hooks/useTeams";
import { PokemonSlotCard } from "./PokemonSlot";
import { PokemonSearch } from "./PokemonSearch";
import { PokemonEditor } from "../pokemon/PokemonEditor";
import { defaultPokemonSlot } from "../../types";
import type { GameDataPokemon } from "../../types";

export function TeamEditor() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const decodedName = name ? decodeURIComponent(name) : "";

  const { data: teamDetail, isLoading } = useTeamDetail(decodedName);
  const activateTeam = useActivateTeam();
  const deleteTeam = useDeleteTeam();
  const renameTeam = useRenameTeam();

  const {
    editingTeam,
    selectedSlot,
    isDirty,
    isSaving,
    setEditingTeam,
    setSelectedSlot,
    updatePokemonSlot,
    removePokemonSlot,
    clearEditing,
  } = useTeamStore();

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState("");

  // Sync loaded team to Zustand store
  useEffect(() => {
    if (teamDetail) {
      setEditingTeam(teamDetail);
      setTempName(teamDetail.name);
    }
    return () => {
      clearEditing();
    };
  }, [teamDetail, setEditingTeam, clearEditing]);

  if (isLoading || !editingTeam) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const pokemonList = editingTeam.pokemon || [];
  const totalSlots = pokemonList.length;

  const handleSlotClick = (index: number) => {
    setSelectedSlot(index);
    if (index >= totalSlots) {
      setIsSearchOpen(true);
    }
  };

  const handleSelectPokemon = (poke: GameDataPokemon) => {
    if (selectedSlot === null) return;
    const newSlot = {
      ...defaultPokemonSlot(),
      pokname: poke.identifier,
      poknick: "None",
      ability_index: poke.abilities?.[0]?.slot ?? 1,
    };
    updatePokemonSlot(selectedSlot, newSlot);
  };

  const handleRename = () => {
    if (!tempName.trim() || tempName.trim().toLowerCase() === editingTeam.name.toLowerCase()) {
      setIsEditingName(false);
      return;
    }
    renameTeam.mutate(
      { name: editingTeam.name, newName: tempName.trim() },
      {
        onSuccess: () => {
          setIsEditingName(false);
          navigate(`/dashboard/teams/${encodeURIComponent(tempName.trim().toLowerCase())}`, { replace: true });
        },
        onError: () => {
          setTempName(editingTeam.name);
        },
      }
    );
  };

  const handleActivate = () => {
    activateTeam.mutate(editingTeam.name);
  };

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${editingTeam.name}"?`)) {
      deleteTeam.mutate(editingTeam.name, {
        onSuccess: () => navigate("/dashboard/teams"),
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/dashboard/teams")}
            className="p-2 rounded-xl bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors"
          >
            ← Back
          </button>
          <div className="flex items-center gap-3">
            {isEditingName ? (
              <input
                type="text"
                value={tempName}
                onChange={(e) => setTempName(e.target.value)}
                onBlur={handleRename}
                onKeyDown={(e) => e.key === "Enter" && handleRename()}
                className="text-2xl font-bold bg-bg-secondary border border-border px-3 py-1 rounded-xl outline-none focus:border-accent capitalize"
                maxLength={32}
                autoFocus
              />
            ) : (
              <h1
                onClick={() => setIsEditingName(true)}
                className="text-2xl font-bold capitalize cursor-pointer hover:text-accent transition-colors flex items-center gap-2 group"
              >
                {editingTeam.name}
                <span className="text-xs text-text-muted opacity-0 group-hover:opacity-100 transition-opacity font-normal">
                  (Edit)
                </span>
              </h1>
            )}
            <div className="flex items-center gap-2 text-xs">
              {isSaving ? (
                <span className="text-text-muted flex items-center gap-1.5">
                  <span className="w-2 h-2 border border-text-muted border-t-transparent rounded-full animate-spin" />
                  Saving...
                </span>
              ) : isDirty ? (
                <span className="text-warning">Unsaved changes</span>
              ) : (
                <span className="text-emerald-400">● Saved</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleActivate}
            disabled={activateTeam.isPending}
            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium text-sm transition-colors disabled:opacity-50"
          >
            Activate Team
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteTeam.isPending}
            className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500 hover:text-white text-rose-400 font-medium text-sm transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: 6 Slots */}
        <div className="lg:col-span-7 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-text-muted mb-2">
            Team Members
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, idx) => {
              const hasSlot = idx < totalSlots;
              const slot = hasSlot ? pokemonList[idx] : undefined;
              const isSelected = selectedSlot === idx;

              // We only want to show filled slots, plus one empty slot at the end to add next Pokémon
              if (idx > totalSlots) return null;

              // We also need the form ID for sprite loading
              // Note: the teamDetail from server includes pokemon list. We don't have the details for newly added pokemon
              // until we query details, but we can look up their ids if they exist.
              // To get pokemon ID, we'll try to guess/retrieve it if slot exists.
              return (
                <PokemonSlotCard
                  key={idx}
                  slot={slot}
                  pokemonId={slot?.id}
                  onClick={() => handleSlotClick(idx)}
                  isSelected={isSelected}
                  index={idx}
                />
              );
            })}
          </div>
        </div>

        {/* Right Side: Slot Editor Panel */}
        <div className="lg:col-span-5">
          {selectedSlot !== null && selectedSlot < totalSlots ? (
            <PokemonEditor
              slot={pokemonList[selectedSlot]}
              onChange={(updated) => updatePokemonSlot(selectedSlot, updated)}
              onRemove={() => removePokemonSlot(selectedSlot)}
              onChangePokemon={() => setIsSearchOpen(true)}
            />
          ) : (
            <div className="rounded-2xl border border-border/40 bg-bg-card/30 p-8 text-center text-text-muted">
              <div className="text-4xl mb-3">👈</div>
              <div className="font-semibold">Select a Pokémon</div>
              <div className="text-xs mt-1">
                Click any active slot to customize stats, moves, nature, and item, or click the empty slot to add a member.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search Modal */}
      <PokemonSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelect={handleSelectPokemon}
      />
    </div>
  );
}
