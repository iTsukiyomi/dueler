import Redis from "ioredis";
import { config } from "../config.js";

let redis: Redis | null = null;

export async function connectRedis(): Promise<Redis | null> {
  if (redis) return redis;

  if (!config.redis.url) {
    console.warn("[redis] REDIS_URL not set — running without cache");
    return null;
  }

  redis = new Redis(config.redis.url, {
    maxRetriesPerRequest: 3,
    retryStrategy(times) {
      if (times > 5) return null;
      return Math.min(times * 200, 2000);
    },
    lazyConnect: true,
  });

  await redis.connect();

  // Aggressive LRU eviction — let Redis manage memory automatically
  try {
    await redis.config("SET", "maxmemory-policy", "allkeys-lru");
    await redis.config("SET", "maxmemory", "25mb");
  } catch {
    // non-fatal — some managed Redis providers restrict CONFIG SET
  }

  console.log("[redis] Connected");
  return redis;
}

export function getRedis(): Redis | null {
  return redis;
}

export async function closeRedis(): Promise<void> {
  if (redis) {
    await redis.quit();
    redis = null;
    console.log("[redis] Connection closed");
  }
}
