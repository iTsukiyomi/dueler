import Fastify from "fastify";
import cors from "@fastify/cors";
import cookie from "@fastify/cookie";
import rateLimit from "@fastify/rate-limit";

import { config } from "./config.js";
import { connectMongo, closeMongo } from "./db/mongo.js";
import { connectRedis, closeRedis } from "./db/redis.js";
import { loadGameData, GameData } from "./gamedata/loader.js";
import { authRoutes } from "./routes/auth.js";
import { playerRoutes } from "./routes/player.js";
import { teamRoutes } from "./routes/teams.js";
import { gamedataRoutes } from "./routes/gamedata.js";
import { statsRoutes } from "./routes/stats.js";
import { chatRoutes } from "./routes/chat.js";

let gameData: GameData;

async function main() {
  const app = Fastify({ logger: false });

  await app.register(cors, {
    origin: config.server.frontendUrl,
    credentials: true,
  });

  await app.register(cookie);

  await app.register(rateLimit, {
    max: 100,
    timeWindow: "1 minute",
  });

  console.log("[server] Connecting to MongoDB...");
  await connectMongo();

  console.log("[server] Connecting to Redis...");
  await connectRedis();

  console.log("[server] Loading game data...");
  gameData = loadGameData(config.dataDir);

  await authRoutes(app);
  await playerRoutes(app);
  teamRoutes(app, gameData);
  gamedataRoutes(app, gameData);
  await statsRoutes(app);
  await chatRoutes(app);

  app.get("/api/health", async () => ({ status: "ok" }));

  const shutdown = async () => {
    console.log("[server] Shutting down...");
    await app.close();
    await closeMongo();
    await closeRedis();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  await app.listen({ port: config.server.port, host: "0.0.0.0" });
  console.log(
    `[server] Pokemon Dueler API running on http://localhost:${config.server.port}`,
  );
}

main().catch((err) => {
  console.error("[server] Fatal:", err);
  process.exit(1);
});
