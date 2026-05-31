import axios from "axios";
import type { AuthUser } from "../types";

const api = axios.create({ withCredentials: true });

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/api/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/api/auth/logout");
}

export function getLoginUrl(): string {
  return "/api/auth/login";
}
