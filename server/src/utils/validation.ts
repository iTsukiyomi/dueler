import { GameData } from "../gamedata/loader.js";

export interface PokemonSlot {
  id: number;
  pokname: string;
  poknick: string;
  hpiv: number;
  atkiv: number;
  defiv: number;
  spatkiv: number;
  spdefiv: number;
  speediv: number;
  hpev: number;
  atkev: number;
  defev: number;
  spatkev: number;
  spdefev: number;
  speedev: number;
  moves: string[];
  hitem: string;
  nature: string;
  pokelevel: number;
  happiness: number;
  ability_index: number;
  gender: string;
  shiny: boolean;
  radiant: boolean;
  skin: string | null;
}

function normalize(s: string): string {
  return s.toLowerCase().replace(/-/g, "").replace(/\s/g, "");
}

export function validatePokemonSlot(
  slot: PokemonSlot,
  data: GameData,
): string[] {
  const errors: string[] = [];

  const form = data.formsByIdentifier.get(slot.pokname.toLowerCase());
  if (!form) {
    errors.push(`Unknown Pokémon: ${slot.pokname}`);
  }

  if (!slot.moves || slot.moves.length !== 4) {
    errors.push("Exactly 4 moves required");
  } else {
    for (const move of slot.moves) {
      if (!data.movesByIdentifier.has(move.toLowerCase())) {
        errors.push(`Unknown move: ${move}`);
      }
    }

    if (form) {
      const identifier = form.identifier;
      const normId = normalize(identifier);
      const baseId = normalize(identifier.split("-")[0]);
      const learnset =
        data.learnsets.get(normId) ?? data.learnsets.get(baseId);

      if (learnset) {
        for (const move of slot.moves) {
          const normMove = normalize(move);
          if (!learnset.includes(normMove)) {
            errors.push(`${slot.pokname} cannot learn ${move}`);
          }
        }
      }
    }
  }

  const ivFields = [
    "hpiv",
    "atkiv",
    "defiv",
    "spatkiv",
    "spdefiv",
    "speediv",
  ] as const;
  for (const f of ivFields) {
    const val = slot[f];
    if (typeof val !== "number" || val < 0 || val > 31) {
      errors.push(`${f} must be 0-31 (got ${val})`);
    }
  }

  const evFields = [
    "hpev",
    "atkev",
    "defev",
    "spatkev",
    "spdefev",
    "speedev",
  ] as const;
  let evTotal = 0;
  for (const f of evFields) {
    const val = slot[f];
    if (typeof val !== "number" || val < 0 || val > 252) {
      errors.push(`${f} must be 0-252 (got ${val})`);
    } else {
      evTotal += val;
    }
  }
  if (evTotal > 510) {
    errors.push(`EV total ${evTotal} exceeds maximum of 510`);
  }

  if (!data.naturesByIdentifier.has(slot.nature.toLowerCase())) {
    errors.push(`Unknown nature: ${slot.nature}`);
  }

  if (slot.hitem && !data.itemsByIdentifier.has(slot.hitem.toLowerCase())) {
    errors.push(`Unknown item: ${slot.hitem}`);
  }

  if (
    typeof slot.ability_index !== "number" ||
    slot.ability_index < 0 ||
    slot.ability_index > 2
  ) {
    errors.push(`ability_index must be 0, 1, or 2`);
  }

  return errors;
}

export function validateTeamName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) return "Team name is required";
  if (trimmed.length > 32) return "Team name must be 32 characters or less";
  if (trimmed === "__active__") return "Reserved team name";
  return null;
}
