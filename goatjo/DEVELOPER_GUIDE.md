# Pokemon Duel - Developer Guide

This guide explains how to extend the Pokemon Duel bot with new content. The bot uses JSON data files for content and Python code for game logic.

---

## Table of Contents

1. [Data Files Overview](#1-data-files-overview)
2. [Adding New Pokemon](#2-adding-new-pokemon)
3. [Adding New Moves](#3-adding-new-moves)
4. [Adding New Abilities](#4-adding-new-abilities)
5. [Adding New Items](#5-adding-new-items)
6. [Adding Images](#6-adding-images)
7. [Forms and Variants](#7-forms-and-variants)
8. [Code Architecture](#8-code-architecture)

---

## 1. Data Files Overview

All game data is stored in `/home/gojo/projects/dueler/goatjo/pokemonduel/data/`. Here's what each file contains:

| File | Purpose |
|------|---------|
| `forms.json` | Pokemon names, IDs, weights, and form relationships |
| `pokemon_stats.json` | Base stats (HP, Atk, Def, SpA, SpD, Spe) for each Pokemon |
| `ptypes.json` | Type assignments for each Pokemon form |
| `poke_abilities.json` | Which abilities each Pokemon can have |
| `moves.json` | Move data (power, accuracy, type, effects, etc.) |
| `abilities.json` | Ability names and descriptions |
| `items.json` | Item names and descriptions |
| `type_effectiveness.json` | Type matchups (super effective, not very effective, etc.) |
| `natures.json` | Nature stat modifiers |
| `pfile.json` | Evolution data (which Pokemon evolve from which) |

---

## 2. Adding New Pokemon

### Step 1: Add to forms.json

```json
{
  "identifier": "gholdengo",
  "base_id": 1000,
  "pokemon_id": 1000,
  "height": 30,
  "weight": 43,
  "base_experience": 265,
  "order": 1000
}
```

### Step 2: Add to pokemon_stats.json

```json
{
  "pokemon_id": 1000,
  "stats": [60, 55, 65, 125, 65, 85]
}
```

The stats array order is: `[HP, Attack, Defense, Sp. Attack, Sp. Defense, Speed]`

Example for Gholdengo (Ghost/Steel type):
- HP: 60, Attack: 55, Defense: 65, SpA: 125, SpD: 65, Spe: 85

### Step 3: Add to ptypes.json

```json
{
  "id": 1000,
  "types": [9, 8]
}
```

Type IDs: 1=Normal, 2=Fighting, 3=Flying, 4=Poison, 5=Ground, 6=Rock, 7=Bug, 8=Ghost, 9=Steel, 10=Fire, 11=Water, 12=Grass, 13=Electric, 14=Ice, 15=Psychic, 16=Dragon, 17=Dark, 18=Fairy

### Step 4: Add to poke_abilities.json

```json
{
  "pokemon_id": 1000,
  "ability_id": 271,
  "is_hidden": false
},
{
  "pokemon_id": 1000,
  "ability_id": 33,
  "is_hidden": true
}
```

- `ability_id` must match an ID from `abilities.json`
- `is_hidden: true` means it's a hidden ability

### Step 5: Add to pfile.json (if it evolves)

```json
{
  "id": 1000,
  "identifier": "gholdengo",
  "evolution_chain_id": 500,
  "evolves_from_species_id": 999,
  "is_default": true
}
```

If the Pokemon doesn't evolve, either omit from pfile.json or set `evolves_from_species_id` to null.

---

## 3. Adding New Moves

### Step 1: Add to moves.json

```json
{
  "id": 1000,
  "identifier": "make-it-rain",
  "power": 120,
  "pp": 20,
  "accuracy": 80,
  "priority": 0,
  "type_id": 11,
  "damage_class_id": 2,
  "effect_id": 450,
  "effect_chance": 100,
  "target_id": 9,
  "crit_rate": 0,
  "min_hits": 1,
  "max_hits": 1
}
```

**Field Explanations:**

| Field | Description | Values |
|-------|-------------|--------|
| `id` | Unique move ID | Any unused integer |
| `identifier` | Move name (lowercase, hyphens) | e.g., "make-it-rain" |
| `power` | Base power (0 for status moves) | 0-250 |
| `pp` | Power Points | 1-64 |
| `accuracy` | Accuracy percentage | 0-100 |
| `priority` | Move priority | -7 to 5 |
| `type_id` | Element type (see types above) | 1-18 |
| `damage_class_id` | 1=Physical, 2=Special, 3=Status | 1, 2, or 3 |
| `effect_id` | Unique effect identifier | See effect codes below |
| `effect_chance` | Chance for secondary effect | 0-100 or null |
| `target_id` | Who the move targets | See target IDs below |
| `crit_rate` | Critical hit rate | 0-4 (0=never, 4=always) |
| `min_hits`/`max_hits` | Number of hits for multi-hit moves | Usually 1-1 |

**Common Target IDs:**
- `9` = Opponent (single target)
- `8` = User
- `10` = Both opponents
- `11` = All Pokemon
- `7` = User's field

**Common Effect IDs (pick one that matches the move's behavior):**
- `0` = No special effect
- `100` = Chance to poison (33%)
- `106` = Chance to flinch (33%)
- `107` = Chance to freeze (20%)
- `108` = Chance to paralyze (25%)
- `109` = Chance to burn (20%)
- `187` = Self-destruct
- `210` = Recoil (Jump 2 turns)
- `241` = Sleep powder/sing (accuracy-based sleep)
- `252` = Thunder/Blizzard accuracy boost in rain/sun
- `266` = Charge (electric moves)
- `302` = Razer Leaf/Solar Beam (solar power)
- `331` = Fly/Dig (semi-invulnerable)
- `334` = Explosion/Final Gambit (faints user)
- `364` = Wish (heal next turn)
- `380` = Protect/Detect
- `401` = Stealth Rock
- `437` = Grassy Glide (priority in terrain)

For complex moves like "Make It Rain", use `effect_id` as an identifier code - the game logic in `move.py` or move effect files will handle the actual implementation.

### Implementing Move Effects in Code

For moves with special effects (beyond basic damage), you need to implement the effect in Python code. Here's how:

#### Example: Thousand Arrows (ignores type immunity)

**Step 1: Add to moves.json**

```json
{
  "id": 614,
  "identifier": "thousand-arrows",
  "power": 90,
  "pp": 10,
  "accuracy": 100,
  "priority": 0,
  "type_id": 5,
  "damage_class_id": 1,
  "effect_id": 373,
  "effect_chance": null,
  "target_id": 9,
  "crit_rate": 0,
  "min_hits": 1,
  "max_hits": 1
}
```

Effect ID 373 is the code for "ignores type immunity" - used by Thousand Arrows and Thousand Waves.

**Step 2: Add the logic in pokemon_mechanics.py**

In `/home/gojo/projects/dueler/goatjo/pokemonduel/pokemon/pokemon_mechanics.py`, the `effectiveness()` method checks for this:

```python
def effectiveness(self, attacker_type: ElementType, battle, *, attacker=None, move=None):
    """Calculates a float representing the effectiveness of `attacker_type` damage on this poke."""
    effectiveness = 1
    
    defender_types = self.type_ids.copy()
    
    # Special case: Thousand Arrows (effect 373) ignores type immunity
    if move is not None and move.effect == 373:
        # Still hit Flying types even if Ground move would normally be immune
        # Type effectiveness still applies (2x, 0.5x, etc.)
        pass  # Don't return early on immunity
    else:
        # Normal type immunity logic
        if attacker_type == ElementType.GROUND and ElementType.FLYING in defender_types and not self.grounded(battle, attacker=attacker, move=move):
            return 1  # Immune
        if attacker_type == ElementType.GHOST and ElementType.NORMAL in defender_types:
            return 1  # Immune
        if attacker_type == ElementType.Psychic and ElementType.DARK in defender_types:
            return 1  # Immune
        # ... more immunity cases
    
    # Continue with effectiveness calculation...
```

#### Example: Smack Down (makes Flying types grounded)

**Step 1: Add to moves.json**

```json
{
  "id": 441,
  "identifier": "smack-down",
  "power": 20,
  "pp": 15,
  "accuracy": 100,
  "priority": 0,
  "type_id": 6,
  "damage_class_id": 1,
  "effect_id": 196,
  "effect_chance": 100,
  "target_id": 9,
  "crit_rate": 0,
  "min_hits": 1,
  "max_hits": 1
}
```

**Step 2: Add in move_attack.py's apply_damage()**

After damage is applied, check for the effect and set grounded state:

```python
def apply_damage(self, attacker, defender, battle, damage, current_type, critical, msg):
    msg += defender.damage(damage, battle, source=self.pretty_name, critical=critical)
    
    # Smack Down effect - makes Flying types grounded
    if self.effect == 196 and not critical:
        if ElementType.FLYING in defender.type_ids:
            defender.grounded_by_move = True
            msg += f"{defender.name} fell out of the sky!\n"
```

#### Example: Move with Multi-Turn Lock (Outrage, Petal Dance)

**Step 1: Add to moves.json**

```json
{
  "id": 200,
  "identifier": "outrage",
  "power": 120,
  "pp": 10,
  "accuracy": 100,
  "priority": 0,
  "type_id": 16,
  "damage_class_id": 1,
  "effect_id": 160,
  "effect_chance": null,
  "target_id": 9,
  "crit_rate": 0,
  "min_hits": 1,
  "max_hits": 1
}
```

**Step 2: Add logic in move_use.py**

In the `use()` method, handle the locked move:

```python
# In move_use.py's use() method
if attacker.locked_move is None:
    # Set up multi-turn moves
    if self.effect == 160:  # Outrage, Petal Dance
        attacker.locked_move = LockedMove(self, random.randint(2, 3))
        attacker.outrage.set_turns(random.randint(2, 3))
        # Or for Petal Dance: attacker.structure = LockedMove(self, ...)
```

And in `pokemon_init.py`, ensure the attributes exist:

```python
self.outrage = ExpiringEffect(0)
self.rollout = ExpiringEffect(0)
self.rampage = ExpiringEffect(0)  # Includes Outrage, Petal Dance, etc.
self.structure = None  # For Petal Dance
```

#### Common Effect IDs Reference

| Effect ID | Description | Implementation Location |
|-----------|-------------|-------------------------|
| 0 | No effect | - |
| 100 | Chance to poison | move_attack.py apply_damage() |
| 106 | Chance to flinch | move_attack.py attack() |
| 196 | Smack Down (ground Flying) | move_attack.py apply_damage() |
| 373 | Ignores type immunity | pokemon_mechanics.py effectiveness() |
| 160 | Multi-turn lock (Outrage) | move_use.py use() |
| 152 | Charge (Solar Beam) | move_use.py use() |
| 256, 257 | Semi-invulnerable (Fly/Dig) | move_use.py use() |
| 380 | Protect | move_checks.py check_protect() |

---

## 4. Adding New Abilities

### Step 1: Add to abilities.json

```json
{
  "id": 300,
  "identifier": "good-as-gold",
  "name": "Good as Gold",
  "description": "Immune to status moves."
}
```

### Step 2: Add to Ability enum

Edit `/home/gojo/projects/dueler/goatjo/pokemonduel/enums/ability.py`:

```python
class Ability(IntEnum):
    BUG = 1
    # ... existing abilities ...
    GOOD_AS_GOLD = 300  # Add at the end
```

### Step 3: Implement in Code

For simple abilities that just grant immunity, add to `pokemon_mechanics.py` in the `ability()` method:

```python
def ability(self, *, attacker=None, move=None):
    # ... existing code ...
    if self._name == "Gholdengo" and self.ability_id == Ability.GOOD_AS_GOLD:
        return Ability.GOOD_AS_GOLD
    # Add new ability checks here
```

For complex abilities with in-battle effects, you'll need to add logic in appropriate places:
- `pokemon_send_out.py` - For abilities that activate on send-out
- `pokemon_turn.py` - For abilities that activate during turns
- `pokemon_damage.py` - For abilities that modify damage
- `moves/` - For abilities that interact with specific moves

---

## 5. Adding New Items

### Step 1: Add to items.json

```json
{
  "id": 2000,
  "identifier": "booster-energy",
  "name": "Booster Energy",
  "description": "Activates Protosynthesis or Quark Drive on Pokemon with those abilities."
}
```

### Step 2: Add to held_item.py

If the item has special effects (like type boosts or abilities), implement in `/home/gojo/projects/dueler/goatjo/pokemonduel/misc/held_item.py`:

```python
def get_damage_multiplier(self, type_id, *, attacker=None, move=None, is_super_effective=False, is_not_very_effective=False):
    # Add item-specific damage multipliers
    if self.get() == "booster-energy":
        if attacker and attacker.ability_id in (Ability.PROTOSYNTHESIS, Ability.QUARK_DRIVE):
            if not attacker.booster_energy:
                attacker.booster_energy = True
                return 1.5
    # ... rest of method
```

---

## 6. Adding Images

### Pokemon Sprites

Place sprite images in `/home/gojo/projects/dueler/goatjo/pokemonduel/data/img/`

Filename format: `{pokemon_id}.png`

For example, Gholdengo (ID 1000):
- Place at: `data/img/1000.png`

Supported formats: PNG, JPG, GIF

### Team Preview Background

Team preview uses images in `generate_team_preview()` from `data_gen/preview.py`.

### Battle UI Images

Battle message generation uses images in `generate_main_battle_message()` from `data_gen/battle_message.py`.

---

## 7. Forms and Variants

### Adding a Form (like Aegislash-Blade)

The code handles many forms automatically in `pokemon/__init__.py`'s `create()` function. For special forms:

#### Step 1: Add form entry in forms.json

```json
{
  "identifier": "gholdengo-h",
  "base_id": 1000,
  "pokemon_id": 1001,
  "height": 30,
  "weight": 43,
  "base_experience": 265,
  "order": 1001
}
```

#### Step 2: Add stats for form in pokemon_stats.json

```json
{
  "pokemon_id": 1001,
  "stats": [60, 55, 65, 125, 65, 100]
}
```

#### Step 3: Add types for form in ptypes.json

```json
{
  "id": 1001,
  "types": [9, 8]
}
```

The `create()` function in `pokemon/__init__.py` automatically handles:
- Mega evolutions (mega-stone items)
- Form transformations (Aegislash-blade, etc.)
- Form-based stat lookups

---

## 8. Code Architecture

### How the Modules Work

```
pokemonduel/
├── pokemon/
│   ├── __init__.py          # DuelPokemon class + create() function
│   ├── pokemon_init.py      # __init__ with all attributes
│   ├── pokemon_send_out.py  # send_out(), send_out_ability(), remove()
│   ├── pokemon_turn.py      # next_turn() - turn-based resets
│   ├── pokemon_damage.py    # damage(), heal(), faint(), confusion, flinch, etc.
│   ├── pokemon_stats.py     # stat calculations, stage modifiers
│   └── pokemon_mechanics.py # ability(), effectiveness(), grounded(), etc.
│
├── moves/
│   ├── __init__.py          # Move class combining all mixins
│   ├── move_init.py         # __init__, setup(), get_priority(), get_effect_chance()
│   ├── move_use.py          # use() - main move execution logic
│   ├── move_attack.py       # attack(), calculate_damage(), apply_damage()
│   ├── move_power.py        # get_power() - damage calculation
│   ├── move_type.py         # get_type() - type determination
│   └── move_checks.py       # check_executable(), check_hit(), etc.
│
├── trainers/
│   ├── trainer_base.py      # Base Trainer class
│   ├── member_trainer.py    # Human player (Discord member)
│   └── npc_trainer.py       # AI opponent
│
├── battle/
│   └── battle.py            # Main battle loop and logic
│
├── misc/
│   ├── expiring_effect.py   # Time-based effects (confusion, etc.)
│   ├── expiring_item.py     # Items with duration (disable, encore)
│   ├── non_volatile_effect.py # Status conditions
│   ├── held_item.py         # Held item logic
│   └── weather.py           # Weather system
│
└── data_gen/
    ├── query.py             # find(), find_one() - data access
    ├── preview.py           # Team preview image
    └── battle_message.py    # Battle UI image
```

### Key Class Inheritance

**DuelPokemon** inherits from multiple mixin classes:
- `DuelPokemonInit` - All attributes and initialization
- `DuelPokemonSendOut` - Send out logic
- `DuelPokemonTurn` - Turn processing
- `DuelPokemonDamage` - Damage and healing
- `DuelPokemonStats` - Stat calculations
- `DuelPokemonMechanics` - Abilities, types, mechanics

**Move** inherits from:
- `MoveInit` - Properties and setup
- `MoveUse` - Execution logic
- `MoveAttack` - Attack calculation
- `MovePower` - Power calculation
- `MoveType` - Type determination
- `MoveChecks` - Validity checks
- `MoveHelpers` - Helper properties

---

## 9. Testing New Content

### Quick Test

```python
# Test a Pokemon can be created
from pokemonduel.pokemon import create
from pokemonduel.data_gen import find_one

# Get some test data
ctx = None  # Not needed for most queries
form = await find_one(ctx, "forms", {"identifier": "gholdengo"})
print(f"Found: {form}")

# Test creating the pokemon
raw_data = {
    "pokname": "Gholdengo",
    "poknick": "None",
    "hpiv": 31, "atkiv": 31, "defiv": 31,
    "spatkiv": 31, "spdefiv": 31, "speediv": 31,
    "hpev": 252, "atkev": 0, "defev": 0,
    "spatkev": 252, "spdefev": 0, "speedev": 4,
    "pokelevel": 50, "shiny": False, "radiant": False,
    "skin": "", "id": 1, "hitem": "none",
    "happiness": 70, "moves": ["make-it-rain", "shadow-ball"],
    "nature_stat_deltas": {"Attack": 1, "Defense": 1, "Special attack": 1, "Special defense": 1, "Speed": 1},
    "ability_index": 0, "nature": "Modest", "gender": "M",
    "ability": "good-as-gold", "mega_ability": "None"
}
poke = await create(ctx, raw_data)
print(f"Created: {poke.name}, HP: {poke.hp}")
```

### Run the Bot

```bash
cd /home/gojo/projects/dueler/goatjo
source .venv/bin/activate
python main.py
```

Then use the bot commands to test battles:
- `;pokemonduel party set` - Set your team
- `;pokemonduel duel @opponent` - Start a battle

---

## 10. Common Issues and Solutions

### Missing attributes error

If you get `AttributeError: 'DuelPokemon' object has no attribute 'X'`, the attribute is missing from `pokemon_init.py`. Add it to the `__init__` method.

### Data file not found

Make sure JSON files are in `/home/gojo/projects/dueler/goatjo/pokemonduel/data/`, not in subdirectories.

### Import errors

When adding new enums, make sure to import them where used:
```python
from ..enums import Ability, ElementType, DamageClass, MoveTarget
```

### Form not loading

Check that the form identifier in `forms.json` matches exactly what's used in code (lowercase, hyphens).

---

## 11. Finding IDs for Data

To find the next available ID for new content:

```bash
# Find highest Pokemon ID
python -c "
import json
with open('pokemonduel/data/forms.json') as f:
    data = json.load(f)
    max_id = max(item['pokemon_id'] for item in data)
    print(f'Next available Pokemon ID: {max_id + 1}')

with open('pokemonduel/data/moves.json') as f:
    data = json.load(f)
    max_id = max(item['id'] for item in data)
    print(f'Next available Move ID: {max_id + 1}')

with open('pokemonduel/data/abilities.json') as f:
    data = json.load(f)
    max_id = max(item['id'] for item in data)
    print(f'Next available Ability ID: {max_id + 1}')
"
```

---

This guide covers the essentials. For more complex mechanics like specific move effects or ability interactions, examine the existing implementations in the source code to understand the patterns used.