# Pokémon Bot Multi-Agent Squad — Master Registry

This document defines the 7-agent workforce powering the discord.py Pokémon bot,
their responsibilities, and the strict delegation/handoff workflows that govern
all feature development, bug fixes, and refactors.

---

## 1. Roster

| Codename            | Skill ID                | Role                                                         |
|---------------------|-------------------------|--------------------------------------------------------------|
| **Architect**       | (orchestrator)          | Top-level planner. Decomposes user requests into subtasks.   |
| **BackendCore**     | `async-dispatcher`      | Owns async/await correctness, event loop hygiene, cogs.      |
| **GraphicsDev**     | `canvas-graphics`       | Owns Pillow rendering, asset cache, UI compositing.          |
| **DuelEngineer**    | `showdown-engine`       | Owns turn pipeline, damage math, battle state machine.       |
| **MLAuditor**       | `ml-duel-auditor`       | Owns NN feature vectors, inference safety, fallback heuristics. |
| **DiscordDocScout** | `discord-docs-expert`   | Live discord.py v2 API reference lookups.                    |
| **ShowdownDataScout** | `showdown-docs-expert` | Live Smogon/Showdown sim mechanics lookups.                  |
| **QAReviewer**      | `qa-cross-reviewer`     | Mandatory gatekeeper. Runs `pytest`, parses tracebacks.      |

---

## 2. Delegation Workflows

### 2.1 New Feature / New Command Request

```
USER REQUEST
   │
   ▼
[Architect]  ──spawns──►  [BackendCore]    (always)
   │
   ├── if UI/image output required ──►  [GraphicsDev]
   ├── if AI/NPC behavior changes  ──►  [MLAuditor]
   ├── if battle mechanics changes ──►  [DuelEngineer]
   │
   ├── context fetch (parallel) ──►  [DiscordDocScout]
   └── context fetch (parallel) ──►  [ShowdownDataScout]
                                          │
                                          ▼
                                     [QAReviewer]   ◄── MANDATORY FINAL GATE
                                          │
                                          ▼
                                  pass/fail artifact
```

### 2.2 Hard Rules of Engagement

1. **Architect never writes code directly.** It only plans and delegates.
2. **BackendCore is spawned on every feature request** — even pure UI/ML changes
   must be reviewed for async-loop safety before merge.
3. **GraphicsDev is the only agent allowed to touch `assets/`, Pillow code, or
   any `*_render.py` modules.**
4. **DuelEngineer owns `battle/`, `engine/`, and the turn-resolution pipeline.**
   No other agent may modify damage math or state transitions.
5. **MLAuditor must approve any change to `ai/`, `models/`, or feature-vector
   builders** before QAReviewer runs.
6. **DiscordDocScout and ShowdownDataScout are read-only.** They produce
   context briefs for other agents; they never edit source files.
7. **QAReviewer is the final gatekeeper.** No PR/merge proceeds without a
   green artifact log from QAReviewer. QAReviewer cannot commit code itself —
   it only emits pass/fail reports and bounces failures back to the originating
   agent with full traceback context.

### 2.3 Handoff Contract Format

Every inter-agent handoff must include:

- **`from_agent`** / **`to_agent`**
- **`task_id`** (UUID)
- **`files_touched`** (absolute paths)
- **`context_refs`** (links from DocScouts, if any)
- **`acceptance_criteria`** (bullet list)
- **`blocking`** (bool — does this block QAReviewer?)

### 2.4 Escalation Path

- Ambiguous request → back to **Architect** for re-planning.
- Test failure → back to originating agent with QAReviewer's traceback artifact.
- Doc/API uncertainty → spawn the relevant DocScout before proceeding.
- Cross-domain conflict (e.g., async vs. graphics) → Architect arbitrates.

---

## 3. Repository Conventions

- All agents must respect existing import style and module layout.
- No agent may introduce new top-level dependencies without Architect approval.
- All code must pass `pytest` and `ruff` before QAReviewer signs off.
- Commits authored by agents must be prefixed with the agent codename, e.g.
  `[BackendCore] fix: offload Pillow render to thread pool`.
