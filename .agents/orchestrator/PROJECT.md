# Project: Pokemon Duel Bot Dashboard Rebuild

## Architecture
- **Frontend**: React + Vite + TypeScript. Styled with Tailwind CSS, Lucide icons, and Framer Motion for premium Pokemon-themed dark/light UI. Component states managed via Zustand. Routing via `react-router-dom`.
- **Backend**: Fastify server with MongoDB (Mongoose) persistence, exposing endpoints for:
  - Auth: Discord OAuth2 login & session management
  - Stats: Trainer details, win/loss stats, battle history, leaderboard
  - Teams: CRUD operations for team configurations, supporting Pokemon Showdown text format import/export
  - Chat: Gemini-powered AI chat integrating trainer database context (profile, teams, stats) and game mechanics data
- **Launcher**: `start_web.sh` running both services concurrently.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Plan & Setup | Initialize PROJECT.md and progress.md | None | DONE |
| 2 | Wipe & Init Vite | Wipe `/home/gojo/UE5/dueler/frontend` and initialize Vite/React/TS, Tailwind, Zustand, react-router-dom, etc. | M1 | DONE |
| 3 | Base Components | Implement custom background, collapsable sidebar, neon buttons, card stack, dropdown, empty state, navbar, scroll animation, slider, spinner, tooltip, menu button from `info/` specifications | M2 | IN_PROGRESS |
| 4 | Pages & Routing | Implement LandingPage, ProfilePage, TeamListPage, TeamEditorPage, ChatPage, Leaderboard, Battle History, and routing | M3 | PLANNED |
| 5 | Backend Integration | Hook Auth, Trainer Profile, Teams CRUD, and Chat with the Fastify backend / MongoDB database | M4 | PLANNED |
| 6 | E2E & start_web.sh | Update `start_web.sh`, compile frontend with zero TS errors, verify full app end-to-end | M5 | PLANNED |

## Interface Contracts
### Frontend ↔ Fastify Backend
- **Auth**:
  - `GET /api/auth/discord/login` - Redirect to Discord OAuth
  - `GET /api/auth/discord/callback` - Handle callback, establish session/token
  - `GET /api/auth/me` - Get logged-in user profile, avatar, username
- **Trainer Profile & Stats**:
  - `GET /api/player/profile` - Get logged-in trainer profile details, stats (wins, losses, rank)
  - `GET /api/stats/leaderboard` - Get top players sorted by rating
  - `GET /api/stats/history` - Get recent battle history for the trainer
- **Teams CRUD**:
  - `GET /api/teams` - Get all teams for the logged-in trainer
  - `POST /api/teams` - Create a new team
  - `PUT /api/teams/:id` - Update an existing team configuration
  - `DELETE /api/teams/:id` - Delete a team
- **AI Chat**:
  - `POST /api/chat` - Send user message, get Gemini model response utilizing context from database (trainer stats/teams) and Pokemon mechanics

## Code Layout
- `/home/gojo/UE5/dueler/frontend` - React Application
  - `/src`
    - `/components` - Background, Sidebar, NeonButton, CardStack, Dropdown, Spinner, etc.
    - `/pages` - LandingPage, ProfilePage, TeamListPage, TeamEditorPage, ChatPage, LeaderboardPage, HistoryPage
    - `/store` - Zustand store for player auth, teams, chat messages
    - `/utils` - Showdown import/export parser
    - `App.tsx` - Main app file with Routing
    - `main.tsx` - Vite entrypoint
    - `index.css` - Tailwind CSS imports
