import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths
const workspaceRoot = __dirname;
const formsPath = path.join(workspaceRoot, 'pokemonduel/data/forms.json');
const typesPath = path.join(workspaceRoot, 'pokemonduel/data/ptypes.json');
const userDataDir = path.join(workspaceRoot, 'data/PokemonDuel');
const destDir = path.join(workspaceRoot, 'frontend/public/pokemon-icons');
const destTypesDir = path.join(destDir, 'types');

// Ensure directories exist
fs.mkdirSync(destDir, { recursive: true });
fs.mkdirSync(destTypesDir, { recursive: true });

async function downloadFile(url, destPath) {
  if (fs.existsSync(destPath)) {
    return; // Already downloaded
  }
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const arrayBuffer = await res.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    fs.writeFileSync(destPath, buffer);
  } catch (error) {
    console.error(`Failed to download ${url}: ${error.message}`);
  }
}

async function run() {
  console.log('🔮 Starting Pokémon assets download...');

  // 1. Read forms and ptypes
  if (!fs.existsSync(formsPath)) {
    console.error(`forms.json not found at ${formsPath}`);
    process.exit(1);
  }
  const forms = JSON.parse(fs.readFileSync(formsPath, 'utf-8'));
  const ptypes = fs.existsSync(typesPath) ? JSON.parse(fs.readFileSync(typesPath, 'utf-8')) : [];

  // Create lookup map of name -> forms
  const nameToForm = new Map();
  for (const form of forms) {
    nameToForm.set(form.identifier.toLowerCase(), form);
  }

  // 2. Determine target Pokémon IDs to download
  const targetIds = new Set();

  // Add Gen 1 & 2 (1 to 251)
  for (let id = 1; id <= 251; id++) {
    targetIds.add(id);
  }

  // Scan user files in data/PokemonDuel/ for other Pokémon used in active squads
  if (fs.existsSync(userDataDir)) {
    const files = fs.readdirSync(userDataDir);
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const content = JSON.parse(fs.readFileSync(path.join(userDataDir, file), 'utf-8'));
          const party = content.party || [];
          for (const member of party) {
            if (member.pokname) {
              const nameLower = member.pokname.toLowerCase();
              const form = nameToForm.get(nameLower) || forms.find(f => f.identifier.toLowerCase().replace(/[^a-z0-9]/g, '') === nameLower.replace(/[^a-z0-9]/g, ''));
              if (form) {
                targetIds.add(form.pokemon_id);
              } else {
                console.warn(`Could not resolve Pokémon name: ${member.pokname}`);
              }
            }
          }
        } catch (e) {
          console.error(`Error reading user file ${file}:`, e.message);
        }
      }
    }
  }

  console.log(`Resolved ${targetIds.size} unique Pokémon to download.`);

  // 3. Download sprites (concurrently in batches)
  const idArray = Array.from(targetIds).sort((a, b) => a - b);
  const BATCH_SIZE = 15;
  
  for (let i = 0; i < idArray.length; i += BATCH_SIZE) {
    const batch = idArray.slice(i, i + BATCH_SIZE);
    console.log(`Downloading sprites batch ${i / BATCH_SIZE + 1}/${Math.ceil(idArray.length / BATCH_SIZE)}...`);
    
    await Promise.all(batch.map(async (id) => {
      const standardUrl = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`;
      const shinyUrl = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/${id}.png`;
      
      await downloadFile(standardUrl, path.join(destDir, `${id}.png`));
      await downloadFile(shinyUrl, path.join(destDir, `shiny-${id}.png`));
    }));
  }

  // 4. Download type SVGs
  const types = [
    'normal', 'fire', 'water', 'electric', 'grass', 'ice',
    'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
    'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy'
  ];
  
  console.log('Downloading Pokémon type SVGs...');
  await Promise.all(types.map(async (type) => {
    const typeUrl = `https://raw.githubusercontent.com/duiker101/pokemon-type-svg-icons/master/icons/${type}.svg`;
    await downloadFile(typeUrl, path.join(destTypesDir, `${type}.svg`));
  }));

  // 5. Generate manifest.json
  const manifest = {
    types,
    pokemon: []
  };

  // Build type mapping from ptypes.json
  const typeMap = {
    1: 'normal', 2: 'fighting', 3: 'flying', 4: 'poison', 5: 'ground',
    6: 'rock', 7: 'bug', 8: 'ghost', 9: 'steel', 10: 'fire',
    11: 'water', 12: 'grass', 13: 'electric', 14: 'psychic', 15: 'ice',
    16: 'dragon', 17: 'dark', 18: 'fairy'
  };

  for (const form of forms) {
    if (form.is_default || targetIds.has(form.pokemon_id)) {
      const typeData = ptypes.find(p => p.id === form.pokemon_id);
      const pokeTypes = typeData ? typeData.types.map(tid => typeMap[tid]).filter(Boolean) : ['normal'];
      
      manifest.pokemon.push({
        id: form.pokemon_id,
        name: form.identifier,
        types: pokeTypes
      });
    }
  }

  fs.writeFileSync(path.join(destDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log('🎉 Pokémon assets download and manifest generation complete!');
}

run().catch(console.error);
