import { FastifyInstance } from "fastify";
import { authMiddleware } from "../middleware/auth.js";
import { getDb } from "../db/mongo.js";
import { cacheGet, cacheSet, cacheDel } from "../utils/cache.js";

export async function playerRoutes(app: FastifyInstance): Promise<void> {
  app.get(
    "/api/player/profile",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;

        // Try cache — Redis may be unavailable on serverless warmups
        try {
          const cached = await cacheGet(`wp:${userId}`);
          if (cached) {
            return JSON.parse(cached);
          }
        } catch {
          // cache miss or Redis error — fall through to DB
        }

        const db = await getDb();
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

        // Best-effort cache write
        try {
          await cacheSet(`wp:${userId}`, JSON.stringify(profile), 30);
        } catch {
          // cache write failure is non-fatal
        }

        return profile;
      } catch (error: any) {
        console.error("[player] GET /api/player/profile error:", error);
        reply.status(500).send({ error: error.message || "Failed to fetch profile" });
      }
    },
  );

  // Profile update endpoint — upserts player fields like theme/gen
  app.patch(
    "/api/player/profile",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const body = request.body as {
          theme?: string;
          gen?: number;
          username?: string;
        };

        const update: Record<string, any> = { updated_at: new Date() };
        if (body.theme !== undefined) update.theme = body.theme;
        if (body.gen !== undefined) update.gen = body.gen;
        if (body.username !== undefined) update.username = body.username;

        const db = await getDb();
        await db.collection("players").updateOne(
          { _id: userId as any },
          { $set: update },
          { upsert: true },
        );

        try {
          await cacheDel(`wp:${userId}`);
        } catch {
          // best-effort
        }

        return { success: true, ...update };
      } catch (error: any) {
        console.error("[player] PATCH /api/player/profile error:", error);
        reply.status(500).send({ error: error.message || "Failed to update profile" });
      }
    },
  );
}
