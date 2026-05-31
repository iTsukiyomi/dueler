import { readFileSync } from "fs";
import { resolve } from "path";

export interface Form {
  identifier: string;
  pokemon_id: number;
  base_id: number;
  is_mega: number;
  is_default: number;
  form_identifier: string;
  weight: number;
}

export interface Move {
  id: number;
  identifier: string;
  type_id: number;
  power: number | null;
  pp: number;
  accuracy: number | null;
  priority: number;
  damage_class_id: number;
}

export interface Nature {
  id: number;
  identifier: string;
  increased_stat_id: number;
  decreased_stat_id: number;
}

export interface Item {
  id: number;
  identifier: string;
}

export interface PokemonStats {
  pokemon_id: number;
  stats: number[];
}

export interface PokemonType {
  id: number;
  types: number[];
}

export interface PokemonAbility {
  pokemon_id: number;
  ability_id: number;
  is_hidden: number;
  slot: number;
}

export interface Ability {
  id: number;
  identifier: string;
}

export interface GameData {
  formsByIdentifier: Map<string, Form>;
  formsByPokemonId: Map<number, Form>;
  formsAll: Form[];
  movesByIdentifier: Map<string, Move>;
  movesAll: Move[];
  learnsets: Map<string, string[]>;
  statsByPokemonId: Map<number, PokemonStats>;
  typesByPokemonId: Map<number, PokemonType>;
  abilitiesByPokemonId: Map<number, PokemonAbility[]>;
  abilitiesById: Map<number, Ability>;
  abilitiesAll: Ability[];
  naturesByIdentifier: Map<string, Nature>;
  naturesAll: Nature[];
  itemsByIdentifier: Map<string, Item>;
  itemsAll: Item[];
}

const TYPE_NAMES: Record<number, string> = {
  1: "Normal",
  2: "Fighting",
  3: "Flying",
  4: "Poison",
  5: "Ground",
  6: "Rock",
  7: "Bug",
  8: "Ghost",
  9: "Steel",
  10: "Fire",
  11: "Water",
  12: "Grass",
  13: "Electric",
  14: "Psychic",
  15: "Ice",
  16: "Dragon",
  17: "Dark",
  18: "Fairy",
};

const STAT_NAMES: Record<number, string> = {
  1: "HP",
  2: "Attack",
  3: "Defense",
  4: "Sp. Atk",
  5: "Sp. Def",
  6: "Speed",
};

const DAMAGE_CLASS: Record<number, string> = {
  1: "Status",
  2: "Physical",
  3: "Special",
};

export { TYPE_NAMES, STAT_NAMES, DAMAGE_CLASS };

function loadJson<T>(dataDir: string, filename: string): T {
  const raw = readFileSync(resolve(dataDir, filename), "utf-8");
  return JSON.parse(raw) as T;
}

export function loadGameData(dataDir: string): GameData {
  console.log(`[gamedata] Loading from ${dataDir}`);

  const formsRaw = loadJson<Form[]>(dataDir, "forms.json");
  const movesRaw = loadJson<Move[]>(dataDir, "moves.json");
  const learnsetsRaw = loadJson<Record<string, string[]>>(
    dataDir,
    "learnsets.json",
  );
  const naturesRaw = loadJson<Nature[]>(dataDir, "natures.json");
  const itemsRaw = loadJson<Item[]>(dataDir, "items.json");
  const statsRaw = loadJson<PokemonStats[]>(dataDir, "pokemon_stats.json");
  const ptypesRaw = loadJson<PokemonType[]>(dataDir, "ptypes.json");
  const pokeAbilitiesRaw = loadJson<PokemonAbility[]>(
    dataDir,
    "poke_abilities.json",
  );
  const abilitiesRaw = loadJson<Ability[]>(dataDir, "abilities.json");

  const formsByIdentifier = new Map<string, Form>();
  const formsByPokemonId = new Map<number, Form>();
  for (const f of formsRaw) {
    formsByIdentifier.set(f.identifier.toLowerCase(), f);
    formsByPokemonId.set(f.pokemon_id, f);
  }

  const movesByIdentifier = new Map<string, Move>();
  for (const m of movesRaw) {
    movesByIdentifier.set(m.identifier.toLowerCase(), m);
  }

  const learnsets = new Map<string, string[]>();
  for (const [key, val] of Object.entries(learnsetsRaw)) {
    learnsets.set(key.toLowerCase(), val);
  }

  const statsByPokemonId = new Map<number, PokemonStats>();
  for (const s of statsRaw) {
    statsByPokemonId.set(s.pokemon_id, s);
  }

  const typesByPokemonId = new Map<number, PokemonType>();
  for (const t of ptypesRaw) {
    typesByPokemonId.set(t.id, t);
  }

  const abilitiesByPokemonId = new Map<number, PokemonAbility[]>();
  for (const a of pokeAbilitiesRaw) {
    const list = abilitiesByPokemonId.get(a.pokemon_id) ?? [];
    list.push(a);
    abilitiesByPokemonId.set(a.pokemon_id, list);
  }

  const abilitiesById = new Map<number, Ability>();
  for (const a of abilitiesRaw) {
    abilitiesById.set(a.id, a);
  }

  const naturesByIdentifier = new Map<string, Nature>();
  for (const n of naturesRaw) {
    naturesByIdentifier.set(n.identifier.toLowerCase(), n);
  }

  const itemsByIdentifier = new Map<string, Item>();
  for (const i of itemsRaw) {
    itemsByIdentifier.set(i.identifier.toLowerCase(), i);
  }

  console.log(
    `[gamedata] Loaded: ${formsRaw.length} forms, ${movesRaw.length} moves, ${learnsets.size} learnsets, ${naturesRaw.length} natures, ${itemsRaw.length} items`,
  );

  return {
    formsByIdentifier,
    formsByPokemonId,
    formsAll: formsRaw,
    movesByIdentifier,
    movesAll: movesRaw,
    learnsets,
    statsByPokemonId,
    typesByPokemonId,
    abilitiesByPokemonId,
    abilitiesById,
    abilitiesAll: abilitiesRaw,
    naturesByIdentifier,
    naturesAll: naturesRaw,
    itemsByIdentifier,
    itemsAll: itemsRaw,
  };
}

export function displayName(identifier: string): string {
  return identifier
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function spriteUrl(pokemonId: number, shiny = false): string {
  const base =
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon";
  return shiny ? `${base}/shiny/${pokemonId}.png` : `${base}/${pokemonId}.png`;
}

export function getTypeNames(typeIds: number[]): string[] {
  return typeIds.map((id) => TYPE_NAMES[id] ?? "Unknown").filter(Boolean);
}
