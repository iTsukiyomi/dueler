import axios from "axios";
import type { Player } from "../types";

const api = axios.create({ withCredentials: true });

export async function fetchProfile(): Promise<Player> {
  const { data } = await api.get<Player>("/api/player/profile");
  return data;
}
