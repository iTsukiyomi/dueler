import { useQuery } from "@tanstack/react-query";
import {
  searchPokemon,
  getPokemonDetail,
  searchMoves,
  fetchNatures,
  searchItems,
} from "../api/pokemon";
import { fetchProfile } from "../api/player";

export function usePokemonSearch(query: string) {
  return useQuery({
    queryKey: ["pokemon-search", query],
    queryFn: () => searchPokemon(query, 30),
    enabled: query.length >= 1,
    staleTime: 60000,
  });
}

export function usePokemonDetail(identifier: string | undefined) {
  return useQuery({
    queryKey: ["pokemon-detail", identifier],
    queryFn: () => getPokemonDetail(identifier!),
    enabled: !!identifier,
    staleTime: 300000,
  });
}

export function useMoveSearch(query: string, pokemon?: string) {
  return useQuery({
    queryKey: ["move-search", query, pokemon],
    queryFn: () => searchMoves(query, pokemon, 50),
    staleTime: 60000,
  });
}

export function useNatures() {
  return useQuery({
    queryKey: ["natures"],
    queryFn: fetchNatures,
    staleTime: Infinity,
  });
}

export function useItemSearch(query: string) {
  return useQuery({
    queryKey: ["item-search", query],
    queryFn: () => searchItems(query, 30),
    enabled: query.length >= 1,
    staleTime: 60000,
  });
}

export function usePlayerProfile() {
  return useQuery({
    queryKey: ["player-profile"],
    queryFn: fetchProfile,
    refetchInterval: 30000,
  });
}
