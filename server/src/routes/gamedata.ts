import { FastifyInstance } from "fastify";
import {
  GameData,
  displayName,
  spriteUrl,
  getTypeNames,
  TYPE_NAMES,
  STAT_NAMES,
  DAMAGE_CLASS,
} from "../gamedata/loader.js";

export function gamedataRoutes(app: FastifyInstance, data: GameData): void {
  app.get("/api/gamedata/pokemon", async (request) => {
    const { q = "", limit = "20" } = request.query as Record<string, string>;
    const query = q.toLowerCase();
    const max = Math.min(parseInt(limit, 10) || 20, 100);

    const results: any[] = [];
    for (const form of data.formsAll) {
      if (results.length >= max) break;
      if (!form.identifier.includes(query)) continue;

      const types = data.typesByPokemonId.get(form.pokemon_id);
      results.push({
        pokemon_id: form.pokemon_id,
        identifier: form.identifier,
        display_name: displayName(form.identifier),
        sprite_url: spriteUrl(form.pokemon_id),
        types: types ? getTypeNames(types.types) : [],
        is_mega: form.is_mega === 1,
        is_default: form.is_default === 1,
      });
    }

    return results;
  });

  app.get("/api/gamedata/pokemon/:identifier", async (request, reply) => {
    const { identifier } = request.params as { identifier: string };
    const form = data.formsByIdentifier.get(identifier.toLowerCase());
    if (!form) {
      reply.status(404).send({ error: "Pokemon not found" });
      return;
    }

    const stats = data.statsByPokemonId.get(form.pokemon_id);
    const types = data.typesByPokemonId.get(form.pokemon_id);
    const pokAbilities = data.abilitiesByPokemonId.get(form.pokemon_id) ?? [];

    const abilities = pokAbilities
      .sort((a, b) => a.slot - b.slot)
      .map((pa) => {
        const ab = data.abilitiesById.get(pa.ability_id);
        return {
          ability_id: pa.ability_id,
          identifier: ab?.identifier ?? `ability-${pa.ability_id}`,
          display_name: ab ? displayName(ab.identifier) : `Unknown`,
          is_hidden: pa.is_hidden === 1,
          slot: pa.slot,
        };
      });

    const normId = form.identifier
      .toLowerCase()
      .replace(/-/g, "")
      .replace(/\s/g, "");
    const baseId = form.identifier
      .toLowerCase()
      .split("-")[0]
      .replace(/-/g, "")
      .replace(/\s/g, "");
    const learnset =
      data.learnsets.get(normId) ?? data.learnsets.get(baseId) ?? [];

    return {
      pokemon_id: form.pokemon_id,
      identifier: form.identifier,
      display_name: displayName(form.identifier),
      sprite_url: spriteUrl(form.pokemon_id),
      sprite_url_shiny: spriteUrl(form.pokemon_id, true),
      types: types ? getTypeNames(types.types) : [],
      type_ids: types?.types ?? [],
      base_stats: stats
        ? {
            hp: stats.stats[0],
            atk: stats.stats[1],
            def: stats.stats[2],
            spa: stats.stats[3],
            spd: stats.stats[4],
            spe: stats.stats[5],
          }
        : null,
      abilities,
      learnset,
      is_mega: form.is_mega === 1,
      weight: form.weight,
    };
  });

  app.get("/api/gamedata/moves", async (request) => {
    const {
      q = "",
      pokemon,
      limit = "20",
    } = request.query as Record<string, string>;
    const query = q.toLowerCase();
    const max = Math.min(parseInt(limit, 10) || 20, 100);

    let allowedMoves: Set<string> | null = null;
    if (pokemon) {
      const normPoke = pokemon
        .toLowerCase()
        .replace(/-/g, "")
        .replace(/\s/g, "");
      const basePoke = pokemon
        .toLowerCase()
        .split("-")[0]
        .replace(/-/g, "")
        .replace(/\s/g, "");
      const ls = data.learnsets.get(normPoke) ?? data.learnsets.get(basePoke);
      if (ls) {
        allowedMoves = new Set(ls);
      }
    }

    const results: any[] = [];
    for (const move of data.movesAll) {
      if (results.length >= max) break;
      if (!move.identifier.includes(query)) continue;

      if (allowedMoves) {
        const normMove = move.identifier
          .toLowerCase()
          .replace(/-/g, "")
          .replace(/\s/g, "");
        if (!allowedMoves.has(normMove)) continue;
      }

      results.push({
        id: move.id,
        identifier: move.identifier,
        display_name: displayName(move.identifier),
        type_name: TYPE_NAMES[move.type_id] ?? "Unknown",
        type_id: move.type_id,
        damage_class: DAMAGE_CLASS[move.damage_class_id] ?? "Unknown",
        damage_class_id: move.damage_class_id,
        power: move.power,
        pp: move.pp,
        accuracy: move.accuracy,
        priority: move.priority,
      });
    }

    return results;
  });

  app.get("/api/gamedata/moves/:identifier", async (request, reply) => {
    const { identifier } = request.params as { identifier: string };
    const move = data.movesByIdentifier.get(identifier.toLowerCase());
    if (!move) {
      reply.status(404).send({ error: "Move not found" });
      return;
    }

    return {
      id: move.id,
      identifier: move.identifier,
      display_name: displayName(move.identifier),
      type_name: TYPE_NAMES[move.type_id] ?? "Unknown",
      type_id: move.type_id,
      damage_class: DAMAGE_CLASS[move.damage_class_id] ?? "Unknown",
      damage_class_id: move.damage_class_id,
      power: move.power,
      pp: move.pp,
      accuracy: move.accuracy,
      priority: move.priority,
    };
  });

  app.get("/api/gamedata/natures", async () => {
    return data.naturesAll.map((n) => ({
      identifier: n.identifier,
      display_name: displayName(n.identifier),
      increased_stat_id: n.increased_stat_id,
      decreased_stat_id: n.decreased_stat_id,
      increases_stat:
        n.increased_stat_id !== n.decreased_stat_id
          ? (STAT_NAMES[n.increased_stat_id] ?? null)
          : null,
      decreases_stat:
        n.increased_stat_id !== n.decreased_stat_id
          ? (STAT_NAMES[n.decreased_stat_id] ?? null)
          : null,
    }));
  });

  app.get("/api/gamedata/items", async (request) => {
    const { q = "", limit = "20" } = request.query as Record<string, string>;
    const query = q.toLowerCase();
    const max = Math.min(parseInt(limit, 10) || 20, 100);

    const results: any[] = [];
    for (const item of data.itemsAll) {
      if (results.length >= max) break;
      if (!item.identifier.includes(query)) continue;
      results.push({
        id: item.id,
        identifier: item.identifier,
        display_name: displayName(item.identifier),
      });
    }
    return results;
  });

  app.get("/api/gamedata/abilities", async (request) => {
    const { q = "", limit = "20" } = request.query as Record<string, string>;
    const query = q.toLowerCase();
    const max = Math.min(parseInt(limit, 10) || 20, 100);

    const results: any[] = [];
    for (const ab of data.abilitiesAll) {
      if (results.length >= max) break;
      if (!ab.identifier.includes(query)) continue;
      results.push({
        id: ab.id,
        identifier: ab.identifier,
        display_name: displayName(ab.identifier),
      });
    }
    return results;
  });
}
