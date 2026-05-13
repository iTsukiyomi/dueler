"""
Random Team Generator - Port of Pokemon Showdown's random battle team generator
Uses sets.json for Pokemon data
"""

import json
import random
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

# Path to data files
SETS_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'sets.json'
PFILE_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'pfile.json'
PSTATS_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'pokemon_stats.json'
FORMS_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'forms.json'
PTYPES_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'ptypes.json'
TEFF_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'type_effectiveness.json'
ABILITY_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'abilities.json'
MOVES_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'moves.json'
POKE_ABILITIES_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'poke_abilities.json'

# Data caches
_PFILE_DATA = None
_PSTATS_DATA = None
_FORMS_DATA = None
_PTYPES_DATA = None
_TEFF_DATA = None
_ABILITY_DATA = None
_SETS_DATA = None
_MOVES_DATA = None
_POKE_ABILITIES_DATA = None

# Pokemon name to form ID mapping (built on first use)
_PNAME_TO_FORM_ID = None

# ============================================
# NORMALIZATION
# ============================================

def normalize_id(text: str) -> str:
    """Centralized ID normalization - removes spaces, hyphens, underscores"""
    return (
        text.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )

# ============================================
# NATURES
# ============================================

NATURES_JSON_PATH = Path(__file__).parent.parent.parent / 'data' / 'natures.json'
_NATURE_DATA = None

def _load_natures_data():
    global _NATURE_DATA
    if _NATURE_DATA is None:
        with open(NATURES_JSON_PATH, 'r') as f:
            _NATURE_DATA = json.load(f)
    return _NATURE_DATA

# Nature stat mapping (stat_id: 1=HP, 2=Atk, 3=Def, 4=SpA, 5=SpD, 6=Spe)
# decreased_stat_id and increased_stat_id define the nature
_NATURE_LOOKUP = None

def _build_nature_lookup():
    global _NATURE_LOOKUP
    if _NATURE_LOOKUP is not None:
        return _NATURE_LOOKUP

    natures = _load_natures_data()
    _NATURE_LOOKUP = {}

    for n in natures:
        increased = n.get('increased_stat_id', 2)
        decreased = n.get('decreased_stat_id', 2)

        # Build lookup by (increased_stat, decreased_stat)
        identifier = n.get('identifier', 'hardy')

        # Map to stat names
        stat_map = {1: 'hp', 2: 'atk', 3: 'def', 4: 'spa', 5: 'spd', 6: 'spe'}
        inc_stat = stat_map.get(increased, 'atk')
        dec_stat = stat_map.get(decreased, 'def')

        _NATURE_LOOKUP[(inc_stat, dec_stat)] = identifier

    return _NATURE_LOOKUP

def get_nature_id(nature_name: str) -> int:
    """Get nature ID from name"""
    natures = _load_natures_data()
    norm = normalize_id(nature_name)
    for n in natures:
        if normalize_id(n.get('identifier', '')) == norm:
            return n.get('id', 1)
    return 1

def get_nature_for_role(role: str, counter: MoveCounter, base_stats: Dict, types: Set[str]) -> str:
    """Select appropriate nature based on role and stats"""
    nature_lookup = _build_nature_lookup()

    atk = base_stats.get('atk', 100)
    spa = base_stats.get('spa', 100)
    spe = base_stats.get('spe', 100)
    def_stat = base_stats.get('def', 100)
    spd = base_stats.get('spd', 100)

    # Setup roles
    if 'Setup' in role or role == 'Wallbreaker':
        if counter.get('Physical', 0) > counter.get('Special', 0):
            return nature_lookup.get(('atk', 'spd'), 'Adamant')
        return nature_lookup.get(('spa', 'atk'), 'Modest')

    # Fast attacker
    if 'Fast' in role:
        if counter.get('Physical', 0) > counter.get('Special', 0):
            return nature_lookup.get(('spe', 'def'), 'Jolly')
        return nature_lookup.get(('spe', 'atk'), 'Timid')

    # Bulky roles
    if 'Bulky' in role:
        if counter.get('Physical', 0) > counter.get('Special', 0):
            return nature_lookup.get(('def', 'spe'), 'Bold')
        return nature_lookup.get(('spd', 'atk'), 'Calm')

    # Default based on move spread
    if counter.get('Physical', 0) >= 2:
        return nature_lookup.get(('atk', 'spa'), 'Adamant')
    elif counter.get('Special', 0) >= 2:
        return nature_lookup.get(('spa', 'atk'), 'Modest')
    elif counter.get('Physical', 0) == counter.get('Special', 0):
        return nature_lookup.get(('spe', 'def'), 'Jolly')

    return 'Hardy'

def _load_pfile_data():
    global _PFILE_DATA
    if _PFILE_DATA is None:
        with open(PFILE_JSON_PATH, 'r') as f:
            _PFILE_DATA = json.load(f)
    return _PFILE_DATA

def _load_pstats_data():
    global _PSTATS_DATA
    if _PSTATS_DATA is None:
        with open(PSTATS_JSON_PATH, 'r') as f:
            _PSTATS_DATA = json.load(f)
    return _PSTATS_DATA

def _load_forms_data():
    global _FORMS_DATA
    if _FORMS_DATA is None:
        with open(FORMS_JSON_PATH, 'r') as f:
            _FORMS_DATA = json.load(f)
    return _FORMS_DATA

def _load_ptypes_data():
    global _PTYPES_DATA
    if _PTYPES_DATA is None:
        with open(PTYPES_JSON_PATH, 'r') as f:
            _PTYPES_DATA = json.load(f)
    return _PTYPES_DATA

def _load_teff_data():
    global _TEFF_DATA
    if _TEFF_DATA is None:
        with open(TEFF_JSON_PATH, 'r') as f:
            _TEFF_DATA = json.load(f)
    return _TEFF_DATA

def _load_ability_data():
    global _ABILITY_DATA
    if _ABILITY_DATA is None:
        with open(ABILITY_JSON_PATH, 'r') as f:
            _ABILITY_DATA = json.load(f)
    return _ABILITY_DATA

def _load_sets_data():
    global _SETS_DATA
    if _SETS_DATA is None:
        with open(SETS_JSON_PATH, 'r') as f:
            _SETS_DATA = json.load(f)
    return _SETS_DATA

def _load_moves_data():
    global _MOVES_DATA
    if _MOVES_DATA is None:
        with open(MOVES_JSON_PATH, 'r') as f:
            _MOVES_DATA = json.load(f)
    return _MOVES_DATA

def _load_poke_abilities_data():
    global _POKE_ABILITIES_DATA
    if _POKE_ABILITIES_DATA is None:
        with open(POKE_ABILITIES_JSON_PATH, 'r') as f:
            _POKE_ABILITIES_DATA = json.load(f)
    return _POKE_ABILITIES_DATA

# Build move lookup: identifier -> move data with normalized keys
_MOVE_DATA = None

# Damage class ID to name mapping (from moves.json)
DAMAGE_CLASS = {1: 'Status', 2: 'Physical', 3: 'Special'}

def _get_move_data():
    """Load and normalize move data from moves.json"""
    global _MOVE_DATA
    if _MOVE_DATA is not None:
        return _MOVE_DATA

    moves = _load_moves_data()
    _MOVE_DATA = {}

    for m in moves:
        move_id = m.get('identifier', '').lower()
        # Store normalized move data with both hyphen and no-hyphen versions
        move_info = {
            'type_id': m.get('type_id', 1),
            'type': TYPE_ID_TO_NAME.get(m.get('type_id', 1), 'normal'),
            'category': DAMAGE_CLASS.get(m.get('damage_class_id', 1), 'Status'),
            'power': m.get('power'),
            'priority': m.get('priority', 0),
            'accuracy': m.get('accuracy'),
        }
        # Store with original identifier (may have hyphens)
        _MOVE_DATA[move_id] = move_info
        # Also store with hyphens removed for matching
        _MOVE_DATA[move_id.replace('-', '')] = move_info

    return _MOVE_DATA

def _get_move_info(move_identifier: str):
    """Get move data from moves.json by identifier"""
    # Normalize: remove spaces, hyphens, underscores
    move_id = move_identifier.lower().replace(' ', '-').replace('_', '')
    move_data = _get_move_data()

    # Try original with hyphens first, then without
    if move_id in move_data:
        return move_data[move_id]
    # Try without hyphens
    if move_id.replace('-', '') in move_data:
        return move_data[move_id.replace('-', '')]
    return None

def _build_pname_to_form_id_map():
    """Build mapping from sets.json pokemon names to forms.json IDs"""
    global _PNAME_TO_FORM_ID
    if _PNAME_TO_FORM_ID is not None:
        return _PNAME_TO_FORM_ID

    sets_data = _load_sets_data()
    forms = _load_forms_data()
    ptypes = _load_ptypes_data()

    # Build set of valid ptypes IDs for quick lookup
    valid_ptype_ids = {pt.get('id') for pt in ptypes}

    _PNAME_TO_FORM_ID = {}

    for pname in sets_data.keys():
        # Normalize sets.json name
        search_name = pname.lower().replace('-', '').replace(' ', '').replace('_', '')

        # Try to find matching form - prefer forms with valid ptypes entries
        best_match = None
        best_match_len = 0
        best_base_id = None

        for entry in forms:
            identifier = entry.get('identifier', '').replace('-', '').replace(' ', '').replace('_', '')
            # Check if search_name is at the start and is a significant match
            if identifier.startswith(search_name) and len(search_name) > best_match_len:
                form_id = entry.get('id')
                pokemon_id = entry.get('pokemon_id', form_id)

                # Only consider if ptypes has an entry for this pokemon
                if pokemon_id in valid_ptype_ids or form_id in valid_ptype_ids:
                    best_match = form_id
                    best_base_id = pokemon_id
                    best_match_len = len(search_name)

        if best_match:
            # Store both form_id and the base pokemon_id for ptypes lookup
            _PNAME_TO_FORM_ID[pname] = (best_match, best_base_id if best_base_id else best_match)

    return _PNAME_TO_FORM_ID

# Type name to ID mapping
TYPE_NAME_TO_ID = {
    'normal': 1, 'fighting': 2, 'flying': 3, 'poison': 4, 'ground': 5,
    'rock': 6, 'bug': 7, 'ghost': 8, 'steel': 9, 'fire': 10,
    'water': 11, 'grass': 12, 'electric': 13, 'psychic': 14, 'ice': 15,
    'dragon': 16, 'dark': 17, 'fairy': 18, 'typeless': 19,
}

# Type ID to name mapping
TYPE_ID_TO_NAME = {v: k for k, v in TYPE_NAME_TO_ID.items()}

def get_pokemon_id_and_types(pokemon_name: str) -> Tuple[int, List[int]]:
    """Get pokemon ID and type IDs from forms.json and ptypes.json"""
    ptypes = _load_ptypes_data()

    # Use pre-built mapping from sets.json names to form IDs
    pname_map = _build_pname_to_form_id_map()

    mapping = pname_map.get(pokemon_name)

    if mapping is None:
        return 1, [1]  # Default to normal type

    form_id, lookup_id = mapping  # form_id for forms.json, lookup_id for ptypes.json

    # Look up types in ptypes using the lookup_id
    for pt in ptypes:
        if pt.get('id') == lookup_id:
            return form_id, pt.get('types', [])

    return 1, [1]  # Default if type not found

def get_ability_id(ability_name: str) -> int:
    """Get ability ID from ability name"""
    abilities = _load_ability_data()
    search_name = ability_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    for ab in abilities:
        identifier = ab.get('identifier', '').replace(' ', '').replace('-', '').replace('_', '')
        if identifier == search_name:
            return ab.get('id', 1)
    return 1  # Default to first ability

def get_pokemon_base_stats(pokemon_name: str) -> Dict[str, int]:
    """Get base stats for a pokemon by name"""
    pfile = _load_pfile_data()
    pstats = _load_pstats_data()

    # Find pokemon by identifier (lowercase, no hyphens)
    pokemon_id = pokemon_name.lower().replace('-', '').replace(' ', '')

    for entry in pfile:
        if entry.get('identifier', '').replace('-', '').replace(' ', '') == pokemon_id:
            pid = entry.get('id')
            # Get stats (index 0=hp, 1=atk, 2=def, 3=spa, 4=spd, 5=spe)
            for stat_entry in pstats:
                if stat_entry.get('pokemon_id') == pid:
                    stats = stat_entry.get('stats', [])
                    return {
                        'hp': stats[0] if len(stats) > 0 else 0,
                        'atk': stats[1] if len(stats) > 1 else 0,
                        'def': stats[2] if len(stats) > 2 else 0,
                        'spa': stats[3] if len(stats) > 3 else 0,
                        'spd': stats[4] if len(stats) > 4 else 0,
                        'spe': stats[5] if len(stats) > 5 else 0,
                    }
    return {}

def get_type_effectiveness(attack_type: int, defend_types: List[int]) -> float:
    """Get type effectiveness multiplier"""
    teff = _load_teff_data()
    multiplier = 1.0
    for dt in defend_types:
        for entry in teff:
            if entry.get('damage_type_id') == attack_type and entry.get('target_type_id') == dt:
                multiplier *= entry.get('damage_factor', 100) / 100
                break
    return multiplier

# ============================================
# CONSTANTS (copied from teams.ts)
# ============================================

RECOVERY_MOVES = [
    'healorder', 'milkdrink', 'moonlight', 'morningsun', 'recover', 'roost', 'shoreup', 'slackoff', 'softboiled', 'strengthsap', 'synthesis',
]

CONTRARY_MOVES = [
    'armorcannon', 'closecombat', 'leafstorm', 'makeitrain', 'overheat', 'spinout', 'superpower', 'vcreate',
]

PHYSICAL_SETUP = [
    'bellydrum', 'bulkup', 'coil', 'curse', 'dragondance', 'honeclaws', 'howl', 'meditate', 'poweruppunch', 'swordsdance', 'tidyup', 'victorydance',
]

SPECIAL_SETUP = [
    'calmmind', 'chargebeam', 'geomancy', 'nastyplot', 'quiverdance', 'tailglow', 'takeheart', 'torchsong',
]

MIXED_SETUP = [
    'clangoroussoul', 'growth', 'happyhour', 'holdhands', 'noretreat', 'shellsmash', 'workup',
]

SPEED_SETUP = [
    'agility', 'autotomize', 'flamecharge', 'rockpolish', 'snowscape', 'trailblaze',
]

SETUP = [
    'acidarmor', 'agility', 'autotomize', 'bellydrum', 'bulkup', 'calmmind', 'clangoroussoul', 'coil', 'cosmicpower', 'curse', 'dragondance',
    'flamecharge', 'growth', 'honeclaws', 'howl', 'irondefense', 'meditate', 'nastyplot', 'noretreat', 'poweruppunch', 'quiverdance',
    'rockpolish', 'shellsmash', 'shiftgear', 'swordsdance', 'tailglow', 'takeheart', 'tidyup', 'trailblaze', 'workup', 'victorydance',
]

SPEED_CONTROL = [
    'electroweb', 'glare', 'icywind', 'lowsweep', 'nuzzle', 'quash', 'tailwind', 'thunderwave', 'trickroom',
]

NO_STAB = [
    'acidspray', 'accelerock', 'aquajet', 'bounce', 'breakingswipe', 'bulletpunch', 'chatter', 'chloroblast', 'clearsmog', 'covet',
    'dragontail', 'doomdesire', 'electroweb', 'eruption', 'explosion', 'fakeout', 'feint', 'flamecharge', 'flipturn', 'futuresight',
    'grassyglide', 'iceshard', 'icywind', 'incinerate', 'infestation', 'machpunch', 'meteorbeam', 'mortalspin', 'nuzzle', 'pluck', 'pursuit',
    'quickattack', 'rapidspin', 'reversal', 'selfdestruct', 'shadowsneak', 'skydrop', 'snarl', 'strugglebug', 'suckerpunch', 'trailblaze',
    'uturn', 'vacuumwave', 'voltswitch', 'watershuriken', 'waterspout',
]

HAZARDS = [
    'spikes', 'stealthrock', 'stickyweb', 'toxicspikes',
]

PROTECT_MOVES = [
    'banefulbunker', 'burningbulwark', 'protect', 'silktrap', 'spikyshield',
]

PIVOT_MOVES = [
    'chillyreception', 'flipturn', 'partingshot', 'shedtail', 'teleport', 'uturn', 'voltswitch',
]

MOVE_PAIRS = [
    ['lightscreen', 'reflect'],
    ['sleeptalk', 'rest'],
    ['protect', 'wish'],
    ['leechseed', 'protect'],
    ['leechseed', 'substitute'],
    ['perishsong', 'protect'],
]

PRIORITY_POKEMON = [
    'breloom', 'brutebonnet', 'cacturne', 'honchkrow', 'mimikyu', 'ragingbolt', 'scizor',
]

NO_LEAD_POKEMON = [
    'Zacian', 'Zamazenta',
]

DEFENSIVE_TERA_BLAST_USERS = [
    'alcremie', 'bellossom', 'comfey', 'fezandipiti', 'florges',
]

# Move enforcement checkers - these ensure certain types get moves
MOVE_ENFORCEMENT_CHECKERS = {
    'Bug': lambda pool, moves, abilities, types, counter, species: (
        'megahorn' in pool or 'pinmissile' in pool or 'xscissor' in pool or
        ('Bug' not in types and ('Electric' in types or 'Psychic' in types))
    ),
    'Dark': lambda pool, moves, abilities, types, counter, species: (
        counter.get('Dark', 0) < 2 and species.get('id') in PRIORITY_POKEMON and 'Wallbreaker' in str(counter)
    ) or counter.get('Dark', 0) == 0,
    'Dragon': lambda pool, moves, abilities, types, counter, species: counter.get('Dragon', 0) == 0,
    'Electric': lambda pool, moves, abilities, types, counter, species: counter.get('Electric', 0) == 0,
    'Fairy': lambda pool, moves, abilities, types, counter, species: counter.get('Fairy', 0) == 0,
    'Fighting': lambda pool, moves, abilities, types, counter, species: counter.get('Fighting', 0) == 0,
    'Fire': lambda pool, moves, abilities, types, counter, species: counter.get('Fire', 0) == 0,
    'Flying': lambda pool, moves, abilities, types, counter, species: counter.get('Flying', 0) == 0,
    'Ghost': lambda pool, moves, abilities, types, counter, species: counter.get('Ghost', 0) == 0,
    'Grass': lambda pool, moves, abilities, types, counter, species: (
        counter.get('Grass', 0) == 0 and ('leafstorm' in pool or species.get('base_stats', {}).get('atk', 100) >= 100 or 'Electric' in types or 'Seed Sower' in abilities)
    ),
    'Ground': lambda pool, moves, abilities, types, counter, species: counter.get('Ground', 0) == 0,
    'Ice': lambda pool, moves, abilities, types, counter, species: 'freezedry' in pool or 'blizzard' in pool or counter.get('Ice', 0) == 0,
    'Normal': lambda pool, moves, types, counter: 'boomburst' in pool or 'hypervoice' in pool,
    'Poison': lambda pool, moves, abilities, types, counter: 'Ground' not in types and counter.get('Poison', 0) == 0,
    'Psychic': lambda pool, moves, abilities, types, counter, species: (
        ('psychic' in pool and species.get('id') == 'hoopaunbound') or
        (not any(t in ['Dark', 'Steel', 'Water'] for t in types) and counter.get('Psychic', 0) == 0)
    ),
    'Rock': lambda pool, moves, abilities, types, counter, species: counter.get('Rock', 0) == 0 and species.get('base_stats', {}).get('atk', 80) >= 80,
    'Steel': lambda pool, moves, abilities, types, counter, species: (
        counter.get('Steel', 0) == 0 and (species.get('base_stats', {}).get('atk', 90) >= 90 or 'gigatonhammer' in pool or 'makeitrain' in pool)
    ),
    'Water': lambda pool, moves, abilities, types, counter, species: counter.get('Water', 0) == 0 and ('Ground' not in types),
}


class MoveCounter:
    """Tracks move properties for decision making"""

    def __init__(self):
        self.counts = {}
        self.damaging_moves = set()
        self.base_power_moves = set()

    def add(self, key: str, value: int = 1):
        self.counts[key] = self.counts.get(key, 0) + value

    def get(self, key: str, default: int = 0) -> int:
        return self.counts.get(key, default)

    def set(self, key: str, value: int):
        self.counts[key] = value


# ============================================
# RANDOM TEAM GENERATOR CLASS
# ============================================

class RandomTeamGenerator:
    """Generates random Pokemon teams using Showdown logic"""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.sets_data = self._load_sets()
        self.max_team_size = 6
        self.max_move_count = 4

    def _load_sets(self) -> Dict:
        """Load sets.json"""
        with open(SETS_JSON_PATH, 'r') as f:
            return json.load(f)

    # ============================================
    # RANDOM HELPERS
    # ============================================

    def sample(self, items: List) -> Any:
        return random.choice(items)

    def sample_no_replace(self, items: List) -> Any:
        idx = random.randint(0, len(items) - 1)
        return items.pop(idx)

    def randomChance(self, numerator: int, denominator: int) -> bool:
        return random.randint(1, denominator) <= numerator

    def fast_pop(self, lst: List, index: int):
        """Remove element at index efficiently"""
        lst[index] = lst[-1]
        lst.pop()

    # ============================================
    # LEVEL
    # ============================================

    def get_level(self, pokemon_name: str) -> int:
        """Get level from sets.json"""
        if pokemon_name in self.sets_data:
            return self.sets_data[pokemon_name].get('level', 50)
        return 50

    # ============================================
    # MOVE QUERYING
    # ============================================

    def get_move_type(self, move_id: str, species_types: List[str], abilities: List[str], tera_type: str) -> str:
        """Get the type of a move considering abilities and tera"""
        # Normalize move_id
        move_id = move_id.lower().replace(' ', '-')

        # Tera Blast uses tera type
        if move_id == 'terablast':
            return tera_type

        # Revelation Dance uses first type
        if move_id == 'revelationdance':
            return species_types[0] if species_types else 'Normal'

        # Get actual move type from moves.json
        move_data = _get_move_info(move_id)
        if move_data:
            move_type = move_data.get('type', 'Normal')
            # Handle abilities that change move types
            if 'Normalize' in abilities:
                return 'Normal'
            return move_type

        # Fallback to Normal if not found
        return 'Normal'

    def get_move_category(self, move_id: str) -> str:
        """Get move category (Physical/Special/Status) from moves.json"""
        move_id = move_id.lower().replace(' ', '-')
        move_data = _get_move_info(move_id)
        if move_data:
            return move_data.get('category', 'Status')
        return 'Status'

    def get_move_power(self, move_id: str) -> Optional[int]:
        """Get move base power from moves.json"""
        move_id = move_id.lower().replace(' ', '-')
        move_data = _get_move_info(move_id)
        if move_data:
            return move_data.get('power')
        return None

    def query_moves(self, moves: Set[str], species_types: List[str], tera_type: str, abilities: List[str]) -> MoveCounter:
        """Analyze what moves do"""
        counter = MoveCounter()
        types_set = set(species_types)

        if not moves:
            return counter

        categories = {'Physical': 0, 'Special': 0, 'Status': 0}

        for move_id in moves:
            move_type = self.get_move_type(move_id, species_types, abilities, tera_type)
            move_category = self.get_move_category(move_id)

            # Track categories using real move data
            categories[move_category] += 1
            counter.add(move_category)

            # STAB tracking - normalize move_type to title case for comparison
            move_type_normalized = move_type.title() if move_type else None
            if move_type_normalized and move_type_normalized in types_set and move_id not in NO_STAB:
                counter.add(move_type_normalized)
                counter.add('stab')
                if move_type_normalized == tera_type.title():
                    counter.add('stabtera')
                counter.damaging_moves.add(move_id)

            # Setup moves
            if move_id in RECOVERY_MOVES:
                counter.add('recovery')
            if move_id in CONTRARY_MOVES:
                counter.add('contrary')
            if move_id in PHYSICAL_SETUP:
                counter.add('physicalsetup')
            if move_id in SPECIAL_SETUP:
                counter.add('specialsetup')
            if move_id in MIXED_SETUP:
                counter.add('mixedsetup')
            if move_id in SPEED_SETUP:
                counter.add('speedsetup')
            if move_id in SPEED_CONTROL:
                counter.add('speedcontrol')
            if move_id in SETUP:
                counter.add('setup')
            if move_id in HAZARDS:
                counter.add('hazards')

            # Priority - use actual move priority from moves.json
            move_priority = 0
            move_data = _get_move_info(move_id.lower().replace(' ', '-'))
            if move_data:
                move_priority = move_data.get('priority', 0)
            if move_priority > 0:
                counter.add('priority')

            # Pivot moves (NOT recoil - they're switching moves)
            if move_id in ['flareblitz', 'bravebird', 'doubleedge']:
                counter.add('recoil')

            # Skill Link (only multi-hit moves)
            if move_id in ['bulletseed', 'pinmissile', 'iciclespear', 'rockblast']:
                counter.add('skilllink')

        counter.set('Physical', categories['Physical'])
        counter.set('Special', categories['Special'])
        counter.set('Status', categories['Status'])

        return counter

    # ============================================
    # MOVE POOL CULLING
    # ============================================

    def incompatible_moves(self, moves: Set[str], move_pool: List[str], moves_a: str, moves_b: str):
        """Remove incompatible moves from pool"""
        move_array_a = [moves_a] if isinstance(moves_a, str) else moves_a
        move_array_b = [moves_b] if isinstance(moves_b, str) else moves_b

        if len(moves) + len(move_pool) <= self.max_move_count:
            return

        for moveid1 in moves:
            if moveid1 in move_array_b:
                for moveid2 in move_array_a:
                    if moveid1 != moveid2 and moveid2 in move_pool:
                        self.fast_pop(move_pool, move_pool.index(moveid2))
                        if len(moves) + len(move_pool) <= self.max_move_count:
                            return

            if moveid1 in move_array_a:
                for moveid2 in move_array_b:
                    if moveid1 != moveid2 and moveid2 in move_pool:
                        self.fast_pop(move_pool, move_pool.index(moveid2))
                        if len(moves) + len(move_pool) <= self.max_move_count:
                            return

    def cull_move_pool(self, types: Set[str], moves: Set[str], abilities: List[str],
                       counter: MoveCounter, move_pool: List[str], team_details: Dict,
                       species: Dict, is_lead: bool, tera_type: str, role: str):
        """Remove incompatible moves from pool based on team needs"""

        if len(moves) + len(move_pool) <= self.max_move_count:
            return

        # If we have two unfilled moves and only one unpaired move, cull the unpaired move
        if len(moves) == self.max_move_count - 2:
            unpaired_moves = list(move_pool)
            for pair in MOVE_PAIRS:
                if pair[0] in move_pool and pair[1] in move_pool:
                    if pair[0] in unpaired_moves:
                        unpaired_moves.remove(pair[0])
                    if pair[1] in unpaired_moves:
                        unpaired_moves.remove(pair[1])
            if len(unpaired_moves) == 1:
                self.fast_pop(move_pool, move_pool.index(unpaired_moves[0]))

        # Paired moves
        if len(moves) == self.max_move_count - 1:
            for pair in MOVE_PAIRS:
                if pair[0] in move_pool and pair[1] in move_pool:
                    self.fast_pop(move_pool, move_pool.index(pair[0]))
                    self.fast_pop(move_pool, move_pool.index(pair[1]))

        # Team-based culls
        if team_details.get('screens'):
            if 'auroraveil' in move_pool:
                self.fast_pop(move_pool, move_pool.index('auroraveil'))
            if len(move_pool) >= self.max_move_count + 2:
                if 'reflect' in move_pool:
                    self.fast_pop(move_pool, move_pool.index('reflect'))
                if 'lightscreen' in move_pool:
                    self.fast_pop(move_pool, move_pool.index('lightscreen'))

        if team_details.get('stickyWeb'):
            if 'stickyweb' in move_pool:
                self.fast_pop(move_pool, move_pool.index('stickyweb'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        if team_details.get('stealthRock'):
            if 'stealthrock' in move_pool:
                self.fast_pop(move_pool, move_pool.index('stealthrock'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        if team_details.get('defog') or team_details.get('rapidSpin'):
            if 'defog' in move_pool:
                self.fast_pop(move_pool, move_pool.index('defog'))
            if 'rapidspin' in move_pool:
                self.fast_pop(move_pool, move_pool.index('rapidspin'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        if team_details.get('toxicSpikes'):
            if 'toxicspikes' in move_pool:
                self.fast_pop(move_pool, move_pool.index('toxicspikes'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        if team_details.get('spikes', 0) >= 2:
            if 'spikes' in move_pool:
                self.fast_pop(move_pool, move_pool.index('spikes'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        if team_details.get('statusCure'):
            if 'healbell' in move_pool:
                self.fast_pop(move_pool, move_pool.index('healbell'))
            if len(moves) + len(move_pool) <= self.max_move_count:
                return

        # General incompatibilities
        incompatible_pairs = [
            [SETUP, PIVOT_MOVES],
            [SETUP, HAZARDS],
            [SETUP, ['defog', 'nuzzle', 'toxic', 'yawn', 'haze']],
            [PHYSICAL_SETUP, PHYSICAL_SETUP],
            ['substitute', PIVOT_MOVES],
            ['curse', ['irondefense', 'rapidspin']],
            ['dragondance', 'dracometeor'],
            ['yawn', 'roar'],
            ['trick', 'uturn'],
        ]

        for pair in incompatible_pairs:
            self.incompatible_moves(moves, move_pool, pair[0], pair[1])

        # Type-specific
        if 'Ice' not in types:
            self.incompatible_moves(moves, move_pool, 'icebeam', 'icywind')

        self.incompatible_moves(moves, move_pool, 'taunt', 'encore')

        if 'Dark' not in types and tera_type != 'Dark':
            self.incompatible_moves(moves, move_pool, 'knockoff', 'suckerpunch')

    # ============================================
    # MOVE SELECTION
    # ============================================

    def add_move(self, move: str, moves: Set[str], types: Set[str], abilities: List[str],
                team_details: Dict, species: Dict, is_lead: bool, move_pool: List[str],
                tera_type: str, role: str) -> MoveCounter:
        """Add a move to the moveset"""
        moves.add(move)
        if move in move_pool:
            self.fast_pop(move_pool, move_pool.index(move))

        counter = self.query_moves(moves, list(types), tera_type, abilities)
        self.cull_move_pool(types, moves, abilities, counter, move_pool, team_details,
                           species, is_lead, tera_type, role)
        return counter

    def random_moveset(self, types: Set[str], abilities: List[str], team_details: Dict,
                      species: Dict, is_lead: bool, move_pool: List[str], tera_type: str,
                      role: str) -> List[str]:
        """Generate 4 moves for a Pokemon"""
        moves = set()
        counter = self.query_moves(moves, list(types), tera_type, abilities)
        self.cull_move_pool(types, moves, abilities, counter, move_pool, team_details,
                           species, is_lead, tera_type, role)

        # If pool is small, just take all moves
        if len(move_pool) <= self.max_move_count:
            return move_pool.copy()

        # Run enforcement checker
        def run_enforcement_checker(checker_name: str) -> bool:
            if checker_name not in MOVE_ENFORCEMENT_CHECKERS:
                return False
            return MOVE_ENFORCEMENT_CHECKERS[checker_name](
                move_pool, moves, abilities, types, counter, species
            )

        # Tera Blast for Tera Blast users
        if role == 'Tera Blast user' and 'terablast' in move_pool:
            counter = self.add_move('terablast', moves, types, abilities, team_details, species,
                                    is_lead, move_pool, tera_type, role)

        # Required moves (species-specific) - would need species.requiredMove

        # Facade for Guts
        if 'facade' in move_pool and 'Guts' in abilities:
            counter = self.add_move('facade', moves, types, abilities, team_details, species,
                                    is_lead, move_pool, tera_type, role)

        # Specific moves
        for moveid in ['nightshade', 'revelationdance', 'revivalblessing', 'stickyweb']:
            if moveid in move_pool:
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Hazard removal for Bulky Support
        if role == 'Bulky Support' and not team_details.get('defog') and not team_details.get('rapidSpin'):
            if 'rapidspin' in move_pool:
                counter = self.add_move('rapidspin', moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)
            if 'defog' in move_pool:
                counter = self.add_move('defog', moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Aurora Veil if no screens
        if not team_details.get('screens') and 'auroraveil' in move_pool:
            counter = self.add_move('auroraveil', moves, types, abilities, team_details, species,
                                    is_lead, move_pool, tera_type, role)

        # Knock Off on pure Normal/Fighting
        if len(types) == 1 and ('Normal' in types or 'Fighting' in types):
            if 'knockoff' in move_pool:
                counter = self.add_move('knockoff', moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Spore on Smeargle
        if species.get('id') == 'smeargle' and 'spore' in move_pool:
            counter = self.add_move('spore', moves, types, abilities, team_details, species,
                                    is_lead, move_pool, tera_type, role)

        # STAB priority for certain roles
        if role in ['Bulky Attacker', 'Bulky Setup', 'Wallbreaker'] or species.get('id') in PRIORITY_POKEMON:
            priority_moves = []
            for moveid in move_pool:
                # Simplified - would need to check move priority and basePower
                if moveid in ['quickattack', 'suckerpunch', 'aquajet', 'machpunch', 'electroweb']:
                    priority_moves.append(moveid)
            if priority_moves:
                moveid = self.sample(priority_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Enforce STAB for each type
        for type_name in types:
            stab_moves = []
            for moveid in move_pool:
                move_type = self.get_move_type(moveid, list(types), abilities, tera_type)
                if moveid not in NO_STAB and type_name == move_type:
                    stab_moves.append(moveid)

            while run_enforcement_checker(type_name):
                if not stab_moves:
                    break
                moveid = self.sample_no_replace(stab_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Tera STAB
        if not counter.get('stabtera') and role not in ['Bulky Support']:
            tera_stab_moves = []
            for moveid in move_pool:
                move_type = self.get_move_type(moveid, list(types), abilities, tera_type)
                if moveid not in NO_STAB and tera_type == move_type:
                    tera_stab_moves.append(moveid)
            if tera_stab_moves:
                moveid = self.sample(tera_stab_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # If no STAB, add one
        if not counter.get('stab'):
            stab_moves = []
            for moveid in move_pool:
                move_type = self.get_move_type(moveid, list(types), abilities, tera_type)
                if moveid not in NO_STAB and move_type in types:
                    stab_moves.append(moveid)
            if stab_moves:
                moveid = self.sample(stab_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Recovery for bulky roles
        if role in ['Bulky Support', 'Bulky Attacker', 'Bulky Setup']:
            recovery_moves = [m for m in move_pool if m in RECOVERY_MOVES]
            if recovery_moves:
                moveid = self.sample(recovery_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Pivot moves for AV Pivot
        if role == 'AV Pivot':
            pivot_moves = [m for m in move_pool if m in PIVOT_MOVES]
            if pivot_moves:
                moveid = self.sample(pivot_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Setup for setup roles
        if 'Setup' in role or role == 'Tera Blast user':
            non_speed_setup = [m for m in move_pool if m in SETUP and m not in SPEED_SETUP]
            if non_speed_setup:
                moveid = self.sample(non_speed_setup)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)
            else:
                setup_moves = [m for m in move_pool if m in SETUP]
                if setup_moves:
                    moveid = self.sample(setup_moves)
                    counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                            is_lead, move_pool, tera_type, role)

        # Protect for Protect roles
        if 'Protect' in role:
            protect_moves = [m for m in move_pool if m in PROTECT_MOVES]
            if protect_moves:
                moveid = self.sample(protect_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # If no damaging moves, add one
        if not counter.damaging_moves:
            attacking_moves = [m for m in move_pool if m not in NO_STAB]
            if attacking_moves:
                moveid = self.sample(attacking_moves)
                counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                        is_lead, move_pool, tera_type, role)

        # Coverage if only one attack (simplified - could add more logic)

        # Fill remaining slots randomly
        while len(moves) < self.max_move_count and move_pool:
            if len(moves) + len(move_pool) <= self.max_move_count:
                for m in move_pool:
                    moves.add(m)
                break
            moveid = self.sample(move_pool)
            counter = self.add_move(moveid, moves, types, abilities, team_details, species,
                                    is_lead, move_pool, tera_type, role)

            # Check move pairs
            for pair in MOVE_PAIRS:
                if moveid == pair[0] and pair[1] in move_pool:
                    counter = self.add_move(pair[1], moves, types, abilities, team_details, species,
                                            is_lead, move_pool, tera_type, role)
                if moveid == pair[1] and pair[0] in move_pool:
                    counter = self.add_move(pair[0], moves, types, abilities, team_details, species,
                                            is_lead, move_pool, tera_type, role)

        return list(moves)

    # ============================================
    # ABILITY SELECTION
    # ============================================

    def should_cull_ability(self, ability: str, types: Set[str], moves: Set[str],
                           abilities: List[str], counter: MoveCounter, team_details: Dict,
                           species: Dict, role: str, is_lead: bool) -> bool:
        """Check if ability should be culled"""

        if ability in ['Chlorophyll', 'Solar Power']:
            return not team_details.get('sun')
        if ability == 'Defiant':
            return species.get('id') == 'thundurus' and counter.get('Status', 0) > 0
        if ability in ['Hydration', 'Swift Swim']:
            return not team_details.get('rain')
        if ability in ['Iron Fist', 'Skill Link']:
            return counter.get(ability, 0) == 0
        if ability == 'Overgrow':
            return counter.get('Grass', 0) == 0
        if ability == 'Prankster':
            return counter.get('Status', 0) == 0
        if ability in ['Sand Force', 'Sand Rush']:
            return not team_details.get('sand')
        if ability == 'Slush Rush':
            return not team_details.get('snow')
        if ability == 'Swarm':
            return counter.get('Bug', 0) == 0
        if ability == 'Torrent':
            return counter.get('Water', 0) == 0 and 'flipturn' not in moves

        return False

    def get_ability(self, types: Set[str], moves: Set[str], abilities: List[str],
                   counter: MoveCounter, team_details: Dict, species: Dict,
                   is_lead: bool, tera_type: str, role: str) -> str:
        """Select ability"""

        if len(abilities) <= 1:
            return abilities[0]

        # Hard-coded species checks
        species_id = species.get('id', '')

        if species_id == 'drifblim':
            return 'Aftermath' if 'defog' in moves else 'Unburden'
        if 'Flash Fire' in abilities:
            # Would need effectiveness check - assume not
            pass
        if species_id in ['thundurus', 'tornadus'] and counter.get('Physical', 0) == 0:
            return 'Prankster'
        if species_id == 'swampert' and (counter.get('Water', 0) > 0 or 'flipturn' in moves):
            return 'Torrent'
        if species_id == 'toucannon' and counter.get('skilllink', 0) > 0:
            return 'Skill Link'
        if 'Slush Rush' in abilities and 'snowscape' in moves:
            return 'Slush Rush'
        if species_id == 'golduck' and team_details.get('rain'):
            return 'Swift Swim'

        # Cull abilities
        ability_allowed = []
        for ability in abilities:
            if not self.should_cull_ability(ability, types, moves, abilities, counter,
                                          team_details, species, role, is_lead):
                ability_allowed.append(ability)

        if ability_allowed:
            return self.sample(ability_allowed)

        # Weather abilities if all culled
        weather_abilities = [a for a in abilities if a in ['Chlorophyll', 'Hydration', 'Sand Force',
                                                              'Sand Rush', 'Slush Rush', 'Solar Power', 'Swift Swim']]
        if weather_abilities:
            return self.sample(weather_abilities)

        # Fallback
        return self.sample(abilities)

    # ============================================
    # ITEM SELECTION
    # ============================================

    def get_priority_item(self, ability: str, types: Set[str], moves: Set[str],
                         counter: MoveCounter, team_details: Dict, species: Dict,
                         is_lead: bool, tera_type: str, role: str) -> str:
        """Priority item selection (singles)"""

        if role == 'Fast Bulky Setup' and ability in ['Quark Drive', 'Protosynthesis']:
            return 'Booster Energy'
        if species.get('id') == 'lokix':
            return 'Silver Powder' if role == 'Fast Attacker' else 'Life Orb'

        # Species-specific
        if species.get('id') == 'pikachu':
            return 'Light Ball'
        if role == 'AV Pivot':
            return 'Assault Vest'
        if species.get('id') == 'regieleki':
            return 'Magnet'
        if types.intersection({'Normal'}) and 'doubleedge' in moves and 'fakeout' in moves:
            return 'Silk Scarf'
        if species.get('id') == 'froslass' or 'populationbomb' in moves:
            return 'Wide Lens'
        if species.get('id') == 'smeargle':
            return 'Focus Sash'
        if 'clangoroussoul' in moves or (species.get('id') == 'toxtricity' and 'shiftgear' in moves):
            return 'Throat Spray'
        if species.get('baseSpecies') == 'Magearna' and role == 'Tera Blast user':
            return 'Weakness Policy'
        if any(m in moves for m in ['dragonenergy', 'lastrespects', 'waterspout']):
            return 'Choice Scarf'
        if ability == 'Imposter' or (species.get('id') == 'magnezone' and role == 'Fast Attacker'):
            return 'Choice Scarf'
        if species.get('id') == 'rampardos' and role == 'Fast Attacker':
            return 'Choice Scarf'
        if species.get('id') == 'palkia' and counter.get('Status', 0) > 0:
            return 'Lustrous Orb'
        if 'courtchange' in moves or (species.get('id') == 'luvdisc' or (species.get('id') == 'terapagos' and 'rest' not in moves)):
            return 'Heavy-Duty Boots'
        if ability in ['Cheek Pouch', 'Cud Chew', 'Harvest', 'Ripen'] or 'bellydrum' in moves or 'filletaway' in moves:
            return 'Sitrus Berry'
        if any(m in moves for m in ['healingwish', 'switcheroo', 'trick']):
            base_spe = species.get('base_stats', {}).get('spe', 100)
            if 60 <= base_spe <= 108 and role != 'Wallbreaker' and counter.get('priority', 0) == 0:
                return 'Choice Scarf'
            return 'Choice Band' if counter.get('Physical', 0) > counter.get('Special', 0) else 'Choice Specs'
        if counter.get('Status', 0) > 0 and species.get('name') in ['Latias', 'Latios']:
            return 'Soul Dew'
        if species.get('id') == 'scyther':
            return 'Eviolite' if (is_lead and 'uturn' not in moves) else 'Heavy-Duty Boots'
        if ability in ['Poison Heal', 'Quick Feet']:
            return 'Toxic Orb'
        if species.get('nfe'):  # Not fully evolved
            return 'Eviolite'
        if ability == 'Guts' or 'facade' in moves:
            if 'Fire' in types or ability == 'Toxic Boost':
                return 'Toxic Orb'
            return 'Flame Orb'
        if ability == 'Magic Guard' or (ability == 'Sheer Force' and counter.get('sheerforce', 0) > 0):
            return 'Life Orb'
        if ability == 'Anger Shell':
            return self.sample(['Expert Belt', 'Lum Berry', 'Scope Lens', 'Sitrus Berry'])
        # Note: Clear Amulet is for doubles, skipping for singles
        if counter.get('skilllink', 0) > 0 and ability != 'Skill Link' and species.get('id') != 'breloom':
            return 'Loaded Dice'
        if ability == 'Unburden':
            return 'White Herb' if ('closecombat' in moves or 'leafstorm' in moves) else 'Sitrus Berry'
        if 'shellsmash' in moves and ability != 'Weak Armor':
            return 'White Herb'
        if 'meteorbeam' in moves or ('electroshot' in moves and not team_details.get('rain')):
            return 'Power Herb'
        if 'acrobatics' in moves and ability != 'Protosynthesis':
            return ''
        if 'auroraveil' in moves or ('lightscreen' in moves and 'reflect' in moves):
            return 'Light Clay'
        if ability == 'Gluttony':
            return self.sample(['aguavberry', 'figyberry', 'iapapaberry', 'magoberry', 'wikiberry'])
        if species.get('id') == 'giratina' and 'rest' in moves and 'sleeptalk' not in moves:
            return 'Leftovers'
        if 'rest' in moves and 'sleeptalk' not in moves and ability not in ['Natural Cure', 'Shed Skin']:
            return 'Chesto Berry'

        return None  # No priority item

    def get_item(self, ability: str, types: Set[str], moves: Set[str],
                counter: MoveCounter, team_details: Dict, species: Dict,
                is_lead: bool, tera_type: str, role: str) -> str:
        """Get item for singles"""

        life_orb_reqs = all(m not in moves for m in ['flamecharge', 'nuzzle', 'rapidspot'])

        # Choice items - only if mostly attacking moves
        if counter.get('Physical', 0) >= len(moves) and all(m not in moves for m in ['dragontail', 'fakeout', 'firstimpression', 'flamecharge', 'rapidspin', 'trailblaze']):
            base_atk = species.get('base_stats', {}).get('atk', 100)
            base_spe = species.get('base_stats', {}).get('spe', 100)
            scarf_req = role != 'Wallbreaker' and (base_atk >= 100 or ability in ['Huge Power', 'Pure Power']) and 60 <= base_spe <= 108 and ability != 'Speed Boost' and counter.get('priority', 0) == 0
            return 'Choice Scarf' if (scarf_req and self.randomChance(1, 2)) else 'Choice Band'

        if counter.get('Special', 0) >= len(moves) or (counter.get('Special', 0) >= len(moves) - 1 and any(m in moves for m in ['flipturn', 'uturn'])):
            base_spa = species.get('base_stats', {}).get('spa', 100)
            base_spe = species.get('base_stats', {}).get('spe', 100)
            scarf_req = role != 'Wallbreaker' and base_spa >= 100 and 60 <= base_spe <= 108 and ability != 'Speed Boost' and ability != 'Tinted Lens' and 'uturn' not in moves and counter.get('priority', 0) == 0
            return 'Choice Scarf' if (scarf_req and self.randomChance(1, 2)) else 'Choice Specs'

        if counter.get('speedsetup', 0) > 0 and counter.get('physicalsetup', 0) == 0 and role == 'Bulky Setup':
            return 'Weakness Policy'

        if counter.get('Status', 0) == 0 and role not in ['Fast Attacker', 'Wallbreaker', 'Tera Blast user']:
            return 'Assault Vest'

        if species.get('id') == 'golem':
            return 'Weakness Policy' if counter.get('speedsetup', 0) > 0 else 'Custap Berry'

        if 'substitute' in moves:
            return 'Leftovers'

        if is_lead and 'stickyweb' in moves:
            total_stats = sum(species.get('base_stats', {}).values())
            if total_stats <= 235:
                return 'Focus Sash'

        # Recovery moves prefer Leftovers
        if counter.get('recovery', 0) > 0:
            return 'Leftovers'

        # Bulky support gets Leftovers
        if role == 'Bulky Support':
            return 'Leftovers'

        # Bulky attackers get variety
        if 'Bulky' in role:
            if counter.get('Status', 0) > 0:
                return self.sample(['Leftovers', 'Heavy-Duty Boots', 'Lum Berry'])

        # Setup sweepers with setup moves
        if counter.get('setup', 0) > 0 and counter.get('recovery', 0) == 0:
            if counter.get('speedsetup', 0) > 0:
                return 'Life Orb'
            elif counter.get('physicalsetup', 0) > 0:
                return 'Life Orb'

        # Wallbreakers with strong attacks
        if role == 'Wallbreaker':
            if counter.get('Physical', 0) > counter.get('Special', 0):
                return self.sample(['Life Orb', 'Choice Band', 'Choice Scarf'])
            else:
                return self.sample(['Life Orb', 'Choice Specs', 'Choice Scarf'])

        # Fast attackers - more variety
        if 'Fast' in role:
            # Life Orb users
            if counter.get('stab', 0) >= 2 and counter.get('priority', 0) == 0:
                return self.sample(['Life Orb', 'Choice Scarf', 'Choice Band', 'Heavy-Duty Boots'])
            elif counter.get('priority', 0) > 0:
                return self.sample(['Life Orb', 'Focus Sash', 'Heavy-Duty Boots'])

        # Defensive Pokemon
        if role not in ['Wallbreaker', 'Fast Attacker'] and counter.get('Physical', 0) + counter.get('Special', 0) <= 2:
            return 'Leftovers'

        # Weather setters
        if 'sunnyday' in moves or 'raindance' in moves or 'sandstorm' in moves or 'hail' in moves:
            return 'Heavy-Duty Boots'

        # Hazard users
        if counter.get('hazards', 0) > 0 and not team_details.get('defog'):
            return self.sample(['Heavy-Duty Boots', 'Leftovers', 'Lum Berry'])

        # Default variety - reduce Heavy-Duty Boots frequency
        return self.sample([
            'Leftovers',
            'Heavy-Duty Boots',
            'Life Orb',
            'Lum Berry',
            'Focus Sash',
            'Sitrus Berry',
            'Leftovers',
            'Heavy-Duty Boots',
        ])

    # ============================================
    # SET GENERATION
    # ============================================

    def random_set(self, pokemon_name: str, team_details: Dict = None, is_lead: bool = False) -> Dict:
        """Generate a random set for a Pokemon"""

        if team_details is None:
            team_details = {}

        if pokemon_name not in self.sets_data:
            return None

        species_data = self.sets_data[pokemon_name]
        sets = species_data.get('sets', [])

        if not sets:
            return None

        # Filter sets
        possible_sets = []
        for s in sets:
            if team_details.get('tera_blast') and s.get('role') == 'Tera Blast user':
                continue
            possible_sets.append(s)

        if not possible_sets:
            possible_sets = sets

        chosen_set = self.sample(possible_sets)
        role = chosen_set.get('role', 'Bulky Attacker')

        # Get movepool - convert to IDs (lowercase with hyphens)
        movepool_raw = chosen_set.get('movepool', [])
        # Keep as-is since sets.json uses proper move names
        movepool = [m.lower().replace(' ', '-') for m in movepool_raw]

        # Get types from forms.json and ptypes.json
        pokemon_id, type_ids = get_pokemon_id_and_types(pokemon_name)
        type_names = [TYPE_ID_TO_NAME.get(tid, 'normal') for tid in type_ids]
        types = set(type_names)

        # Get abilities
        abilities = chosen_set.get('abilities', ['Overgrow'])

        # Build species dict with base stats
        base_stats = get_pokemon_base_stats(pokemon_name)
        species_dict = {'id': pokemon_name, 'name': pokemon_name, 'base_stats': base_stats}

        # Get moves
        moves = self.random_moveset(types, abilities, team_details,
                                   species_dict,
                                   is_lead, movepool.copy(),
                                   chosen_set.get('teraTypes', ['Grass'])[0], role)

        # Get ability
        counter = self.query_moves(set(moves), list(types), chosen_set.get('teraTypes', ['Grass'])[0], abilities)
        ability = self.get_ability(types, set(moves), abilities, counter, team_details,
                                   species_dict, is_lead,
                                   chosen_set.get('teraTypes', ['Grass'])[0], role)

        # Get item
        tera_type = self.sample(chosen_set.get('teraTypes', ['Grass']))
        priority_item = self.get_priority_item(ability, types, set(moves), counter, team_details,
                                              species_dict, is_lead,
                                              tera_type, role)

        if priority_item:
            item = priority_item
        else:
            item = self.get_item(ability, types, set(moves), counter, team_details,
                                species_dict, is_lead,
                                tera_type, role)

        # Get level
        level = species_data.get('level', 50)

        # Get gender
        gender = 'M' if pokemon_name == 'Greninja' else self.sample(['M', 'F'])

        # Shiny
        shiny = self.randomChance(1, 1024)

        # EVs - proper EV optimization based on role
        evs = self.get_evs(role, base_stats, counter, types, ability, item, moves)

        # Nature selection
        nature = get_nature_for_role(role, counter, base_stats, types)
        nature_id = get_nature_id(nature)

        # IVs
        ivs = {'hp': 31, 'atk': 31, 'def': 31, 'spa': 31, 'spd': 31, 'spe': 31}

        # Get ability ID
        ability_id = get_ability_id(ability)

        # Tera type ID
        tera_type_id = TYPE_NAME_TO_ID.get(tera_type.lower(), 1)

        return {
            'pokemon_name': pokemon_name,
            'pokemon_id': pokemon_id,
            'type_ids': type_ids,
            'tera_type_id': tera_type_id,
            'role': role,
            'moves': moves,
            'ability': ability,
            'ability_id': ability_id,
            'nature': nature,
            'nature_id': nature_id,
            'tera_type': tera_type,
            'item': item if item else 'Leftovers',
            'level': level,
            'gender': gender,
            'evs': evs,
            'ivs': ivs,
            'shiny': shiny,
            'base_stats': base_stats,
        }

    def get_evs(self, role: str, base_stats: Dict, counter: MoveCounter,
                types: Set[str], ability: str, item: str, moves: List[str]) -> Dict:
        """Generate appropriate EVs based on role and stats"""
        hp = 0
        atk = 0
        def_stat = 0
        spa = 0
        spd = 0
        spe = 0

        base_atk = base_stats.get('atk', 100)
        base_spa = base_stats.get('spa', 100)
        base_spe = base_stats.get('spe', 100)
        base_def = base_stats.get('def', 100)
        base_spd = base_stats.get('spd', 100)

        # Wallbreaker - max attack
        if role == 'Wallbreaker':
            if counter.get('Physical', 0) > counter.get('Special', 0):
                atk = 252
                spe = 252
            else:
                spa = 252
                spe = 252

        # Fast Attacker - speed + offense
        elif 'Fast' in role:
            if counter.get('Physical', 0) >= counter.get('Special', 0):
                atk = 252
            else:
                spa = 252
            spe = 252

        # Bulky Setup - bulk + speed
        elif role == 'Bulky Setup':
            if counter.get('Physical', 0) > counter.get('Special', 0):
                atk = 252
            else:
                spa = 252
            spe = 252

        # Tera Blast user
        elif role == 'Tera Blast user':
            if counter.get('Physical', 0) > counter.get('Special', 0):
                atk = 252
            else:
                spa = 252
            spe = 252

        # AV Pivot - special bulk
        elif role == 'AV Pivot':
            atk = 252
            spd = 252

        # Bulky Attacker
        elif 'Bulky' in role:
            # Balance bulk based on types
            if 'Fire' in types or 'Ice' in types or 'Dragon' in types:
                def_stat = 252
                spd = 252
            elif 'Steel' in types or 'Rock' in types:
                def_stat = 252
                spd = 252
            else:
                def_stat = 252
                spd = 252

        # Bulky Support - max HP and bulk
        elif role == 'Bulky Support':
            hp = 252
            def_stat = 252
            spd = 252

        # Default - offensive spread
        else:
            if counter.get('Physical', 0) > counter.get('Special', 0):
                atk = 252
            elif counter.get('Special', 0) > counter.get('Physical', 0):
                spa = 252
            else:
                # Mixed - put in better stat
                if base_atk >= base_spa:
                    atk = 252
                else:
                    spa = 252
            spe = 252

        # Special cases
        if 'trickroom' in moves:
            # TR spreads - min speed
            if spe > 4:
                spe = 4
                hp = 252
                def_stat = 252

        if item in ['Choice Scarf', 'Choice Band', 'Choice Specs']:
            if counter.get('Physical', 0) >= counter.get('Special', 0):
                atk = 252
            else:
                spa = 252
            spe = 252

        if ability in ['Guts', 'Toxic Boost']:
            atk = 252
            spe = 252

        if ability in ['Huge Power', 'Pure Power']:
            atk = 252
            spe = 252

        if 'dragondance' in moves or 'swordsdance' in moves or 'nastyplot' in moves:
            if counter.get('Physical', 0) > counter.get('Special', 0):
                atk = 252
            else:
                spa = 252
            spe = 252

        return {
            'hp': hp, 'atk': atk, 'def': def_stat,
            'spa': spa, 'spd': spd, 'spe': spe
        }

    # ============================================
    # TEAM GENERATION
    # ============================================

    def get_pokemon_pool(self, team: List[Dict] = None, force_type: str = None) -> Tuple[Dict, List]:
        """Get available Pokemon pool"""

        if team is None:
            team = []

        exclude = [p['pokemon_name'].lower().replace('-', '').replace(' ', '') for p in team]

        pokemon_pool = {}
        base_species_pool = []

        for pokemon_name in self.sets_data.keys():
            species_id = pokemon_name.lower().replace(' ', '').replace('-', '')

            if species_id in exclude:
                continue

            pokemon_pool[pokemon_name] = [pokemon_name]
            base_species_pool.append(pokemon_name)

        return pokemon_pool, base_species_pool

    def generate_team(self, team_size: int = 6) -> List[Dict]:
        """Generate a random team"""

        team = []
        team_details = {
            'tera_blast': False, 'screens': False, 'defog': False,
            'rapidSpin': False, 'stealthRock': False, 'stickyWeb': False,
            'toxicSpikes': False, 'spikes': 0, 'statusCure': False,
            # Type tracking
            'types': {},  # {type_name: count}
            'weaknesses': set(),  # Types that are super effective against team
            'resistances': set(),  # Types that are not very effective against team
        }

        pokemon_pool, base_species_pool = self.get_pokemon_pool(team)

        leads_remaining = 1

        attempts = 0
        while len(team) < self.max_team_size and base_species_pool and attempts < 100:
            attempts += 1

            # Sample Pokemon
            if not base_species_pool:
                break

            pokemon_name = self.sample_no_replace(base_species_pool)

            # Generate set
            pokemon_set = self.random_set(pokemon_name, team_details, is_lead=(leads_remaining > 0 and len(team) < 2))

            if pokemon_set is None:
                continue

            # Track team details
            if pokemon_set['role'] == 'Tera Blast user':
                team_details['tera_blast'] = True

            if pokemon_set['ability'] in ['Drizzle'] or 'raindance' in pokemon_set['moves']:
                team_details['rain'] = True
            if pokemon_set['ability'] in ['Drought', 'Orichalcum Pulse'] or 'sunnyday' in pokemon_set['moves']:
                team_details['sun'] = True
            if pokemon_set['ability'] == 'Sand Stream':
                team_details['sand'] = True
            if pokemon_set['ability'] in ['Snow Warning'] or 'snowscape' in pokemon_set['moves']:
                team_details['snow'] = True
            if 'healbell' in pokemon_set['moves']:
                team_details['statusCure'] = True
            if 'spikes' in pokemon_set['moves']:
                team_details['spikes'] = team_details.get('spikes', 0) + 1
            if 'toxicspikes' in pokemon_set['moves'] or pokemon_set['ability'] == 'Toxic Debris':
                team_details['toxicSpikes'] = True
            if 'stealthrock' in pokemon_set['moves']:
                team_details['stealthRock'] = True
            if 'stickyweb' in pokemon_set['moves']:
                team_details['stickyWeb'] = True
            if 'defog' in pokemon_set['moves']:
                team_details['defog'] = True
            if 'rapidspin' in pokemon_set['moves']:
                team_details['rapidSpin'] = True

            # Track type counts
            for type_name in [TYPE_ID_TO_NAME.get(tid, 'normal') for tid in pokemon_set.get('type_ids', [])]:
                team_details['types'][type_name] = team_details['types'].get(type_name, 0) + 1

            # Calculate team weaknesses and resistances PER POKEMON (not merged)
            # Track which types are weak/resist/immune per team member
            team_details['type_chart'] = {}  # {type_name: {'weak': count, 'resist': count, 'immune': count}}

            for attack_type_id in range(1, 19):
                type_name = TYPE_ID_TO_NAME.get(attack_type_id, 'normal')
                weak_count = 0
                resist_count = 0
                immune_count = 0

                for p in team + [pokemon_set]:
                    p_types = p.get('type_ids', [])
                    eff = get_type_effectiveness(attack_type_id, p_types)
                    if eff == 0:
                        immune_count += 1
                    elif eff >= 2.0:
                        weak_count += 1
                    elif eff <= 0.5:
                        resist_count += 1

                team_details['type_chart'][type_name] = {
                    'weak': weak_count,
                    'resist': resist_count,
                    'immune': immune_count
                }

            team.append(pokemon_set)

            if leads_remaining > 0 and len(team) <= 2:
                leads_remaining -= 1

        return team


def generate_random_team(team_size: int = 6, seed: int = None) -> List[Dict]:
    """Generate a random Pokemon team"""
    generator = RandomTeamGenerator(seed=seed)
    return generator.generate_team(team_size)


def generate_two_teams(seed: int = None) -> Tuple[List[Dict], List[Dict]]:
    """Generate two random teams for battle"""
    generator = RandomTeamGenerator(seed=seed)
    team1 = generator.generate_team(6)
    team2 = generator.generate_team(6)
    return team1, team2


def convert_team_to_raw_data(team: List[Dict], team_name: str = "Random Team") -> List[Dict]:
    """
    Convert generated team to raw_data format compatible with pokemon.create().
    This produces the dict format expected by the async create() function.
    """
    # Build lookup from form ID to identifier, preferring entries that have valid ptypes
    forms_data = _load_forms_data()
    ptypes_data = _load_ptypes_data()
    valid_ptype_ids = {pt.get('id') for pt in ptypes_data}

    # Build two maps: id -> identifier, preferring ones with valid ptypes
    id_to_identifier = {}
    for entry in forms_data:
        form_id = entry.get('id')
        pokemon_id = entry.get('pokemon_id', form_id)
        identifier = entry.get('identifier', '')

        # Only consider entries with valid ptypes
        if pokemon_id in valid_ptype_ids or form_id in valid_ptype_ids:
            # Only store if not already stored (first match is fine)
            if form_id not in id_to_identifier:
                id_to_identifier[form_id] = identifier

    raw_party = []
    for i, pokemon in enumerate(team):
        # Map gender
        gender_str = "-m" if pokemon.get('gender') == 'M' else "-f"

        # Convert moves - keep as lowercase identifiers (matching moves.json)
        moves = [m.lower().replace(' ', '-') for m in pokemon.get('moves', [])]

        # Get item name - convert to proper format
        item = pokemon.get('item', 'Leftovers')
        item = item.replace(' ', '-').replace("'", "").lower()

        # Get the proper pokemon name from forms.json using pokemon_id
        # But if the ID is 1 (default fallback), use the sets.json name directly
        # because ID 1 maps to Bulbasaur in forms.json regardless of actual Pokemon
        pokemon_id = pokemon.get('pokemon_id', 1)
        if pokemon_id == 1:
            # ID 1 is the fallback - use the original sets.json name
            proper_name = pokemon['pokemon_name']
            base_pokemon_id = 1
        else:
            proper_name = id_to_identifier.get(pokemon_id, pokemon['pokemon_name'])
            base_pokemon_id = pokemon_id

        # Find ability index by matching ability name to poke_abilities
        selected_ability = pokemon.get('ability', '')
        ability_index = 0

        # Get all abilities for this pokemon from poke_abilities
        poke_abilities_data = _load_poke_abilities_data()
        pokemon_abilities = [pa for pa in poke_abilities_data if pa.get('pokemon_id') == base_pokemon_id]
        # Sort by slot to get correct order
        pokemon_abilities = sorted(pokemon_abilities, key=lambda x: x.get('slot', 0))

        # Build ability name lookup (normalize for comparison)
        abilities_data = _load_ability_data()
        ability_id_to_name = {ab.get('id'): ab.get('identifier', '').lower().replace('-', '').replace(' ', '')
                            for ab in abilities_data}

        # Find index of selected ability
        normalized_selected = selected_ability.lower().replace('-', '').replace(' ', '')
        for i, pa in enumerate(pokemon_abilities):
            ability_name = ability_id_to_name.get(pa.get('ability_id'), '')
            if ability_name == normalized_selected:
                ability_index = i
                break

        # Build raw_data dict
        raw_data = {
            "pokname": proper_name,
            "poknick": "None",
            "hpiv": pokemon['ivs'].get('hp', 31),
            "atkiv": pokemon['ivs'].get('atk', 31),
            "defiv": pokemon['ivs'].get('def', 31),
            "spatkiv": pokemon['ivs'].get('spa', 31),
            "spdefiv": pokemon['ivs'].get('spd', 31),
            "speediv": pokemon['ivs'].get('spe', 31),
            "hpev": pokemon['evs'].get('hp', 0),
            "atkev": pokemon['evs'].get('atk', 0),
            "defev": pokemon['evs'].get('def', 0),
            "spatkev": pokemon['evs'].get('spa', 0),
            "spdefev": pokemon['evs'].get('spd', 0),
            "speedev": pokemon['evs'].get('spe', 0),
            "pokelevel": pokemon.get('level', 50),
            "shiny": pokemon.get('shiny', False),
            "radiant": False,
            "skin": False,
            "id": i,  # Slot ID
            "hitem": item,
            "happiness": 255,
            "moves": moves,
            "ability_index": ability_index,
            "nature": pokemon.get('nature', 'Hardy'),
            "gender": gender_str,
        }
        raw_party.append(raw_data)

    return raw_party


# For testing
if __name__ == '__main__':
    team1, team2 = generate_two_teams()
    print(f"Team 1 ({len(team1)} Pokemon):")
    for p in team1:
        print(f"  {p['pokemon_name']} Lv{p['level']} - {p['moves'][:2]}...")
    print(f"\nTeam 2 ({len(team2)} Pokemon):")
    for p in team2:
        print(f"  {p['pokemon_name']} Lv{p['level']} - {p['moves'][:2]}...")