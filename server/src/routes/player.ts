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
      let player = await db
        .collection("players")
        .findOne({ _id: userId as any });

      if (!player) {
        const now = new Date();
        const avatar = request.user!.avatar;
        const avatarUrl = avatar
          ? `https://cdn.discordapp.com/avatars/${userId}/${avatar}.png?size=128`
          : `https://cdn.discordapp.com/embed/avatars/${parseInt(userId) % 5}.png`;

        player = {
          _id: userId as any,
          username: request.user!.username || "Trainer",
          avatarUrl,
          wins: 0,
          losses: 0,
          elo: 1000,
          wallet: 0,
          active_party_name: null,
          theme: "firered",
          gen: 5,
          moveset_img: true,
          created_at: now,
          updated_at: now,
        };
        await db.collection("players").insertOne(player);
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
