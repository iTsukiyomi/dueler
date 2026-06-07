import { PokemonSlot } from '@/stores/teamStore';

// Helper to convert names to lower-case, hyphenated (e.g. "Choice Band" -> "choice-band")
function formatIdentifier(name: string): string {
  return name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

export function parseShowdownTeam(text: string): PokemonSlot[] {
  const pokemonBlocks = text.split(/\r?\n\r?\n/);
  const slots: PokemonSlot[] = [];
  let idCounter = 1;

  for (const block of pokemonBlocks) {
    const lines = block.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (lines.length === 0) continue;

    // Create a default slot
    const slot: PokemonSlot = {
      id: idCounter++,
      pokname: '',
      poknick: '',
      hpiv: 31, atkiv: 31, defiv: 31, spatkiv: 31, spdefiv: 31, speediv: 31,
      hpev: 0, atkev: 0, defev: 0, spatkev: 0, spdefev: 0, speedev: 0,
      moves: [],
      hitem: '',
      nature: 'Hardy',
      pokelevel: 100,
      happiness: 255,
      ability_index: 0,
      gender: 'M',
      shiny: false,
      radiant: false,
      skin: null,
    };

    // Parse Line 1: [Nick] [(Species)] [(M/F)] [@ Item]
    let firstLine = lines[0];
    
    // Extract item
    if (firstLine.includes(' @ ')) {
      const parts = firstLine.split(' @ ');
      slot.hitem = formatIdentifier(parts[1]);
      firstLine = parts[0];
    }

    // Extract gender
    if (firstLine.includes('(M)')) {
      slot.gender = 'M';
      firstLine = firstLine.replace('(M)', '').trim();
    } else if (firstLine.includes('(F)')) {
      slot.gender = 'F';
      firstLine = firstLine.replace('(F)', '').trim();
    } else if (firstLine.includes('(N)')) {
      slot.gender = 'N';
      firstLine = firstLine.replace('(N)', '').trim();
    }

    // Extract nickname and species
    const speciesMatch = firstLine.match(/(.+)\((.+)\)/);
    if (speciesMatch) {
      slot.poknick = speciesMatch[1].trim();
      slot.pokname = formatIdentifier(speciesMatch[2]);
    } else {
      slot.pokname = formatIdentifier(firstLine);
    }

    // Parse remaining lines
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];

      if (line.startsWith('-')) {
        // Move line
        const moveName = line.substring(1).trim();
        if (slot.moves.length < 4) {
          slot.moves.push(formatIdentifier(moveName));
        }
      } else if (line.startsWith('Ability:')) {
        // We set ability_index to 0, since we can't map ability string to index easily without database lookup.
        // The user can adjust this in the editor.
        slot.ability_index = 0;
      } else if (line.startsWith('Level:')) {
        slot.pokelevel = parseInt(line.replace('Level:', '').trim()) || 100;
      } else if (line.startsWith('Shiny:')) {
        slot.shiny = line.replace('Shiny:', '').trim().toLowerCase() === 'yes';
      } else if (line.startsWith('Happiness:')) {
        slot.happiness = parseInt(line.replace('Happiness:', '').trim()) || 255;
      } else if (line.includes('Nature')) {
        // Nature line (e.g. "Jolly Nature" or "Nature: Jolly")
        const natureName = line.replace('Nature', '').replace(':', '').trim();
        slot.nature = natureName.charAt(0).toUpperCase() + natureName.slice(1).toLowerCase();
      } else if (line.startsWith('EVs:')) {
        const evsText = line.replace('EVs:', '').trim();
        const evParts = evsText.split(' / ');
        for (const evPart of evParts) {
          const [valStr, stat] = evPart.trim().split(' ');
          const val = parseInt(valStr) || 0;
          const lowerStat = stat?.toLowerCase() || '';
          if (lowerStat.includes('hp')) slot.hpev = val;
          else if (lowerStat.includes('atk')) slot.atkev = val;
          else if (lowerStat.includes('def')) slot.defev = val;
          else if (lowerStat.includes('spa')) slot.spatkev = val;
          else if (lowerStat.includes('spd')) slot.spdefev = val;
          else if (lowerStat.includes('spe')) slot.speedev = val;
        }
      } else if (line.startsWith('IVs:')) {
        const ivsText = line.replace('IVs:', '').trim();
        const ivParts = ivsText.split(' / ');
        for (const ivPart of ivParts) {
          const [valStr, stat] = ivPart.trim().split(' ');
          const val = parseInt(valStr) === 0 ? 0 : (parseInt(valStr) || 31);
          const lowerStat = stat?.toLowerCase() || '';
          if (lowerStat.includes('hp')) slot.hpiv = val;
          else if (lowerStat.includes('atk')) slot.atkiv = val;
          else if (lowerStat.includes('def')) slot.defiv = val;
          else if (lowerStat.includes('spa')) slot.spatkiv = val;
          else if (lowerStat.includes('spd')) slot.spdefiv = val;
          else if (lowerStat.includes('spe')) slot.speediv = val;
        }
      }
    }

    // Pads moves to 4
    while (slot.moves.length < 4) {
      slot.moves.push('');
    }

    slots.push(slot);
    if (slots.length >= 6) break; // Maximum 6 Pokémon
  }

  return slots;
}

export function exportShowdownTeam(pokemon: PokemonSlot[]): string {
  let output = '';

  for (const slot of pokemon) {
    if (!slot.pokname) continue;

    // Header line: [Nick] [(Species)] [(M/F)] [@ Item]
    let header = '';
    const cleanPokname = slot.pokname.charAt(0).toUpperCase() + slot.pokname.slice(1).replace(/-/g, ' ');
    if (slot.poknick) {
      header += `${slot.poknick} (${cleanPokname})`;
    } else {
      header += cleanPokname;
    }

    if (slot.gender === 'F') header += ' (F)';
    if (slot.gender === 'M') header += ' (M)';

    if (slot.hitem) {
      const cleanItem = slot.hitem.charAt(0).toUpperCase() + slot.hitem.slice(1).replace(/-/g, ' ');
      header += ` @ ${cleanItem}`;
    }
    output += `${header}\n`;

    if (slot.pokelevel !== 100) {
      output += `Level: ${slot.pokelevel}\n`;
    }

    if (slot.shiny) {
      output += `Shiny: Yes\n`;
    }

    if (slot.happiness !== 255) {
      output += `Happiness: ${slot.happiness}\n`;
    }

    // EVs
    const evs: string[] = [];
    if (slot.hpev > 0) evs.push(`${slot.hpev} HP`);
    if (slot.atkev > 0) evs.push(`${slot.atkev} Atk`);
    if (slot.defev > 0) evs.push(`${slot.defev} Def`);
    if (slot.spatkev > 0) evs.push(`${slot.spatkev} SpA`);
    if (slot.spdefev > 0) evs.push(`${slot.spdefev} SpD`);
    if (slot.speedev > 0) evs.push(`${slot.speedev} Spe`);
    if (evs.length > 0) {
      output += `EVs: ${evs.join(' / ')}\n`;
    }

    // Nature
    output += `${slot.nature} Nature\n`;

    // IVs
    const ivs: string[] = [];
    if (slot.hpiv !== 31) ivs.push(`${slot.hpiv} HP`);
    if (slot.atkiv !== 31) ivs.push(`${slot.atkiv} Atk`);
    if (slot.defiv !== 31) ivs.push(`${slot.defiv} Def`);
    if (slot.spatkiv !== 31) ivs.push(`${slot.spatkiv} SpA`);
    if (slot.spdefiv !== 31) ivs.push(`${slot.spdefiv} SpD`);
    if (slot.speediv !== 31) ivs.push(`${slot.speediv} Spe`);
    if (ivs.length > 0) {
      output += `IVs: ${ivs.join(' / ')}\n`;
    }

    // Moves
    for (const move of slot.moves) {
      if (move) {
        const cleanMove = move.charAt(0).toUpperCase() + move.slice(1).replace(/-/g, ' ');
        output += `- ${cleanMove}\n`;
      }
    }

    output += '\n';
  }

  return output.trim();
}
