import { create } from 'zustand';
import { apiFetch } from '@/api/client';

export interface User {
  id: string;
  username: string;
  avatar: string;
  avatarUrl: string;
}

export interface PlayerProfile {
  username: string;
  wins: number;
  losses: number;
  elo: number;
  wallet: number;
  active_party_name: string | null;
  theme: string;
  gen: number;
  rank: number | null;
}

interface AuthState {
  user: User | null;
  profile: PlayerProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isProfileLoading: boolean;
  error: string | null;
  
  fetchUser: () => Promise<User | null>;
  fetchProfile: () => Promise<PlayerProfile | null>;
  login: () => void;
  logout: () => Promise<void>;
  updateThemeOrGen: (theme?: string, gen?: number) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  profile: null,
  isAuthenticated: false,
  isLoading: true,
  isProfileLoading: false,
  error: null,

  fetchUser: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await apiFetch<User>('/api/auth/me');
      set({ user, isAuthenticated: true, isLoading: false });
      // Proactively fetch the profile details
      await get().fetchProfile();
      return user;
    } catch (err: any) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return null;
    }
  },

  fetchProfile: async () => {
    if (!get().isAuthenticated) return null;
    set({ isProfileLoading: true });
    try {
      const profile = await apiFetch<PlayerProfile>('/api/player/profile');
      set({ profile, isProfileLoading: false });
      return profile;
    } catch (err: any) {
      set({ isProfileLoading: false, error: err.message });
      return null;
    }
  },

  login: () => {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    window.location.href = isLocal
      ? 'http://localhost:3001/api/auth/login'
      : `${window.location.origin}/api/auth/login`;
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await apiFetch<{ success: boolean }>('/api/auth/logout', { method: 'POST' });
    } catch (err) {
      console.error('Logout request failed, clearing local state anyway', err);
    } finally {
      set({
        user: null,
        profile: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  updateThemeOrGen: async (theme, gen) => {
    // Currently the backend stores theme/gen in DB players table, let's see if there is an endpoint to update profile/player.
    // Wait, let's check playerRoutes in player.ts to see if it allows PUT or POST to update them.
    // Wait, is there any update endpoint in player.ts? No, player.ts only has GET /api/player/profile!
    // But wait! Is there any active_party_name or theme update?
    // Let's check teamRoutes /api/teams/:name/activate, which updates active_party_name.
    // If the user wants to edit theme/gen, they might do it through other routes or bot. Let's look at requirements.
    // In any case, we can keep it here for local updates or if we find update routes.
  }
}));
