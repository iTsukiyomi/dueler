import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeamStore } from "../../stores/teamStore";
import { useTeamDetail, useActivateTeam, useDeleteTeam, useRenameTeam } from "../../hooks/useTeams";
import { PokemonSlotCard } from "./PokemonSlot";
import { PokemonSearch } from "./PokemonSearch";
import { PokemonEditor } from "../pokemon/PokemonEditor";
import { defaultPokemonSlot } from "../../types";
import type { GameDataPokemon } from "../../types";
import { 
  ArrowLeft, 
  Trash2, 
  Check, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Edit3, 
  Sliders, 
  HelpCircle,
  FolderOpen
} from "lucide-react";

function TeamEditorSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      <div className="flex items-center justify-between border-b border-border-subtle pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-20 bg-bg-raised rounded" />
          <div className="h-8 w-44 bg-bg-raised rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-bg-raised rounded" />
          <div className="h-10 w-20 bg-bg-raised rounded" />
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7 grid grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-28 bg-bg-raised border border-border-subtle rounded" />
          ))}
        </div>
        <div className="lg:col-span-5 h-64 bg-bg-raised border border-border-subtle rounded" />
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/dashboard/teams")}
            className="btn-secondary py-2 px-3"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Squads</span>
          </button>
          
          <div className="flex flex-col">
            <div className="mono text-[10px] text-text-muted uppercase tracking-widest mb-0.5">
              Terminal / Battle Squads / Editor
            </div>
            <div className="flex items-center gap-3">
              {isEditingName ? (
                <input
                  type="text"
                  value={tempName}
                  onChange={(e) => setTempName(e.target.value)}
                  onBlur={handleRename}
                  onKeyDown={(e) => e.key === "Enter" && handleRename()}
                  className="input py-1 text-sm font-bold w-48 sm:w-64 uppercase tracking-wider"
                  maxLength={32}
                  autoFocus
                />
              ) : (
                <h1
                  onClick={() => setIsEditingName(true)}
                  className="text-xl sm:text-2xl font-display font-black capitalize cursor-pointer hover:text-poke-yellow transition-colors flex items-center gap-2 group tracking-wide uppercase"
                >
                  {editingTeam.name}
                  <Edit3 className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                </h1>
              )}
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider font-rajdhani">
                {isSaving ? (
                  <span className="text-text-muted flex items-center gap-1.5 animate-pulse">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Saving
                  </span>
                ) : isDirty ? (
                  <span className="text-poke-yellow flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Unsaved
                  </span>
                ) : (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Synced
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleActivate}
            disabled={activateTeam.isPending}
            className="btn-secondary border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
          >
            <Check className="w-4 h-4" />
            <span>Activate</span>
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteTeam.isPending}
            className="btn-danger"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: 6 Slots Grid */}
        <div className="lg:col-span-7 space-y-4">
          <h2 className="font-rajdhani text-xs font-bold uppercase tracking-widest text-text-muted mb-2 border-b border-border-subtle pb-1">
            Squad Members
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
            <div className="card p-4 border-l-2 border-poke-red">
              <PokemonEditor
                slot={pokemonList[selectedSlot]}
                onChange={(updated) => updatePokemonSlot(selectedSlot, updated)}
                onRemove={() => removePokemonSlot(selectedSlot)}
                onChangePokemon={() => setIsSearchOpen(true)}
              />
            </div>
          ) : (
            <div className="card p-8 text-center text-text-muted flex flex-col items-center justify-center space-y-4 border-dashed">
              <div className="w-12 h-12 rounded-full bg-bg-overlay border border-border-subtle flex items-center justify-center text-text-secondary">
                <Sliders className="w-6 h-6 text-text-muted" />
              </div>
              <div>
                <h3 className="font-display text-sm font-bold text-text-secondary uppercase tracking-wide">
                  Configure Member Slot
                </h3>
                <p className="font-sans text-xs text-text-muted leading-relaxed mt-2 max-w-xs mx-auto">
                  Click any filled slot card to customize statistics, movepools, and held items. Click an empty slot to draft a new fighter.
                </p>
              </div>
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
