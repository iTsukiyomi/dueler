## 2026-06-06T11:16:26Z
You are a teamwork_preview_worker. Your working directory is `/home/gojo/UE5/dueler/.agents/worker_m2`.
Your mission is to execute Milestone 2: Wipe & Initialize Vite App in the `/home/gojo/UE5/dueler` repository.
You must:
1. Safely backup the assets from the existing `frontend/public` directory (which contains critical Pokémon sprites, background image, and manifest.json).
2. Wipe the existing `frontend` directory. Rename `frontend` to `frontend_old` to prevent any loss of assets.
3. Initialize a clean React + Vite + TypeScript application in `frontend` folder using `npm create vite@latest frontend -- --template react-ts`.
4. Install production dependencies: `lucide-react`, `framer-motion`, `uuid`, `react-router-dom`, `zustand`.
5. Install development dependencies: `tailwindcss`, `postcss`, `autoprefixer`, `@types/node`, `@types/uuid`.
6. Configure:
   - `postcss.config.js` with tailwindcss and autoprefixer.
   - `tailwind.config.js` with content paths and Unbounded, Outfit, Share Tech Mono, Rajdhani fonts.
   - `vite.config.ts` with react plugin, `@` path alias mapping to `./src`, and server port 5173 with `/api` proxy mapping to `http://localhost:3001`.
   - `tsconfig.json` (or `tsconfig.app.json` if Vite v6 structure is used) to configure the `@/*` path mapping alias.
   - `src/index.css` with Tailwind directives:
     ```css
     @tailwind base;
     @tailwind components;
     @tailwind utilities;
     ```
7. Restore the backup of `public/` assets back into the new `frontend/public/` directory.
8. Delete `frontend_old` after restoring assets.
9. Verify that `npm run build` runs successfully inside `frontend` with zero compilation or TS errors.
10. Write a handoff report at `/home/gojo/UE5/dueler/.agents/worker_m2/handoff.md` detailing the commands you ran, package versions installed, files created/modified, and the build outputs/results.

> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Send a message back to the orchestrator (conversation ID: b1e9cd8f-9ca5-4cd8-9ae4-f2b82854ec17) when done.
