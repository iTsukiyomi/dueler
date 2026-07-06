import { gzipSync, gunzipSync } from "zlib";
import { getRedis } from "../db/redis.js";

export async function cacheGet(key: string): Promise<string | null> {
  try {
    const r = getRedis();
    if (!r) return null;
    const raw = await r.get(key) as Buffer | null;
    if (!raw) return null;
    const buf = gunzipSync(raw);
    return buf.toString();
  } catch {
    return null;
  }
}

export async function cacheSet(
  key: string,
  value: string,
  ttl: number,
): Promise<void> {
  try {
    const r = getRedis();
    if (!r) return;
    const compressed = gzipSync(Buffer.from(value));
    await r.set(key, compressed, "EX", ttl);
  } catch {
    // non-fatal
  }
}

export async function cacheDel(...keys: string[]): Promise<void> {
  try {
    const r = getRedis();
    if (!r) return;
    if (keys.length > 0) await r.del(...keys);
  } catch {
    // non-fatal
  }
}

/** Invalidate all Python-bot cache keys for a user — uses shortened key patterns. */
export async function invalidatePlayerCache(userId: string): Promise<void> {
  try {
    await cacheDel(
      `p:${userId}`,
      `ap:${userId}`,
      `id:pr:${userId}`,
      `id:st:${userId}`,
      `id:qw:${userId}`,
    );

    const r = getRedis();
    if (!r) return;
    const qiKeys = await r.keys(`id:qs:${userId}:*`);
    const helpKeys = await r.keys(`id:hl:${userId}:*`);
    const allKeys = [...qiKeys, ...helpKeys];
    if (allKeys.length > 0) await r.del(...allKeys);
  } catch {
    // non-fatal
  }
}

export async function invalidateActiveParty(userId: string): Promise<void> {
  try {
    await cacheDel(
      `ap:${userId}`,
      `id:pr:${userId}`,
    );
  } catch {
    // non-fatal
  }
}
