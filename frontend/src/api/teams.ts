import axios from "axios";
import type { TeamListItem, Team, PokemonSlot } from "../types";

const api = axios.create({ withCredentials: true });

export async function fetchTeams(): Promise<TeamListItem[]> {
  const { data } = await api.get<TeamListItem[]>("/api/teams");
  return data;
}

export async function fetchTeam(name: string): Promise<Team> {
  const { data } = await api.get<Team>(
    `/api/teams/${encodeURIComponent(name)}`,
  );
  return data;
}

export async function createTeam(
  name: string,
  pokemon: PokemonSlot[],
): Promise<Team> {
  const { data } = await api.post<Team>("/api/teams", { name, pokemon });
  return data;
}

export async function updateTeam(
  name: string,
  pokemon: PokemonSlot[],
): Promise<void> {
  await api.put(`/api/teams/${encodeURIComponent(name)}`, { pokemon });
}

export async function renameTeam(
  name: string,
  newName: string,
): Promise<void> {
  await api.patch(`/api/teams/${encodeURIComponent(name)}/rename`, {
    new_name: newName,
  });
}

export async function deleteTeam(name: string): Promise<void> {
  await api.delete(`/api/teams/${encodeURIComponent(name)}`);
}

export async function activateTeam(name: string): Promise<void> {
  await api.post(`/api/teams/${encodeURIComponent(name)}/activate`);
}
