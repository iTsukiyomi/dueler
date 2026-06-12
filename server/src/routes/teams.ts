import { FastifyInstance } from "fastify";
import { authMiddleware } from "../middleware/auth.js";
import { getDb } from "../db/mongo.js";
import {
  invalidatePlayerCache,
  invalidateActiveParty,
  cacheDel,
} from "../utils/cache.js";
import {
  validatePokemonSlot,
  validateTeamName,
  PokemonSlot,
} from "../utils/validation.js";
import { GameData } from "../gamedata/loader.js";
import { syncActivePartyToDiscord } from "../utils/squadSync.js";

export function teamRoutes(app: FastifyInstance, data: GameData): void {
  app.get(
    "/api/teams",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const db = getDb();

        const player = await db
          .collection("players")
          .findOne({ _id: userId as any });
        const activePartyName = player?.active_party_name ?? null;

        const teams = await db
          .collection("teams")
          .find(
            { owner_id: userId, name: { $ne: "__active__" } },
            { projection: { name: 1, pokemon: 1, updated_at: 1 } },
          )
          .sort({ name: 1 })
          .toArray();

        return teams.map((t) => ({
          name: t.name,
          pokemon_count: t.pokemon?.length ?? 0,
          pokemon: (t.pokemon ?? []).map((p: any) => ({
            pokname: p.pokname,
            pokemon_id:
              data.formsByIdentifier.get(p.pokname?.toLowerCase())
                ?.pokemon_id ?? 0,
            shiny: p.shiny ?? false,
          })),
          updated_at: t.updated_at,
          is_active: t.name === activePartyName,
        }));
      } catch (error: any) {
        console.error("[teams] GET /api/teams error:", error);
        reply.status(500).send({ error: error.message || "Failed to fetch teams" });
      }
    },
  );

  app.get(
    "/api/teams/:name",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { name } = request.params as { name: string };
        const db = getDb();

        const team = await db
          .collection("teams")
          .findOne({ owner_id: userId, name: name.trim().toLowerCase() });

        if (!team) {
          reply.status(404).send({ error: "Team not found" });
          return;
        }

        return {
          name: team.name,
          pokemon: (team.pokemon ?? []).map((p: any) => ({
            ...p,
            pokemon_id:
              data.formsByIdentifier.get(p.pokname?.toLowerCase())
                ?.pokemon_id ?? 0,
          })),
          created_at: team.created_at,
          updated_at: team.updated_at,
        };
      } catch (error: any) {
        console.error(`[teams] GET /api/teams/${(request.params as any).name} error:`, error);
        reply.status(500).send({ error: error.message || "Failed to fetch team details" });
      }
    },
  );

  app.post(
    "/api/teams",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const body = request.body as { name: string; pokemon: PokemonSlot[] };

        const nameError = validateTeamName(body.name);
        if (nameError) {
          reply.status(400).send({ error: nameError });
          return;
        }

        if (
          !body.pokemon ||
          body.pokemon.length < 1 ||
          body.pokemon.length > 6
        ) {
          reply.status(400).send({ error: "Team must have 1-6 Pokémon" });
          return;
        }

        const allErrors: string[] = [];
        for (let i = 0; i < body.pokemon.length; i++) {
          const errs = validatePokemonSlot(body.pokemon[i], data);
          allErrors.push(...errs.map((e) => `Slot ${i + 1}: ${e}`));
        }
        if (allErrors.length > 0) {
          reply.status(400).send({ error: "Validation failed", details: allErrors });
          return;
        }

        const db = getDb();
        const now = new Date();
        const teamName = body.name.trim().toLowerCase();

        const existing = await db
          .collection("teams")
          .findOne({ owner_id: userId, name: teamName });
        if (existing) {
          reply
            .status(409)
            .send({ error: `Team "${body.name}" already exists` });
          return;
        }

        const doc = {
          owner_id: userId,
          name: teamName,
          pokemon: body.pokemon,
          created_at: now,
          updated_at: now,
        };

        await db.collection("teams").insertOne(doc);
        await invalidatePlayerCache(userId);

        reply.status(201).send({
          name: doc.name,
          pokemon: doc.pokemon,
          created_at: doc.created_at,
          updated_at: doc.updated_at,
        });
      } catch (error: any) {
        console.error("[teams] POST /api/teams error:", error);
        reply.status(500).send({ error: error.message || "Failed to create team" });
      }
    },
  );

  app.put(
    "/api/teams/:name",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { name } = request.params as { name: string };
        const body = request.body as { pokemon: PokemonSlot[] };
        const teamName = name.trim().toLowerCase();

        if (
          !body.pokemon ||
          body.pokemon.length < 1 ||
          body.pokemon.length > 6
        ) {
          reply.status(400).send({ error: "Team must have 1-6 Pokémon" });
          return;
        }

        const allErrors: string[] = [];
        for (let i = 0; i < body.pokemon.length; i++) {
          const errs = validatePokemonSlot(body.pokemon[i], data);
          allErrors.push(...errs.map((e) => `Slot ${i + 1}: ${e}`));
        }
        if (allErrors.length > 0) {
          reply.status(400).send({ error: "Validation failed", details: allErrors });
          return;
        }

        const db = getDb();
        const result = await db.collection("teams").updateOne(
          { owner_id: userId, name: teamName },
          { $set: { pokemon: body.pokemon, updated_at: new Date() } },
        );

        if (result.matchedCount === 0) {
          reply.status(404).send({ error: "Team not found" });
          return;
        }

        await invalidatePlayerCache(userId);
        await invalidateActiveParty(userId);
        await cacheDel(`web:profile:${userId}`);

        const player = await db
          .collection("players")
          .findOne({ _id: userId as any });
        if (player?.active_party_name === teamName) {
          await db.collection("teams").updateOne(
            { owner_id: userId, name: "__active__" },
            {
              $set: { pokemon: body.pokemon, updated_at: new Date() },
              $setOnInsert: {
                owner_id: userId,
                name: "__active__",
                created_at: new Date(),
              },
            },
            { upsert: true },
          );
          syncActivePartyToDiscord(userId, body.pokemon);
        }

        return { success: true };
      } catch (error: any) {
        console.error(`[teams] PUT /api/teams/${(request.params as any).name} error:`, error);
        reply.status(500).send({ error: error.message || "Failed to update team" });
      }
    },
  );

  app.patch(
    "/api/teams/:name/rename",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { name } = request.params as { name: string };
        const body = request.body as { new_name: string };
        const oldName = name.trim().toLowerCase();

        const nameError = validateTeamName(body.new_name);
        if (nameError) {
          reply.status(400).send({ error: nameError });
          return;
        }

        const newName = body.new_name.trim().toLowerCase();
        const db = getDb();

        const existing = await db
          .collection("teams")
          .findOne({ owner_id: userId, name: newName });
        if (existing) {
          reply.status(409).send({ error: `Team "${body.new_name}" already exists` });
          return;
        }

        const result = await db.collection("teams").updateOne(
          { owner_id: userId, name: oldName },
          { $set: { name: newName, updated_at: new Date() } },
        );

        if (result.matchedCount === 0) {
          reply.status(404).send({ error: "Team not found" });
          return;
        }

        const player = await db
          .collection("players")
          .findOne({ _id: userId as any });
        if (player?.active_party_name === oldName) {
          await db.collection("players").updateOne(
            { _id: userId as any },
            { $set: { active_party_name: newName, updated_at: new Date() } },
          );
          await invalidatePlayerCache(userId);
        }

        await cacheDel(`web:profile:${userId}`);
        return { success: true };
      } catch (error: any) {
        console.error(`[teams] PATCH /api/teams/${(request.params as any).name}/rename error:`, error);
        reply.status(500).send({ error: error.message || "Failed to rename team" });
      }
    },
  );

  app.delete(
    "/api/teams/:name",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { name } = request.params as { name: string };
        const teamName = name.trim().toLowerCase();

        const db = getDb();
        
        const player = await db
          .collection("players")
          .findOne({ _id: userId as any });
        
        const result = await db
          .collection("teams")
          .deleteOne({ owner_id: userId, name: teamName });

        if (result.deletedCount === 0) {
          reply.status(404).send({ error: "Team not found" });
          return;
        }

        if (player?.active_party_name === teamName) {
          await db.collection("players").updateOne(
            { _id: userId as any },
            {
              $set: { active_party_name: null, updated_at: new Date() },
            },
          );
          await db
            .collection("teams")
            .deleteOne({ owner_id: userId, name: "__active__" });
          syncActivePartyToDiscord(userId, []);
        }

        await invalidatePlayerCache(userId);
        await invalidateActiveParty(userId);
        await cacheDel(`web:profile:${userId}`);

        return { success: true };
      } catch (error: any) {
        console.error(`[teams] DELETE /api/teams/${(request.params as any).name} error:`, error);
        reply.status(500).send({ error: error.message || "Failed to delete team" });
      }
    },
  );

  app.post(
    "/api/teams/:name/activate",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { name } = request.params as { name: string };
        const teamName = name.trim().toLowerCase();

        const db = getDb();
        const team = await db
          .collection("teams")
          .findOne({ owner_id: userId, name: teamName });

        if (!team) {
          reply.status(404).send({ error: "Team not found" });
          return;
        }

        await db.collection("players").updateOne(
          { _id: userId as any },
          {
            $set: {
              active_party_name: teamName,
              updated_at: new Date(),
            },
            $setOnInsert: {
              wins: 0,
              losses: 0,
              elo: 1000,
              wallet: 0,
              theme: "firered",
              gen: 5,
              moveset_img: true,
              created_at: new Date(),
              username: request.user!.username || "Trainer",
            }
          },
          { upsert: true },
        );

        await db.collection("teams").updateOne(
          { owner_id: userId, name: "__active__" },
          {
            $set: {
              pokemon: team.pokemon,
              updated_at: new Date(),
            },
            $setOnInsert: {
              owner_id: userId,
              name: "__active__",
              created_at: new Date(),
            },
          },
          { upsert: true },
        );

        await invalidatePlayerCache(userId);
        await invalidateActiveParty(userId);
        await cacheDel(`web:profile:${userId}`);

        // Sync active party to Discord member config JSON file
        syncActivePartyToDiscord(userId, team.pokemon);

        return { success: true };
      } catch (error: any) {
        console.error(`[teams] POST /api/teams/${(request.params as any).name}/activate error:`, error);
        reply.status(500).send({ error: error.message || "Failed to activate team" });
      }
    },
  );
}
