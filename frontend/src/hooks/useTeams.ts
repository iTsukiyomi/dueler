import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchTeams,
  fetchTeam,
  createTeam,
  deleteTeam,
  activateTeam,
  renameTeam,
} from "../api/teams";
import type { PokemonSlot } from "../types";
import toast from "react-hot-toast";

export function useTeamsList() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
    refetchInterval: 30000,
  });
}

export function useTeamDetail(name: string | undefined) {
  return useQuery({
    queryKey: ["team", name],
    queryFn: () => fetchTeam(name!),
    enabled: !!name,
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      name,
      pokemon,
    }: {
      name: string;
      pokemon: PokemonSlot[];
    }) => createTeam(name, pokemon),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team created!");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error ?? "Failed to create team");
    },
  });
}

export function useDeleteTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => deleteTeam(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team deleted");
    },
    onError: () => toast.error("Failed to delete team"),
  });
}

export function useActivateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => activateTeam(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team set as active!");
    },
    onError: () => toast.error("Failed to activate team"),
  });
}

export function useRenameTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, newName }: { name: string; newName: string }) =>
      renameTeam(name, newName),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team renamed!");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error ?? "Failed to rename team");
    },
  });
}
