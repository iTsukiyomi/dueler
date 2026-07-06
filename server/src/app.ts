import Fastify, { FastifyInstance } from "fastify";
import cors from "@fastify/cors";
import cookie from "@fastify/cookie";
import rateLimit from "@fastify/rate-limit";

import { config } from "./config.js";
import { connectMongo } from "./db/mongo.js";
import { connectRedis } from "./db/redis.js";
import { loadGameData } from "./gamedata/loader.js";
import { authRoutes } from "./routes/auth.js";
import { playerRoutes } from "./routes/player.js";
import { teamRoutes } from "./routes/teams.js";
import { gamedataRoutes } from "./routes/gamedata.js";
import { statsRoutes } from "./routes/stats.js";
import { chatRoutes } from "./routes/chat.js";

let app: FastifyInstance | null = null;

export async function initApp(): Promise<FastifyInstance> {
  if (app) return app;

  app = Fastify({ logger: false });

  await app.register(cors, {
    origin: config.server.frontendUrl,
    credentials: true,
  });

  await app.register(cookie);

  await app.register(rateLimit, {
    max: 100,
    timeWindow: "1 minute",
  });

  // Non-fatal DB connections — server starts even if DB is down so auth routes always register
  try {
    console.log("[server] Connecting to MongoDB...");
    await connectMongo();
  } catch (err) {
    console.warn("[server] MongoDB connection failed — running without database:", (err as Error).message);
  }

  try {
    console.log("[server] Connecting to Redis...");
    await connectRedis();
  } catch (err) {
    console.warn("[server] Redis connection failed — running without cache:", (err as Error).message);
  }

  console.log("[server] Loading game data...");
  const gameData = loadGameData(config.dataDir);

  // Register API routes
  await authRoutes(app);
  await playerRoutes(app);
  teamRoutes(app, gameData);
  gamedataRoutes(app, gameData);
  await statsRoutes(app);
  await chatRoutes(app);

  app.get("/api/health", async () => ({ status: "ok" }));

  return app;
}
