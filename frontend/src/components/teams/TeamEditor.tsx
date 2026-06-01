import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeamStore } from "../../stores/teamStore";
import { useTeamDetail, useActivateTeam, useDeleteTeam, useRenameTeam } from "../../hooks/useTeams";
import { PokemonSlotCard } from "./PokemonSlot";
import { PokemonSearch } from "./PokemonSearch";
import { PokemonEditor } from "../pokemon/PokemonEditor";
import { defaultPokemonSlot } from "../../types";
import type { GameDataPokemon } from "../../types";
import { BorderBeam } from "../ui/BorderBeam";

function TeamEditorSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between border-b border-border/30 pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-20 bg-bg-card/70 rounded-xl" />
          <div className="h-8 w-44 bg-bg-card/85 rounded-lg" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-bg-card/60 rounded-xl" />
          <div className="h-10 w-20 bg-bg-card/60 rounded-xl" />
        </div>
      </div>

      {/* Grid Workspaces Skeleton */}
      <div className="grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7 grid grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-28 bg-bg-card/30 border border-border/30 rounded-2xl" />
          ))}
        </div>
        <div className="lg:col-span-5 h-64 bg-bg-card/30 border border-border/30 rounded-2xl" />
      </div>
    </div>
  );
}

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
    return <TeamEditorSkeleton />;
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
    <div className="space-y-8 w-full select-none">
      {/* Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/30 pb-5">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/dashboard/teams")}
            className="px-3 py-2 rounded-xl bg-bg-secondary border border-border/60 hover:bg-bg-hover text-text-muted hover:text-text-primary text-xs font-bold uppercase tracking-wider transition-all cursor-pointer"
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
                className="text-xl font-bold bg-bg-secondary border border-accent/40 px-3 py-1 rounded-xl outline-none focus:border-accent capitalize w-48 sm:w-64"
                maxLength={32}
                autoFocus
              />
            ) : (
              <h1
                onClick={() => setIsEditingName(true)}
                className="text-xl sm:text-2xl font-display font-black capitalize cursor-pointer hover:text-accent transition-colors flex items-center gap-2 group tracking-wide"
              >
                {editingTeam.name}
                <span className="text-[10px] text-text-muted opacity-0 group-hover:opacity-100 transition-opacity font-bold uppercase tracking-widest mt-1">
                  (Edit)
                </span>
              </h1>
            )}
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider">
              {isSaving ? (
                <span className="text-text-muted flex items-center gap-1.5 animate-pulse">
                  <span className="w-2 h-2 border border-text-muted border-t-transparent rounded-full animate-spin" />
                  Saving
                </span>
              ) : isDirty ? (
                <span className="text-warning">● Unsaved</span>
              ) : (
                <span className="text-emerald-400">● Synced</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleActivate}
            disabled={activateTeam.isPending}
            className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-bg-primary font-display font-bold text-xs uppercase tracking-widest transition-all disabled:opacity-50 cursor-pointer"
          >
            Activate
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteTeam.isPending}
            className="px-4 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500 hover:text-bg-primary text-rose-400 font-display font-bold text-xs uppercase tracking-widest transition-all cursor-pointer"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: 6 Slots Grid */}
        <div className="lg:col-span-7 space-y-4">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2">
            Team Members
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, idx) => {
              const hasSlot = idx < totalSlots;
              const slot = hasSlot ? pokemonList[idx] : undefined;
              const isSelected = selectedSlot === idx;

              // Only show filled slots + 1 empty slot at end
              if (idx > totalSlots) return null;

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
            <div className="relative rounded-3xl bg-bg-card/25 border border-border/70 p-6 overflow-hidden group">
              <BorderBeam duration={5} borderWidth={1.5} />
              <PokemonEditor
                slot={pokemonList[selectedSlot]}
                onChange={(updated) => updatePokemonSlot(selectedSlot, updated)}
                onRemove={() => removePokemonSlot(selectedSlot)}
                onChangePokemon={() => setIsSearchOpen(true)}
              />
            </div>
          ) : (
            <div className="rounded-3xl border border-border/50 bg-bg-card/25 p-8 text-center text-text-muted space-y-3">
              <div className="text-4xl select-none">👈</div>
              <div className="font-display text-sm font-bold text-text-secondary">Select Pokémon Slot</div>
              <p className="text-[10px] font-medium leading-relaxed max-w-xs mx-auto">
                Click any slot card to customize statistics, movepools, and held items. Click empty slot to draft a new fighter.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Search Modal overlay */}
      <PokemonSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelect={handleSelectPokemon}
      />
    </div>
  );
}

export default TeamEditor;
