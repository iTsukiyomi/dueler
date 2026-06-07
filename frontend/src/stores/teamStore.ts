import { create } from 'zustand';
import { apiFetch } from '@/api/client';
import { useAuthStore } from './authStore';

export interface PokemonSlot {
  id: number;
  pokemon_id?: number;
  pokname: string;
  poknick: string;
  hpiv: number;
  atkiv: number;
  defiv: number;
  spatkiv: number;
  spdefiv: number;
  speediv: number;
  hpev: number;
  atkev: number;
  defev: number;
  spatkev: number;
  spdefev: number;
  speedev: number;
  moves: string[];
  hitem: string;
  nature: string;
  pokelevel: number;
  happiness: number;
  ability_index: number;
  gender: string;
  shiny: boolean;
  radiant: boolean;
  skin: string | null;
}

export interface TeamSummary {
  name: string;
  pokemon_count: number;
  pokemon: {
    pokname: string;
    pokemon_id: number;
    shiny: boolean;
  }[];
  updated_at: string;
  is_active: boolean;
}

export interface TeamDetails {
  name: string;
  pokemon: PokemonSlot[];
  created_at: string;
  updated_at: string;
}

interface TeamState {
  teams: TeamSummary[];
  currentTeam: TeamDetails | null;
  isLoading: boolean;
  error: string | null;

  fetchTeams: () => Promise<TeamSummary[]>;
  fetchTeamDetails: (name: string) => Promise<TeamDetails | null>;
  createTeam: (name: string, pokemon: PokemonSlot[]) => Promise<TeamDetails>;
  updateTeam: (name: string, pokemon: PokemonSlot[]) => Promise<void>;
  renameTeam: (name: string, newName: string) => Promise<void>;
  deleteTeam: (name: string) => Promise<void>;
  activateTeam: (name: string) => Promise<void>;
}

export const useTeamStore = create<TeamState>((set) => ({
  teams: [],
  currentTeam: null,
  isLoading: false,
  error: null,

  fetchTeams: async () => {
    set({ isLoading: true, error: null });
    try {
      const teams = await apiFetch<TeamSummary[]>('/api/teams');
      set({ teams, isLoading: false });
      return teams;
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      return [];
    }
  },

  fetchTeamDetails: async (name: string) => {
    set({ isLoading: true, error: null });
    try {
      const currentTeam = await apiFetch<TeamDetails>(`/api/teams/${encodeURIComponent(name)}`);
      set({ currentTeam, isLoading: false });
      return currentTeam;
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      return null;
    }
  },

  createTeam: async (name: string, pokemon: PokemonSlot[]) => {
    set({ isLoading: true, error: null });
    try {
      const newTeam = await apiFetch<TeamDetails>('/api/teams', {
        method: 'POST',
        body: JSON.stringify({ name, pokemon }),
      });
      set({ isLoading: false });
      // Refresh user profile in case active party changed, and fetch teams list
      useAuthStore.getState().fetchProfile();
      return newTeam;
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      throw err;
    }
  },

  updateTeam: async (name: string, pokemon: PokemonSlot[]) => {
    set({ isLoading: true, error: null });
    try {
      await apiFetch<any>(`/api/teams/${encodeURIComponent(name)}`, {
        method: 'PUT',
        body: JSON.stringify({ pokemon }),
      });
      set({ isLoading: false });
      useAuthStore.getState().fetchProfile();
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      throw err;
    }
  },

  renameTeam: async (name: string, newName: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiFetch<any>(`/api/teams/${encodeURIComponent(name)}/rename`, {
        method: 'PATCH',
        body: JSON.stringify({ new_name: newName }),
      });
      set({ isLoading: false });
      useAuthStore.getState().fetchProfile();
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      throw err;
    }
  },

  deleteTeam: async (name: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiFetch<any>(`/api/teams/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      set({ isLoading: false });
      useAuthStore.getState().fetchProfile();
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      throw err;
    }
  },

  activateTeam: async (name: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiFetch<any>(`/api/teams/${encodeURIComponent(name)}/activate`, {
        method: 'POST',
      });
      set({ isLoading: false });
      useAuthStore.getState().fetchProfile();
    } catch (err: any) {
      set({ isLoading: false, error: err.message });
      throw err;
    }
  },
}));
export const createEmptyPokemon = (id: number): PokemonSlot => ({
  id,
  pokname: '',
  poknick: '',
  hpiv: 31,
  atkiv: 31,
  defiv: 31,
  spatkiv: 31,
  spdefiv: 31,
  speediv: 31,
  hpev: 0,
  atkev: 0,
  defev: 0,
  spatkev: 0,
  spdefev: 0,
  speedev: 0,
  moves: ['', '', '', ''],
  hitem: '',
  nature: 'Hardy',
  pokelevel: 100,
  happiness: 255,
  ability_index: 0,
  gender: 'M',
  shiny: false,
  radiant: false,
  skin: null,
});
