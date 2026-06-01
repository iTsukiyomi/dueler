import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const api = axios.create({ withCredentials: true });

export interface GlobalStats {
  totalUsers: number;
  totalServers: number;
  totalBattles: number;
  updatedAt: string;
}

export async function fetchGlobalStats(): Promise<GlobalStats> {
  const { data } = await api.get<GlobalStats>("/api/stats/global");
  return data;
}

export function useGlobalStats() {
  return useQuery({
    queryKey: ["global-stats"],
    queryFn: fetchGlobalStats,
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000, // Consider fresh for 30 seconds
  });
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  avatarUrl: string;
  elo: number;
  wins: number;
  losses: number;
  winRate: number;
}

export interface LeaderboardData {
  leaderboard: LeaderboardEntry[];
  updatedAt: string;
}

export async function fetchLeaderboard(limit: number = 50): Promise<LeaderboardData> {
  const { data } = await api.get<LeaderboardData>("/api/leaderboard", {
    params: { limit },
  });
  return data;
}

export function useLeaderboard(limit: number = 50) {
  return useQuery({
    queryKey: ["leaderboard", limit],
    queryFn: () => fetchLeaderboard(limit),
    refetchInterval: 60000,
  });
}

export interface BattleEntry {
  id: string;
  opponent: string;
  opponentAvatar: string;
  result: "win" | "loss";
  myTeam: string;
  opponentTeam: string;
  eloChange: number;
  timestamp: string;
  duration: string;
  turns: number;
}

export interface BattleHistoryData {
  battles: BattleEntry[];
  updatedAt: string;
}

export async function fetchBattleHistory(): Promise<BattleHistoryData> {
  const { data } = await api.get<BattleHistoryData>("/api/battles/history");
  return data;
}

export function useBattleHistory() {
  return useQuery({
    queryKey: ["battle-history"],
    queryFn: fetchBattleHistory,
    refetchInterval: 30000,
  });
}