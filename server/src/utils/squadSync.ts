import { writeFileSync, readFileSync, existsSync } from "fs";
import { join } from "path";
import { config } from "../config.js";
import { PokemonSlot } from "./validation.js";

const mapPokemonSlotToBot = (slot: PokemonSlot): any => {
  let mappedGender = "-x";
  const g = (slot.gender || "").toLowerCase();
  if (g.includes("m") || g === "male") mappedGender = "-m";
  else if (g.includes("f") || g === "female") mappedGender = "-f";
  else if (g.includes("x") || g === "genderless") mappedGender = "-x";

  // Format moves to exactly 4 items, filtering out blank ones
  const moves = Array.isArray(slot.moves)
    ? slot.moves.map(m => typeof m === "string" ? m.trim().toLowerCase() : "").filter(Boolean)
    : [];
  while (moves.length < 4) {
    moves.push("");
  }

  return {
    id: typeof slot.id === "number" ? slot.id : 0,
    pokname: typeof slot.pokname === "string" ? slot.pokname.trim() : "",
    hpiv: typeof slot.hpiv === "number" ? slot.hpiv : 31,
    atkiv: typeof slot.atkiv === "number" ? slot.atkiv : 31,
    defiv: typeof slot.defiv === "number" ? slot.defiv : 31,
    spatkiv: typeof slot.spatkiv === "number" ? slot.spatkiv : 31,
    spdefiv: typeof slot.spdefiv === "number" ? slot.spdefiv : 31,
    speediv: typeof slot.speediv === "number" ? slot.speediv : 31,
    hpev: typeof slot.hpev === "number" ? slot.hpev : 0,
    atkev: typeof slot.atkev === "number" ? slot.atkev : 0,
    defev: typeof slot.defev === "number" ? slot.defev : 0,
    spatkev: typeof slot.spatkev === "number" ? slot.spatkev : 0,
    spdefev: typeof slot.spdefev === "number" ? slot.spdefev : 0,
    speedev: typeof slot.speedev === "number" ? slot.speedev : 0,
    moves: moves.slice(0, 4),
    hitem: typeof slot.hitem === "string" ? slot.hitem.trim().toLowerCase() : "",
    nature: typeof slot.nature === "string" ? slot.nature.trim() : "Hardy",
    poknick: typeof slot.poknick === "string" && slot.poknick.trim() ? slot.poknick.trim() : "None",
    pokelevel: typeof slot.pokelevel === "number" ? slot.pokelevel : 100,
    happiness: typeof slot.happiness === "number" ? slot.happiness : 255,
    ability_index: typeof slot.ability_index === "number" ? slot.ability_index : 0,
    gender: mappedGender,
    shiny: !!slot.shiny,
    radiant: !!slot.radiant,
    skin: slot.skin || null,
  };
};

export function syncActivePartyToDiscord(userId: string, pokemon: PokemonSlot[]): void {
  try {
    const userConfigFile = join(config.userConfigDir, `member_${userId}.json`);
    let data: any = {};
    if (existsSync(userConfigFile)) {
      try {
        const raw = readFileSync(userConfigFile, "utf-8");
        data = JSON.parse(raw);
      } catch (e) {
        console.error(`[squadSync] Failed to read/parse existing config for ${userId}:`, e);
      }
    }
    
    data.party = pokemon.map(mapPokemonSlotToBot);
    
    writeFileSync(userConfigFile, JSON.stringify(data, null, 4), "utf-8");
    console.log(`[squadSync] Successfully synchronized party to ${userConfigFile}`);
  } catch (error) {
    console.error(`[squadSync] Error synchronizing party for ${userId}:`, error);
  }
}
