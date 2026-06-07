# BRIEFING — 2026-06-06T17:07:00+05:30

## Mission
Complete the Pokemon Duel frontend rebuild: create stores, API layer, 7 pages, routing, and styling.

## 🔒 My Identity
- Archetype: Teamwork orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /home/gojo/UE5/dueler/.agents/orchestrator_v2
- Original parent: main agent
- Original parent conversation ID: c220d0ae-9b51-4f4c-8b77-97ff83867d1f

## 🔒 My Workflow
- **Pattern**: Project / Direct iteration
- **Scope document**: /home/gojo/UE5/dueler/.agents/sentinel_v2/ORIGINAL_REQUEST.md
1. **Decompose**: 3 parallel milestones + 1 verification milestone
   - M1: API layer + Stores + Showdown parser + index.css (foundational)
   - M2: Sidebar customization + App.tsx routing + main.tsx
   - M3: All 7 pages (depends on M1 and M2 patterns)
   - M4: Build verification + TypeScript error fixes
2. **Dispatch & Execute**: Workers for M1, M2, M3 in parallel, then M4 after
3. **On failure**: Retry with error output
4. **Succession**: At 16 spawns

## 🔒 Key Constraints
- Sidebar already uses react-router-dom (NOT Next.js) — no conversion needed
- Must use existing 24 UI components, do NOT create new variants
- Backend at http://localhost:3001
- Final verification: `cd frontend && npm run build` must have ZERO errors
- tsconfig has `noUnusedLocals: true` and `noUnusedParameters: true` — strict
- tsconfig has `verbatimModuleSyntax: true` — must use `import type` for type-only imports

## Current Parent
- Conversation ID: c220d0ae-9b51-4f4c-8b77-97ff83867d1f

## Key Decisions Made
- Sidebar does NOT need Next.js conversion (already uses react-router-dom)
- M1 and M2 can run in parallel since they're independent
- M3 pages need to know the store/API interfaces from M1

## Key API Shapes (from server routes)
- GET /api/auth/me → { id, username, avatar, avatarUrl }
- POST /api/auth/logout → { success: true }
- GET /api/player/profile → { username, wins, losses, elo, wallet, active_party_name, theme, gen, rank }
- GET /api/teams → [{ name, pokemon_count, pokemon: [{pokname, pokemon_id, shiny}], updated_at, is_active }]
- GET /api/teams/:name → { name, pokemon: [...full slots], created_at, updated_at }
- POST /api/teams → { name, pokemon } → team obj
- PUT /api/teams/:name → { pokemon } → { success }
- DELETE /api/teams/:name → { success }
- POST /api/teams/:name/activate → { success }
- GET /api/leaderboard?limit=N → { leaderboard: [{rank, username, avatarUrl, elo, wins, losses, winRate}], updatedAt }
- GET /api/battles/history → { battles: [{id, opponent, opponentAvatar, result, myTeam, opponentTeam, eloChange, timestamp, duration, turns}], updatedAt }
- POST /api/chat → { message, history } → { text }
- GET /api/stats/global → { totalUsers, totalServers, totalBattles, updatedAt }

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|

## Succession Status
- Succession required: no
- Spawn count: 0 / 16
- Pending subagents: none
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: not started
- Safety timer: none
