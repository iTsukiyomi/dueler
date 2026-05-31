import type { PokemonSlot } from "../types";
import { totalEvs } from "./pokemon";

export function validateSlotClient(slot: PokemonSlot): string[] {
  const errors: string[] = [];

  if (!slot.pokname) errors.push("No Pokémon selected");
  if (!slot.moves || slot.moves.length !== 4) errors.push("4 moves required");

  const evTotal = totalEvs(slot);
  if (evTotal > 510) errors.push(`EV total ${evTotal} exceeds 510`);

  const evFields = ["hpev", "atkev", "defev", "spatkev", "spdefev", "speedev"] as const;
  for (const f of evFields) {
    if (slot[f] < 0 || slot[f] > 252) errors.push(`${f} must be 0-252`);
  }

  const ivFields = ["hpiv", "atkiv", "defiv", "spatkiv", "spdefiv", "speediv"] as const;
  for (const f of ivFields) {
    if (slot[f] < 0 || slot[f] > 31) errors.push(`${f} must be 0-31`);
  }

  return errors;
}
