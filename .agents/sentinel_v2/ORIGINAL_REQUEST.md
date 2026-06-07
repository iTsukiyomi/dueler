# Original User Request

## Initial Request — 2026-06-06T17:05:00+05:30

CONTINUE an in-progress frontend rebuild for the Pokemon Duel dashboard. The previous agent run completed the component layer but hit a quota limit before building pages, stores, routing, or API integration.

Working directory: /home/gojo/UE5/dueler
Integrity mode: development

## ALREADY COMPLETED — DO NOT REDO
- The `frontend` directory has been wiped and re-scaffolded as a clean Vite + React + TypeScript project.
- All dependencies are installed (package.json is correct — Tailwind, Framer Motion, Radix UI, Zustand, react-router-dom, lucide-react, uuid, class-variance-authority, etc.)
- 24 UI components exist in `frontend/src/components/ui/` — sidebar, navbar, card-stack, pixel-trail, gooey-filter, neon-button, dropdown, slider, tooltip, empty state, avatar, badge, button, scroll-area, separator, skeleton, label, input, container-scroll-animation, cybernetic-bento-grid, liquid-glass-button, menu-toggle-icon, not-found-page.
- Hooks exist in `frontend/src/hooks/` — use-screen-size, use-debounced-dimensions, use-slider-with-input.
- `frontend/src/lib/utils.ts` exists with a `cn()` helper.
- Tailwind is configured (`tailwind.config.js`, `postcss.config.js`).

## WHAT REMAINS — DO THIS NOW

### 1. State Stores (Zustand)
Create in `frontend/src/stores/`:
- `authStore.ts` — manages Discord OAuth2 session state (user object, isAuthenticated, isLoading, fetchUser, login, logout). The backend API is at `http://localhost:3001` with these endpoints:
  - `GET /api/auth/login` — redirects to Discord OAuth
  - `GET /api/auth/me` — returns current user (uses httpOnly cookie)
  - `POST /api/auth/logout`
- `teamStore.ts` — manages team CRUD. Backend endpoints:
  - `GET /api/teams` — list teams
  - `POST /api/teams` — create team
  - `PUT /api/teams/:name` — update team
  - `DELETE /api/teams/:name` — delete team

### 2. API Utility
Create `frontend/src/api/client.ts` — a thin fetch wrapper that always sends `credentials: 'include'` to the backend at `http://localhost:3001`.
Create `frontend/src/api/chat.ts` — POST to `/api/chat` with `{ message, context }` for Gemini AI chat.

### 3. Pages (in `frontend/src/pages/`)
Build these pages using the existing UI components from `components/ui/`:
- `LandingPage.tsx` — Beautiful glassmorphic hero page with Pokemon theme. Uses PixelTrail + GooeyFilter as background effect. Discord OAuth login button using NeonButton. Should feel premium and exciting.
- `ProfilePage.tsx` — Shows user avatar, Discord username, trainer stats (wins, losses, rank). Uses Card components.
- `TeamListPage.tsx` — Lists all teams from teamStore. Each team shown as a card. Buttons to create new team, delete, and export to Showdown format. Import from Showdown text.
- `TeamEditorPage.tsx` — Edit a specific team. Add/remove Pokemon, set moves, abilities, items, EVs/IVs, nature. Save back to API.
- `ChatPage.tsx` — AI chat interface. Message input, scrollable message history, sends to `/api/chat`. Gemini responds with Pokemon advice using player context.
- `LeaderboardPage.tsx` — Shows top trainers. Fetches from `GET /api/stats/leaderboard`.
- `BattleHistoryPage.tsx` — Shows recent battles. Fetches from `GET /api/stats/history`.

### 4. App.tsx — Routing & Layout
Replace the current boilerplate `App.tsx` with:
- React Router DOM setup with `BrowserRouter` (wrap in `main.tsx`)
- Public route: `/` → LandingPage
- Protected layout at `/dashboard/*` with Sidebar + Navbar wrapping an `<Outlet />`
- Protected child routes: index→ProfilePage, teams→TeamListPage, teams/:name→TeamEditorPage, chat→ChatPage, leaderboard→LeaderboardPage, battles→BattleHistoryPage
- Auth guard that redirects to `/` if not authenticated
- ErrorBoundary wrapper

### 5. main.tsx
Wrap App with BrowserRouter from react-router-dom.

### 6. Showdown Parser Utility
Create `frontend/src/utils/showdown.ts` with:
- `parseShowdownTeam(text: string)` — parses Showdown paste format into team objects
- `exportShowdownTeam(team)` — converts team object back to Showdown text

### 7. Update `start_web.sh`
The file at `/home/gojo/UE5/dueler/start_web.sh` already runs both server and frontend concurrently. Verify it works — it should already be correct since it runs `npm run dev --prefix server &` and `npm run dev --prefix frontend &`.

### 8. index.css Styling
Update `frontend/src/index.css` to include Tailwind directives and set up dark theme CSS variables for the Pokemon dashboard aesthetic.

## IMPORTANT NOTES
- The sidebar component uses Next.js imports (`next/link`, `next/image`, `usePathname`). These MUST be converted to react-router-dom equivalents (`Link` from react-router-dom, `useLocation`, regular `<img>` tags).
- All pages must use the existing UI components — do NOT create new component variants.
- The backend server is a Fastify app in `/home/gojo/UE5/dueler/server/`. Read `server/src/index.ts` and `server/src/config.ts` to understand the API structure.

## Verification
- Run `npm run build` in `frontend` — must compile with zero errors.
- All routes must render without crashes.
- Sidebar navigation must work between all pages.
