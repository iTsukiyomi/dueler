import type { GameDataNature } from "../types";

export function calcStat(
  statName: "hp" | "atk" | "def" | "spa" | "spd" | "spe",
  base: number,
  iv: number,
  ev: number,
  level: number,
  nature?: GameDataNature,
): number {
  if (statName === "hp") {
    if (base === 1) return 1; // Shedinja
    return (
      Math.floor(((2 * base + iv + Math.floor(ev / 4)) * level) / 100) +
      level +
      10
    );
  }

  let stat =
    Math.floor(((2 * base + iv + Math.floor(ev / 4)) * level) / 100) + 5;

  if (nature) {
    const statIdMap: Record<string, number> = {
      hp: 1,
      atk: 2,
      def: 3,
      spa: 4,
      spd: 5,
      spe: 6,
    };
    const statId = statIdMap[statName];
    if (
      nature.increased_stat_id !== nature.decreased_stat_id &&
      nature.increased_stat_id === statId
    ) {
      stat = Math.floor(stat * 1.1);
    } else if (
      nature.increased_stat_id !== nature.decreased_stat_id &&
      nature.decreased_stat_id === statId
    ) {
      stat = Math.floor(stat * 0.9);
    }
  }

  return stat;
}

export function displayName(identifier: string): string {
  return identifier
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function spriteUrl(pokemonId: number, shiny = false): string {
  if (!pokemonId) return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%233D5068' stroke-width='1.5'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='2' y1='12' x2='22' y2='12'/%3E%3C/svg%3E";
  return `/pokemon-icons/${shiny ? "shiny-" : ""}${pokemonId}.png`;
}

export function totalEvs(slot: {
  hpev: number;
  atkev: number;
  defev: number;
  spatkev: number;
  spdefev: number;
  speedev: number;
}): number {
  return (
    slot.hpev +
    slot.atkev +
    slot.defev +
    slot.spatkev +
    slot.spdefev +
    slot.speedev
  );
}

export const TYPE_COLORS: Record<string, string> = {
  Normal: "#a8a878",
  Fire: "#f08030",
  Water: "#6890f0",
  Electric: "#f8d030",
  Grass: "#78c850",
  Ice: "#98d8d8",
  Fighting: "#c03028",
  Poison: "#a040a0",
  Ground: "#e0c068",
  Flying: "#a890f0",
  Psychic: "#f85888",
  Bug: "#a8b820",
  Rock: "#b8a038",
  Ghost: "#705898",
  Dragon: "#7038f8",
  Dark: "#705848",
  Steel: "#b8b8d0",
  Fairy: "#ee99ac",
};
