export interface Player {
  username: string;
  wins: number;
  losses: number;
  elo: number;
  wallet: number;
  active_party_name: string | null;
  theme: string;
  gen: number;
  rank: number | null;
}

export interface AuthUser {
  id: string;
  username: string;
  avatar: string;
  avatarUrl: string;
}

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

export interface Team {
  name: string;
  pokemon: PokemonSlot[];
  created_at?: string;
  updated_at?: string;
}

export interface TeamListItem {
  name: string;
  pokemon_count: number;
  pokemon: { pokname: string; pokemon_id: number; shiny: boolean }[];
  updated_at: string;
  is_active: boolean;
}

export interface GameDataPokemon {
  pokemon_id: number;
  identifier: string;
  display_name: string;
  sprite_url: string;
  sprite_url_shiny?: string;
  types: string[];
  type_ids?: number[];
  base_stats: {
    hp: number;
    atk: number;
    def: number;
    spa: number;
    spd: number;
    spe: number;
  } | null;
  abilities?: {
    ability_id: number;
    identifier: string;
    display_name: string;
    is_hidden: boolean;
    slot: number;
  }[];
  learnset?: string[];
  is_mega?: boolean;
  weight?: number;
}

export interface GameDataMove {
  id: number;
  identifier: string;
  display_name: string;
  type_name: string;
  type_id: number;
  damage_class: string;
  damage_class_id: number;
  power: number | null;
  pp: number;
  accuracy: number | null;
  priority: number;
}

export interface GameDataNature {
  identifier: string;
  display_name: string;
  increased_stat_id: number;
  decreased_stat_id: number;
  increases_stat: string | null;
  decreases_stat: string | null;
}

export interface GameDataItem {
  id: number;
  identifier: string;
  display_name: string;
}

export interface GameDataAbility {
  id: number;
  identifier: string;
  display_name: string;
}

export function defaultPokemonSlot(): PokemonSlot {
  return {
    id: 0,
    pokname: "",
    poknick: "",
    hpiv: 31,
    atkiv: 31,
    defiv: 31,
    spatkiv: 31,
    spdefiv: 31,
    speediv: 31,
    hpev: 0,
    atkev: 0,
    defev: 0,
    spatkev: 0,
    spdefev: 0,
    speedev: 0,
    moves: ["tackle", "tackle", "tackle", "tackle"],
    hitem: "",
    nature: "adamant",
    pokelevel: 100,
    happiness: 255,
    ability_index: 0,
    gender: "",
    shiny: false,
    radiant: false,
    skin: null,
  };
}
