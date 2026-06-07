# BRIEFING — 2026-06-06T11:15:00Z

## Mission
Orchestrate the complete wipe and rebuild of the React + Vite + TypeScript frontend application and launcher configuration.

## 🔒 My Identity
- Archetype: orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /home/gojo/UE5/dueler/.agents/orchestrator
- Original parent: main agent
- Original parent conversation ID: 0c81d0f9-3717-4f56-bae5-f9324945d49b

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: /home/gojo/UE5/dueler/.agents/orchestrator/PROJECT.md
1. **Decompose**: Decompose the task into milestones (wipe, init, components, pages, integration, build, verify)
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: Explorer → Worker → Reviewer → test → gate
   - **Delegate (sub-orchestrator)**: Spawn a sub-orchestrator if needed. (We will use direct iteration loops or sub-orchestrators for milestones)
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns. Write handoff.md, spawn successor.
- **Work items**:
  1. Initialize and configure Project Plan [pending]
  2. Wipe and Initialize Vite App [pending]
  3. Recreate components from specifications in info/ [pending]
  4. Build dashboard pages and routing [pending]
  5. Integrate backend endpoints and state store [pending]
  6. Final E2E build and verification [pending]
- **Current phase**: 2
- **Current focus**: Wipe and Initialize Vite App

## 🔒 My Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- File-editing tools allowed only for metadata/state files (.md) in .agents/.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent
- Conversation ID: 0c81d0f9-3717-4f56-bae5-f9324945d49b
- Updated: not yet

## Key Decisions Made
- Preserve `frontend/public/` contents (sprites, manifest, icons) during wipe by renaming `frontend` to `frontend_old` and restoring it after init.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| Explorer 1 | explorer | Explore M2 Strategy | completed | fe7bb057-3f44-4231-911d-2df4d7873b4b |
| Explorer 2 | explorer | Explore M2 Strategy | completed | fa4f1b6d-d1f5-4aec-9051-ead1087cdd8e |
| Explorer 3 | explorer | Explore M2 Strategy | completed | 2e91ba43-04d8-4612-bf65-974944b7212d |
| Worker 1 (M2) | worker | Execute M2 Wipe & Init | completed | 5fe450a2-2b2e-4c93-9aa5-5968066e3dfc |
| Reviewer 1 (M2) | reviewer | Review M2 Work | completed | 40ca1571-2a0e-460e-9f70-63f3d2fb24cf |
| Reviewer 2 (M2) | reviewer | Review M2 Work | completed | 3385d5f3-8a07-4d03-99be-6520155e44d7 |
| Worker 2 (M2 Fix) | worker | Execute M2 Fixes | completed | b26d079e-2fd2-4a71-8c62-f93f59047e33 |
| Auditor (M2) | auditor | Audit M2 integrity | completed | 7ebfc85d-7ad3-4c05-8c64-3ab761e26fe1 |
| Explorer 1 (M3) | explorer | Explore M3 Strategy | completed | 8d2b10b4-01da-4812-86a9-fc8ef0239364 |
| Explorer 2 (M3) | explorer | Explore M3 Strategy | completed | 57c8260a-37f2-44fb-a9b3-beacff83b6e7 |
| Explorer 3 (M3) | explorer | Explore M3 Strategy | completed | 75343bcf-fd83-4633-9ccc-cc849eaa3ec3 |
| Worker (M3) | worker | Execute M3 Components | pending | 10fbe47c-5615-4bc5-bd25-dd0be66071be |

## Succession Status
- Succession required: no
- Spawn count: 12 / 16
- Pending subagents: 10fbe47c-5615-4bc5-bd25-dd0be66071be
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: task-23
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run manage_task(Action="list") — re-create if missing

## Artifact Index
- /home/gojo/UE5/dueler/.agents/orchestrator/PROJECT.md — Project Scope and Milestones
- /home/gojo/UE5/dueler/.agents/orchestrator/progress.md — Execution heartbeat and progress tracking
- /home/gojo/UE5/dueler/.agents/orchestrator/original_prompt.md — Copy of the user request
