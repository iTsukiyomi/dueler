# Original User Request

## Initial Request — 2026-06-06T16:22:11+05:30

Redesign and implement the React + Vite + TypeScript frontend dashboard at `/home/gojo/UE5/dueler/frontend` to be a premium, harmoniously styled, and feature-rich interface for the Pokemon Duel bot.

Working directory: /home/gojo/UE5/dueler
Integrity mode: development

## Requirements

### R1. UI/UX Redesign & Layout (Aesthetic Excellence)
- Revamp the entire frontend dashboard with rich, harmoniously designed custom styles.
- Eliminate all component misalignments and layout glitches. The theme should be a modern dark/light mode with sleek Pokemon-themed elements.
- Create polished transitions, clear typography, and responsive grid layouts.

### R2. Discord OAuth2 Login
- Integrate Discord OAuth2 login for secure session management.
- Allow users to authenticate, retrieve their avatar/name, and display their profile on a dedicated Profile page.

### R3. Team Builder & Manager
- Provide UI screens to view, create, edit, and delete teams.
- Integrate Import/Export to/from Pokemon Showdown text format.
- Persist team configurations back to the MongoDB Atlas database.

### R4. AI Assistant Chat (Gemini Integration)
- Add a dedicated AI Chat interface where users can converse with a Gemini model.
- The assistant should be capable of:
  - Reading the user's database state (e.g. current teams, stats, profile data).
  - Answering general Pokemon mechanics questions.
  - Generating and recommending teams that the user can directly save/apply.

## Verification Plan

### Automated/Build Tests
- Run `npm run build` inside `frontend` to verify TypeScript compile and Vite asset bundling.
- Verify OAuth2 callback handling routes build without errors.

### Manual Verification
- Deploy/start local development server using `npm run dev` and verify visually.
- Test team creation, import/export with Showdown formats, and mock database persistence.
- Test Gemini chat integration mock queries.

### Acceptance Criteria

### Visuals & Pages
- [ ] Responsive layouts for Home, Profile, Team Manager, and AI Chat pages.
- [ ] Aesthetic theme using clean typography, polished glassmorphism or high-end components.
- [ ] No layout/alignment glitches.

### Core Features
- [ ] Discord OAuth login is fully operational.
- [ ] Showdown import/export parsing is robust and correct.
- [ ] Users can edit/create/delete teams from the dashboard interface.
- [ ] AI Chat provides responses utilizing database-derived team context and pokemon info.

## Follow-up — 2026-06-06T11:14:02Z

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
