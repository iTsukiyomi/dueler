# Implementation and Verification Plan - Milestone 2

## Steps

### Step 1: Backup and Rename
- Copy `/home/gojo/UE5/dueler/frontend/public` recursively to `/home/gojo/UE5/dueler/frontend_public_backup` as a safe backup.
- Rename `/home/gojo/UE5/dueler/frontend` to `/home/gojo/UE5/dueler/frontend_old`.

### Step 2: Initialize Vite App
- Run `npm create vite@latest frontend -- --template react-ts` inside `/home/gojo/UE5/dueler`.
- Verify the `frontend` directory is created and has a basic Vite template structure.

### Step 3: Install Dependencies
- Run `npm install` for production dependencies: `lucide-react`, `framer-motion`, `uuid`, `react-router-dom`, `zustand` in `frontend`.
- Run `npm install -D` for development dependencies: `tailwindcss`, `postcss`, `autoprefixer`, `@types/node`, `@types/uuid` in `frontend`.

### Step 4: Configure PostCSS, Tailwind, and Vite
- Create/modify `postcss.config.js` with `tailwindcss` and `autoprefixer`.
- Create/modify `tailwind.config.js` with content paths (`./index.html`, `./src/**/*.{js,ts,jsx,tsx}`) and fonts: Unbounded, Outfit, Share Tech Mono, Rajdhani.
- Modify `vite.config.ts` to include:
  - `@` path alias mapping to `./src`
  - server port `5173`
  - `/api` proxy mapping to `http://localhost:3001`
- Configure `tsconfig.json` or `tsconfig.app.json` for path aliases (`@/*` -> `src/*`).
- Modify `src/index.css` to add Tailwind directives.

### Step 5: Restore Assets & Cleanup
- Restore `/home/gojo/UE5/dueler/frontend_public_backup/*` (or `frontend_old/public/*`) into `/home/gojo/UE5/dueler/frontend/public/`.
- Verify restore.
- Delete `frontend_old` and `frontend_public_backup`.

### Step 6: Verify and Build
- Run `npm run build` inside `frontend`.
- Verify output builds with zero errors.
