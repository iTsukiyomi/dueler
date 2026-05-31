import { FastifyInstance } from "fastify";
import { authMiddleware } from "../middleware/auth.js";
import { getDb } from "../db/mongo.js";
import { cacheGet, cacheSet } from "../utils/cache.js";

export async function playerRoutes(app: FastifyInstance): Promise<void> {
  app.get(
    "/api/player/profile",
    { preHandler: authMiddleware },
    async (request, reply) => {
      const userId = request.user!.userId;

      const cacheKey = `web:profile:${userId}`;
      const cached = await cacheGet(cacheKey);
      if (cached) {
        return JSON.parse(cached);
      }

      const db = getDb();
      const player = await db
        .collection("players")
        .findOne({ _id: userId as any });

      if (!player) {
        reply.status(404).send({ error: "Player profile not found" });
        return;
      }

      const higherCount = await db.collection("players").countDocuments({
        elo: { $gt: player.elo ?? 1000 },
        $or: [{ wins: { $gt: 0 } }, { losses: { $gt: 0 } }],
      });
      const rank =
        (player.wins ?? 0) > 0 || (player.losses ?? 0) > 0
          ? higherCount + 1
          : null;

      const profile = {
        username: player.username,
        wins: player.wins ?? 0,
        losses: player.losses ?? 0,
        elo: player.elo ?? 1000,
        wallet: player.wallet ?? 0,
        active_party_name: player.active_party_name ?? null,
        theme: player.theme ?? "firered",
        gen: player.gen ?? 5,
        rank,
      };

      await cacheSet(cacheKey, JSON.stringify(profile), 60);
      return profile;
    },
  );
}
