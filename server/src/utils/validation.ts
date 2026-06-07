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

  const poknameStr = typeof slot.pokname === "string" ? slot.pokname.trim() : "";
  if (poknameStr === "") {
    return errors;
  }

  const form = data.formsByIdentifier.get(poknameStr.toLowerCase());
  if (!form) {
    errors.push(`Unknown Pokémon: ${slot.pokname || "missing"}`);
  }

  if (!slot.moves || !Array.isArray(slot.moves) || slot.moves.length !== 4) {
    errors.push("Exactly 4 moves required");
  } else {
    for (const move of slot.moves) {
      const mStr = typeof move === "string" ? move.trim() : "";
      if (mStr !== "" && !data.movesByIdentifier.has(mStr.toLowerCase())) {
        errors.push(`Unknown move: ${move || "missing"}`);
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

  const natureStr = typeof slot.nature === "string" ? slot.nature.trim() : "";
  if (!natureStr || !data.naturesByIdentifier.has(natureStr.toLowerCase())) {
    errors.push(`Unknown nature: ${slot.nature || "missing"}`);
  }

  const itemStr = typeof slot.hitem === "string" ? slot.hitem.trim() : "";
  if (itemStr && !data.itemsByIdentifier.has(itemStr.toLowerCase())) {
    errors.push(`Unknown item: ${slot.hitem || "missing"}`);
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
