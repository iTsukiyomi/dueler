import { initApp } from "./app.js";
import { config } from "./config.js";
import { closeMongo } from "./db/mongo.js";
import { closeRedis } from "./db/redis.js";
import path from "path";
import { fileURLToPath } from "url";
import fastifyStatic from "@fastify/static";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const app = await initApp();

  // Serve React frontend static files when running standalone
  await app.register(fastifyStatic, {
    root: path.join(__dirname, "../../frontend/dist"),
    prefix: "/",
    wildcard: false,
  });

  // Client-side router fallback (React Router) for standalone — skip API routes
  app.setNotFoundHandler(async (request, reply) => {
    if (request.url.startsWith("/api/")) {
      return reply.status(404).send({ error: "Route not found" });
    }
    return reply.sendFile("index.html");
  });

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
    `[server] Darkmew API running on http://localhost:${config.server.port}`,
  );
}

main().catch((err) => {
  console.error("[server] Fatal:", err);
  process.exit(1);
});
