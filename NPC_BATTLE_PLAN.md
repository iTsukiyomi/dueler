# NPC Battle System Plan

## Goal
Create an NPC battle system where players can fight AI opponents that play like top Pokemon Showdown ranked players.

## Folder Structure
```
pokemonduel/modes/npc/
├── __init__.py
├── npc_ai.py        # Smart AI brain
└── npc_team_gen.py  # Wrapper for team generation
```

## Components

### 1. npc_team_gen.py
- Wrapper functions around existing `random_team_gen.py`
- Functions:
  - `generate_npc_team()` - Generate a random team for NPC
  - `convert_to_raw_data()` - Convert team to raw_data format

### 2. npc_ai.py
The AI brain with the following logic:

**Move Selection:**
- Calculate move scores based on:
  - Base power
  - STAB bonus (1.5x)
  - Type effectiveness vs opponent
  - Coverage (how many types it hits super-effectively)
  - Utility (status, hazards, healing, setup)
  - Choice item locked moves
- Prefer moves that:
  - Can OHKO or 2HKO opponent
  - Hit opponent's weaknesses
  - Set up hazards/status if beneficial

**Switching Decision:**
- Switch if:
  - Current pokemon is threatened (opponent move is 4x effective)
  - Current pokemon is statused and has no good recovery
  - Another pokemon has better matchup
  - Predicting opponent will set up/hazard
- Switch to:
  - Pokemon with type advantage
  - Pokemon that can counter opponent's setup
  - Safe switch (like pursuit blocker)

**Prediction:**
- Predict opponent switches based on:
  - Being in kill range
  - Being statused
  - Having no good moves left
-Predict opponent moves based on:
  - Their available moves' power
  - What would be most punished by current pokemon

**General Strategy:**
- Identify win condition (best sweeper vs opponent's checks)
- Preserve necessary pokemon (defensive answers)
- Play around common mechanics (hazards, status, setup)
- Know matchups (what beats what)

### 3. Integration with commands.py

**New Commands:**
```
;duel npc        - User team vs random NPC team
;duel random npc - Both random teams
```

**Flow:**
1. Parse command
2. Generate teams (user's party or random)
3. Create trainers (MemberTrainer for user, NPCTrainer for AI)
4. Create Battle and run

## Implementation Steps

1. Create `pokemonduel/modes/npc/` folder
2. Create `__init__.py`
3. Create `npc_team_gen.py` with team generation wrappers
4. Create `npc_ai.py` with:
   - Score calculation for moves
   - Switch evaluation
   - Prediction logic
5. Modify `NPCTrainer` in `trainers/npc_trainer.py` to use the new AI
6. Add commands to `commands.py` (after testing AI)
7. Test thoroughly

## Key Files to Modify
- `pokemonduel/trainers/npc_trainer.py` - Update to use smart AI
- `pokemonduel/cog/commands.py` - Add npc commands
- Create new files in `pokemonduel/modes/npc/`