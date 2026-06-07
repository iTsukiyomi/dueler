# Original User Request

## Initial Request — 2026-06-06T17:02:43+05:30

Wipe the existing frontend directory and rebuild the React + Vite + TypeScript application from scratch. The design and components must be implemented strictly following the specifications in the `info/` folder. Ensure the frontend and server run together via `start_web.sh`.

Working directory: /home/gojo/UE5/dueler
Integrity mode: development

## Requirements

### R1. Wipe and Initialize Vite App
- Delete the existing `frontend` directory completely.
- Initialize a clean Vite React TypeScript project in the `frontend` folder.
- Install tailwindcss, lucide-react, framer-motion, uuid, react-router-dom, Zustand/state store dependencies.

### R2. Recreate Components from specifications in the `info/` folder
Implement components exactly as specified in the markdown files under `/home/gojo/UE5/dueler/info`:
- Sidebar (`info/sidebar.md`) using custom animations with Framer Motion, converted to use `react-router-dom` instead of Next.js navigation.
- Background (`info/background.md`) featuring `GooeyFilter` and `PixelTrail`.
- Buttons (`info/buttons.md`) featuring the `NeonButton` styling.
- Card (`info/card.md`) featuring the `CardStack` layout.
- Other base elements (Dropdowns, Navbars, ScrollAnimations, Sliders, Spinners, Tooltips, EmptyStates).

### R3. Dashboard Pages & Core Integration
Build responsive and beautiful pages:
- `LandingPage`: Glassmorphic layout with Discord Login trigger.
- `ProfilePage`: Trainer details, stats, wins/losses.
- `TeamListPage`: Show list of teams, Showdown text export/import utility.
- `TeamEditorPage`: Edit Pokemon stats, forms, moves, and items.
- `ChatPage`: AI conversational interface with Gemini model using player database context.
- Leaderboard & Battle History pages.
- Integrate player auth state and CRUD database storage via the Fastify server endpoints.

### R4. Launcher Configuration (`start_web.sh`)
- Hook both server and frontend services to run together under `start_web.sh` so running the script launches the entire app.

## Verification Plan

### Automated/Build Tests
- Run `npm run build` inside `frontend` to verify successful compilation with zero TypeScript errors.
- Run `./start_web.sh` to confirm both services run concurrently and cleanly.

## Acceptance Criteria

### Component Accuracy
- [ ] Sidebar is collapsable with smooth animation and correct routes.
- [ ] Pixel Trail and Gooey Filter background is active and functional.
- [ ] Neon buttons, custom cards, dropdowns are utilized across all pages and aligned perfectly.

### Features & Database Integration
- [ ] Discord OAuth2 callback resolves session.
- [ ] Showdown team import/export parses and prints team list.
- [ ] User can fully edit and save team configurations to MongoDB Atlas.
- [ ] Gemini chatbot responds correctly based on active database trainer context.
