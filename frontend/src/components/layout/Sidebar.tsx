import React from "react";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";
import { SessionNavBar } from "../ui/sidebar";

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const { data: profile } = usePlayerProfile();

  const wins = profile?.wins ?? 0;
  const losses = profile?.losses ?? 0;
  const total = wins + losses;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";

  return (
    <SessionNavBar
      wins={wins}
      losses={losses}
      winRate={winRate}
      username={user?.username ?? "Trainer"}
      avatarUrl={user?.avatarUrl ?? ""}
      userId={user?.id ?? ""}
      onSignOut={logout}
    />
  );
}

export default Sidebar;