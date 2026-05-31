import { create } from "zustand";
import type { Team, PokemonSlot } from "../types";
import { updateTeam } from "../api/teams";

interface TeamStore {
  editingTeam: Team | null;
  selectedSlot: number | null;
  isDirty: boolean;
  isSaving: boolean;
  saveTimer: ReturnType<typeof setTimeout> | null;

  setEditingTeam: (team: Team | null) => void;
  updatePokemonSlot: (slot: number, pokemon: PokemonSlot) => void;
  removePokemonSlot: (slot: number) => void;
  setSelectedSlot: (slot: number | null) => void;
  triggerSave: () => void;
  clearEditing: () => void;
}

export const useTeamStore = create<TeamStore>((set, get) => ({
  editingTeam: null,
  selectedSlot: null,
  isDirty: false,
  isSaving: false,
  saveTimer: null,

  setEditingTeam: (team) => {
    const prev = get().saveTimer;
    if (prev) clearTimeout(prev);
    set({ editingTeam: team, selectedSlot: null, isDirty: false, isSaving: false, saveTimer: null });
  },

  updatePokemonSlot: (slotIndex, pokemon) => {
    const { editingTeam } = get();
    if (!editingTeam) return;

    const newPokemon = [...editingTeam.pokemon];
    newPokemon[slotIndex] = pokemon;
    set({
      editingTeam: { ...editingTeam, pokemon: newPokemon },
      isDirty: true,
    });
    get().triggerSave();
  },

  removePokemonSlot: (slotIndex) => {
    const { editingTeam } = get();
    if (!editingTeam) return;

    const newPokemon = editingTeam.pokemon.filter((_, i) => i !== slotIndex);
    set({
      editingTeam: { ...editingTeam, pokemon: newPokemon },
      isDirty: true,
      selectedSlot: null,
    });
    get().triggerSave();
  },

  setSelectedSlot: (slot) => set({ selectedSlot: slot }),

  triggerSave: () => {
    const prev = get().saveTimer;
    if (prev) clearTimeout(prev);

    const timer = setTimeout(async () => {
      const { editingTeam, isDirty } = get();
      if (!editingTeam || !isDirty) return;

      set({ isSaving: true });
      try {
        await updateTeam(editingTeam.name, editingTeam.pokemon);
        set({ isDirty: false });
      } catch (err) {
        console.error("[teamStore] Save failed:", err);
      } finally {
        set({ isSaving: false });
      }
    }, 1000);

    set({ saveTimer: timer });
  },

  clearEditing: () => {
    const prev = get().saveTimer;
    if (prev) clearTimeout(prev);
    set({ editingTeam: null, selectedSlot: null, isDirty: false, isSaving: false, saveTimer: null });
  },
}));
