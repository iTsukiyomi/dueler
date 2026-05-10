# Pokemon Duel - Developer Technical Manual

This guide documents the fully modularized Pokemon Discord bot architecture. Every system has been separated into focused, single-responsibility modules that can be extended independently.

---

## 1. The Modular Blueprint

### Directory Structure

```
goatjo/
├── DEVELOPER_GUIDE.md          # This file
└── pokemonduel/                 # Main package
    ├── __init__.py              # Entry point (exports PokemonDuel cog)
    │
    ├── battle/                  # Core battle system
    │   ├── __init__.py
    │   └── battle.py            # Main Battle class (~491 lines)
    │
    ├── cog/                     # Discord command handler
    │   ├── __init__.py
    │   └── commands.py          # PokemonDuel Cog class (~480 lines)
    │
    ├── config/                  # Configuration management
    │   ├── __init__.py
    │   └── config_manager.py    # EnhancedConfigManager classes
    │
    ├── data_gen/                # Data access & image generation
    │   ├── __init__.py          # Exports find, find_one, generate_*
    │   ├── query.py             # find() and find_one() functions
    │   ├── preview.py           # Team preview image generation
    │   └── battle_message.py    # Battle UI image generation
    │
    ├── enums/                   # Enumeration definitions
    │   ├── __init__.py
    │   ├── ability.py           # Ability enum (300+ abilities)
    │   ├── damage_class.py     # PHYSICAL/SPECIAL/STATUS
    │   ├── element_type.py      # 18 Pokemon types
    │   └── move_target.py       # Move targeting enums
    │
    ├── misc/                    # Shared utility classes
    │   ├── __init__.py
    │   ├── baton_pass.py        # Baton pass effect handler
    │   ├── expiring_effect.py   # Base class for timed effects
    │   ├── expiring_item.py     # Item with duration
    │   ├── expiring_wish.py     # Wish move effect
    │   ├── held_item.py         # Pokemon held item logic
    │   ├── item.py              # Base Item class
    │   ├── locked_move.py       # LockedMove (bound/trapped)
    │   ├── metronome.py         # Metronome random move
    │   ├── non_volatile_effect.py  # Status (burn/paralyze/sleep)
    │   ├── terrain.py           # Battle terrain (grassy/electric)
    │   └── weather.py           # Weather system (rain/sun/sand)
    │
    ├── moves/                   # Move execution logic
    │   ├── __init__.py          # Move class (inherits all mixins)
    │   ├── move_init.py        # Move initialization & properties
    │   ├── move_use.py         # Move execution & targeting
    │   ├── move_attack.py      # Damage dealing logic
    │   ├── move_power.py       # Power calculation
    │   ├── move_type.py        # Move type determination
    │   └── move_checks.py      # Validation & helper methods
    │
    ├── pokemon/                 # Pokemon entity logic
    │   ├── __init__.py         # DuelPokemon class (mixin inheritance)
    │   ├── pokemon_init.py     # Pokemon initialization
    │   ├── pokemon_send_out.py # Send out / remove from battle
    │   ├── pokemon_turn.py     # Turn-based updates
    │   ├── pokemon_damage.py   # Damage, heal, faint, status
    │   ├── pokemon_stats.py    # Stat calculation & stages
    │   └── pokemon_mechanics.py # Transform, form, abilities
    │
    ├── trainers/               # Trainer logic
    │   ├── __init__.py
    │   ├── trainer_base.py     # Base Trainer class
    │   ├── member_trainer.py   # Discord member trainer
    │   └── npc_trainer.py      # AI NPC trainer
    │
    └── ui/                     # Discord UI components
        ├── __init__.py
        ├── duel_accept.py      # Duel request accept view
        ├── team_preview.py     # Team selection preview
        ├── battle_ui.py       # Battle action buttons
        ├── swap_ui.py         # Pokemon swap UI
        ├── forfeit_ui.py      # Forfeit confirmation
        └── mega_evo.py        # Mega evolution UI
```

### Single Responsibility Principle

| Folder | Responsibility | Extension Pattern |
|--------|----------------|-------------------|
| `moves/` | Move execution | Add new file, inherit from Move mixins |
| `pokemon/` | Pokemon entity | Add new mixin, extend DuelPokemon |
| `enums/` | Game constants | Add new enum value |
| `misc/` | Shared effects | Create new effect class |
| `ui/` | Discord UI | Create new View class |
| `data_gen/` | Data/Images | Add new generator function |
| `trainers/` | Trainer logic | Extend Trainer base |
| `battle/` | Battle loop | Modify Battle class |

---

## 2. The "Plug-and-Play" Framework

### 2.1 Moves System

**Location:** `goatjo/pokemonduel/moves/`

**Pattern:** The Move class uses Python multiple inheritance (mixins). Each aspect of a move is in a separate file:
- `move_init.py` - Basic properties (name, power, accuracy, etc.)
- `move_use.py` - How the move is selected and executed
- `move_attack.py` - Damage calculation
- `move_power.py` - Power modifications
- `move_type.py` - Type determination
- `move_checks.py` - Validation and helpers

**Boilerplate Template:**

```python
# In moves/move_init.py or a new file
from ..enums import DamageClass, ElementType, MoveTarget

class MoveInit:
    """Mixin for move initialization."""
    
    def _init_move(self, name: str, power: int, accuracy: int, 
                   element: ElementType, damage_class: DamageClass,
                   target: MoveTarget, effect: int = 0):
        self.name = name
        self.power = power
        self.accuracy = accuracy
        self.element_id = element
        self.damage_class = damage_class
        self.target = target
        self.effect = effect
        # ... other initialization
```

**Registration:** All move files are combined in `moves/__init__.py`:
```python
from .move_init import MoveInit
from .move_use import MoveUse
# ... other imports

class Move(MoveInit, MoveUse, ...):
    pass
```

**How to add a new Move:**
1. Use the `Move` class directly in Pokemon's moves list
2. Moves are loaded from JSON data in `data_gen/query.py`
3. To add new move behavior, add methods to appropriate mixin file

---

### 2.2 Pokemon System

**Location:** `goatjo/pokemonduel/pokemon/`

**Pattern:** DuelPokemon uses 6 mixins for separation of concerns:
- `pokemon_init.py` - __init__ and basic setup
- `pokemon_send_out.py` - Send out / remove logic  
- `pokemon_turn.py` - Turn-by-turn updates
- `pokemon_damage.py` - Damage/healing/faint/staus
- `pokemon_stats.py` - Stat calculation, stages
- `pokemon_mechanics.py` - Transform, form, type effectiveness

**Boilerplate Template:**

```python
# In pokemon/pokemon_xxx.py
class DuelPokemonXXX:
    """Documentation for what this mixin handles."""
    
    def new_method(self, arg1, arg2):
        """Method that handles specific Pokemon functionality."""
        # Implementation
        return result
```

**Registration:** Add import to `pokemon/__init__.py` and add to class inheritance:
```python
from .pokemon_init import DuelPokemonInit
from .pokemon_xxx import DuelPokemonXXX

class DuelPokemon(DuelPokemonInit, DuelPokemonXXX, ...):
    pass
```

---

### 2.3 Abilities System

**Location:** `goatjo/pokemonduel/enums/ability.py`

**Pattern:** Abilities are defined as Enum values with metadata (name, ID, pretty_name).

**Boilerplate Template:**

```python
# In enums/ability.py
class Ability(Enum):
    """Pokemon abilities enumeration."""
    
    # Existing abilities...
    NEW_ABILITY = auto()
    
    @property
    def pretty_name(self):
        return self.name.replace("_", " ").title()
```

**Registration:** Abilities are automatically available once added to the enum. Usage in code:
```python
from ..enums import Ability

if self.ability() == Ability.NEW_ABILITY:
    # Handle new ability
```

**How to add ability logic:** Abilities are checked in various places:
- In `pokemon_damage.py` - damage modifications
- In `pokemon_stats.py` - stat calculations
- In `pokemon_send_out.py` - on-send-out effects
- In `pokemon_turn.py` - end-of-turn effects

---

### 2.4 Items System

**Location:** `goatjo/pokemonduel/misc/`

**Pattern:** Two main classes:
- `item.py` - Base Item class
- `held_item.py` - Logic for held items (activation, consumption)

**Boilerplate Template:**

```python
# In misc/held_item.py or new file
class MyCustomItem:
    """Custom item behavior."""
    
    def activate_on_switch_in(self, battle):
        """Called when Pokemon switches in."""
        return "Custom item activated!\n"
    
    def activate_end_of_turn(self, battle):
        """Called at end of turn."""
        return ""
```

**Registration:** Import in `misc/__init__.py`:
```python
from .held_item import HeldItem, MyCustomItem
```

---

### 2.5 Status Effects (Non-Volatile)

**Location:** `goatjo/pokemonduel/misc/non_volatile_effect.py`

**Pattern:** Handles burn, poison, paralysis, sleep, freeze.

**Boilerplate Template:**

```python
# In misc/non_volatile_effect.py
class NonVolatileEffect:
    # Existing code...
    
    def apply_status(self, status: str, battle, attacker=None, source=""):
        """Apply a status condition."""
        if status == "burn":
            # Burn logic
            return f"{self.poke.name} is burned!\n"
        # ... other statuses
```

---

### 2.6 Weather & Terrain

**Location:** `goatjo/pokemonduel/misc/weather.py` and `terrain.py`

**Boilerplate Template:**

```python
# In misc/weather.py
class Weather(ExpiringEffect):
    """Base weather class."""
    
    def __init__(self):
        super().__init__(5)  # 5 turns duration
    
    def apply(self, battle, user=None):
        """Apply weather to battle."""
        return f"Weather started!\n"

# In misc/terrain.py
class Terrain(ExpiringItem):
    """Base terrain class."""
    
    def __init__(self):
        super().__init__()
```

---

### 2.7 Trainer System

**Location:** `gogo/pokemonduel/trainers/`

**Pattern:** Base Trainer class with Human and NPC subclasses.

**Boilerplate Template:**

```python
# In trainers/trainer_base.py
class Trainer:
    """Base trainer class."""
    
    def __init__(self, name, party):
        self.name = name
        self.party = party
        self.current_pokemon = party[0] if party else None
    
    def valid_moves(self, defender):
        """Return list of valid move indices."""
        return [i for i, m in enumerate(self.current_pokemon.moves) if m.pp > 0]

# In trainers/member_trainer.py
class MemberTrainer(Trainer):
    """Human player trainer."""
    
    def is_human(self):
        return True

# In trainers/npc_trainer.py  
class NPCTrainer(Trainer):
    """AI trainer."""
    
    def is_human(self):
        return False
    
    def move(self, defender, battle):
        # AI logic
        pass
```

**Registration:** Imports in `trainers/__init__.py`:
```python
from .trainer_base import Trainer
from .member_trainer import MemberTrainer
from .npc_trainer import NPCTrainer
```

---

### 2.8 UI System (Discord Views)

**Location:** `goatjo/pokemonduel/ui/`

**Pattern:** Each UI component is a separate file with Discord UI classes.

**Boilerplate Template:**

```python
# In ui/my_new_view.py
import discord
from discord.ui import View, Button

class MyNewView(View):
    """Custom interaction view."""
    
    def __init__(self, battle):
        super().__init__()
        self.battle = battle
    
    @discord.ui.button(label="Action", style=discord.ButtonStyle.primary)
    async def action_button(self, interaction, button):
        await interaction.response.send_message("Action taken!")
        # Handle action
```

**Registration:** Import in `ui/__init__.py`:
```python
from .my_new_view import MyNewView

__all__ = [..., 'MyNewView']
```

---

### 2.9 Data System

**Location:** `goatjo/pokemonduel/data_gen/`

**Pattern:** Functions for JSON data access and image generation.

**Boilerplate Template:**

```python
# In data_gen/my_generator.py
async def generate_something(battle):
    """Generate something for the battle."""
    # Image generation or data processing
    return view_or_embed

# In data_gen/__init__.py
from .my_generator import generate_something

__all__ = [..., 'generate_something']
```

---

## 3. Inter-System Communication

### How Systems Connect

```
┌─────────────────────────────────────────────────────────────────┐
│                        COG (commands.py)                        │
│  Discord command handler - creates Battle, manages context    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BATTLE (battle.py)                          │
│  Main battle loop - orchestrates turns, calls Pokemon methods │
└─────────────────────────────────────────────────────────────────┘
          │                    │                      │
          ▼                    ▼                      ▼
┌──────────────────┐  ┌────────────────┐    ┌─────────────────────┐
│   POKEMON        │  │    TRAINER    │    │     MOVE           │
│ (pokemon/*)      │  │ (trainers/*)  │    │    (moves/*)       │
│                  │  │                │    │                    │
│ - HP calc        │  │ - Party mgmt  │    │ - Damage calc      │
│ - Stats          │  │ - Move select │    │ - Type effect      │
│ - Abilities      │  │ - Swap logic  │    │ - Accuracy check   │
└──────────────────┘  └────────────────┘    └─────────────────────┘
          │                    │                      │
          ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SHARED SYSTEMS                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ ENUMS    │  │  MISC    │  │  DATA    │  │     UI       │   │
│  │ Ability  │  │ Weather  │  │ find()   │  │ Views/Buttons│   │
│  │ Element  │  │ Status   │  │ JSON     │  │              │   │
│  │ Damage   │  │ Items    │  │ Images   │  │              │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Examples

**Battle calling Pokemon ability:**
```python
# In battle/battle.py
if self.trainer1.current_pokemon.ability() == Ability.INTIMIDATE:
    msg += self.trainer2.current_pokemon.append_attack(-1, attacker=attacker, source="Intimidate")
```

**Pokemon using Move:**
```python
# In pokemon/pokemon_damage.py
move.power = move.calculate_power(self, otherpoke, battle)
```

**UI triggering Battle action:**
```python
# In ui/battle_ui.py
async def callback(self, interaction):
    await self.battle.process_turn(self.selected_move)
```

---

## 4. Developer Workflow

### Checklist: Adding a New Feature

1. **Identify the domain** - Which folder does it belong to?
   - New move behavior → `moves/`
   - New Pokemon logic → `pokemon/`
   - New ability → `enums/ability.py` + relevant pokemon file
   - New item → `misc/held_item.py`
   - New UI → `ui/`
   - New data source → `data_gen/`

2. **Create or modify the file**
   - For new files: Follow the boilerplate templates above
   - For modifications: Find the relevant method in appropriate file

3. **Update `__init__.py` if needed**
   - Add new imports to the folder's `__init__.py`

4. **Test the import**
   ```bash
   cd /home/gojo/projects/dueler
   PYTHONPATH=/home/gojo/projects/dueler .venv/bin/python -c "from goatjo.pokemonduel.whatever import Whatever"
   ```

5. **Test the functionality**
   - Run the bot and test the feature

### Debugging a Micro-Module

**To test a specific module without running the bot:**

```bash
cd /home/gojo/projects/dueler
PYTHONPATH=/home/gojo/projects/dueler .venv/bin/python << 'EOF'
# Import the specific module
from goatjo.pokemonduel.moves import Move
from goatjo.pokemonduel.enums import ElementType, DamageClass

# Create a simple test move
move = Move(
    name="Test Move",
    element_id=ElementType.FIRE,
    damage_class=DamageClass.SPECIAL,
    power=80,
    accuracy=100,
    pp=20
)

# Test methods
print(f"Move name: {move.name}")
print(f"Power: {move.power}")
print("Module works!")
EOF
```

---

## 5. Extensibility & Future-Proofing

### Adding a New Top-Level System (e.g., Trading System)

**Step 1: Create the folder structure**
```
goatjo/pokemonduel/
├── trading/                 # New system folder
│   ├── __init__.py         # Export main classes
│   ├── trading_init.py     # Trading initialization
│   ├── trading_offers.py   # Offer handling
│   ├── trading_accept.py   # Accept/Decline logic
│   └── trading_ui.py       # Discord UI for trading
```

**Step 2: Create base classes**
```python
# In trading/trading_init.py
class TradeManager:
    """Manages all trading operations."""
    
    def __init__(self):
        self.active_trades = {}
    
    def create_offer(self, user1, user2, pokemon_id):
        """Create a new trade offer."""
        # Implementation
        pass
    
    def accept_offer(self, trade_id):
        """Accept and process a trade."""
        # Implementation
        pass
```

**Step 3: Add to Cog**
```python
# In cog/commands.py
from ..trading import TradeManager

class PokemonDuel(commands.Cog):
    def __init__(self, bot):
        # ... existing code ...
        self.trading = TradeManager()
```

**Step 4: Add Discord commands**
```python
# In cog/commands.py
@commands.command()
async def trade(self, ctx, pokemon_id: int):
    await ctx.send("Trading not implemented yet!")
```

### Extension Patterns Summary

| Component | Pattern | Add New By |
|-----------|---------|------------|
| Moves | Mixin inheritance | Creating Move instance |
| Pokemon | Mixin inheritance | Adding mixin + __init__ |
| Abilities | Enum + checks | Adding enum + code checks |
| Items | Class inheritance | Creating HeldItem subclass |
| Status | Class methods | Adding status case |
| Weather | Class inheritance | Subclass Weather |
| Terrain | Class inheritance | Subclass Terrain |
| UI | View inheritance | Creating View subclass |
| Trainers | Class inheritance | Subclass Trainer |

---

## 6. Important File Locations Reference

| Feature | File Path | Key Class/Function |
|---------|-----------|-------------------|
| Main entry | `cog/commands.py` | `PokemonDuel` class |
| Battle loop | `battle/battle.py` | `Battle` class |
| Pokemon entity | `pokemon/__init__.py` | `DuelPokemon` class |
| Move execution | `moves/__init__.py` | `Move` class |
| Ability enum | `enums/ability.py` | `Ability` enum |
| Type enum | `enums/element_type.py` | `ElementType` enum |
| Status handling | `misc/non_volatile_effect.py` | `NonVolatileEffect` |
| Weather system | `misc/weather.py` | `Weather` class |
| Terrain system | `misc/terrain.py` | `Terrain` class |
| Item handling | `misc/held_item.py` | `HeldItem` class |
| Data lookup | `data_gen/query.py` | `find()`, `find_one()` |
| Human trainer | `trainers/member_trainer.py` | `MemberTrainer` |
| AI trainer | `trainers/npc_trainer.py` | `NPCTrainer` |
| Battle UI | `ui/battle_ui.py` | `BattlePromptView` |
| Team preview | `ui/team_preview.py` | `PreviewPromptView` |

---

## 7. Quick Reference Commands

```bash
# Test all imports
PYTHONPATH=/home/gojo/projects/dueler .venv/bin/python -c "
from goatjo.pokemonduel.cog.commands import PokemonDuel
from goatjo.pokemonduel.battle.battle import Battle
from goatjo.pokemonduel.pokemon import DuelPokemon
from goatjo.pokemonduel.moves import Move
from goatjo.pokemonduel.trainers import Trainer
from goatjo.pokemonduel.data_gen import find, find_one
print('All imports OK!')
"

# Test specific module
PYTHONPATH=/home/gojo/projects/dueler .venv/bin/python -c "from goatjo.pokemonduel.enums import Ability; print(Ability.INTIMIDATE)"
```

---

This architecture allows any developer to:
1. **Easily locate** where any functionality lives
2. **Quickly extend** any system without touching other code
3. **Safely modify** individual modules in isolation
4. **Scale** the bot by adding new systems without breaking existing code

The modular design ensures that adding a new Pokemon, Move, Ability, or Item requires changes only in the specific relevant file, not scattered throughout the codebase.