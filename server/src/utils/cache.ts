import { getRedis } from "../db/redis.js";

export async function cacheGet(key: string): Promise<string | null> {
  try {
    const r = getRedis();
    if (!r) return null;
    return r.get(key);
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
    await r.set(key, value, "EX", ttl);
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

export async function invalidatePlayerCache(userId: string): Promise<void> {
  try {
    await cacheDel(
      `player:${userId}`,
      `active_party:${userId}`,
      `img:profile:${userId}`,
      `img:settings:${userId}`,
      `img:qi:ws:${userId}`,
    );

    const r = getRedis();
    if (!r) return;
    const qiKeys = await r.keys(`img:qi:search:${userId}:*`);
    const helpKeys = await r.keys(`img:help:${userId}:*`);
    const allKeys = [...qiKeys, ...helpKeys];
    if (allKeys.length > 0) await r.del(...allKeys);
  } catch {
    // non-fatal
  }
}

export async function invalidateActiveParty(userId: string): Promise<void> {
  try {
    await cacheDel(
      `active_party:${userId}`,
      `img:profile:${userId}`,
    );
  } catch {
    // non-fatal
  }
}
