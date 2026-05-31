import axios from "axios";
import type {
  GameDataPokemon,
  GameDataMove,
  GameDataNature,
  GameDataItem,
  GameDataAbility,
} from "../types";

const api = axios.create({ withCredentials: true });

export async function searchPokemon(
  q: string,
  limit = 20,
): Promise<GameDataPokemon[]> {
  const { data } = await api.get<GameDataPokemon[]>("/api/gamedata/pokemon", {
    params: { q, limit },
  });
  return data;
}

export async function getPokemonDetail(
  identifier: string,
): Promise<GameDataPokemon> {
  const { data } = await api.get<GameDataPokemon>(
    `/api/gamedata/pokemon/${encodeURIComponent(identifier)}`,
  );
  return data;
}

export async function searchMoves(
  q: string,
  pokemon?: string,
  limit = 20,
): Promise<GameDataMove[]> {
  const { data } = await api.get<GameDataMove[]>("/api/gamedata/moves", {
    params: { q, pokemon, limit },
  });
  return data;
}

export async function getMoveDetail(
  identifier: string,
): Promise<GameDataMove> {
  const { data } = await api.get<GameDataMove>(
    `/api/gamedata/moves/${encodeURIComponent(identifier)}`,
  );
  return data;
}

export async function fetchNatures(): Promise<GameDataNature[]> {
  const { data } = await api.get<GameDataNature[]>("/api/gamedata/natures");
  return data;
}

export async function searchItems(
  q: string,
  limit = 20,
): Promise<GameDataItem[]> {
  const { data } = await api.get<GameDataItem[]>("/api/gamedata/items", {
    params: { q, limit },
  });
  return data;
}

export async function searchAbilities(
  q: string,
  limit = 20,
): Promise<GameDataAbility[]> {
  const { data } = await api.get<GameDataAbility[]>(
    "/api/gamedata/abilities",
    { params: { q, limit } },
  );
  return data;
}
