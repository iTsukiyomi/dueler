# Handoff Report: Milestone 2 — Wipe and Initialize Vite App

This report outlines the observations, logic chain, caveats, conclusion, and verification methods for Milestone 2: Wipe and Initialize Vite App in the `/home/gojo/UE5/dueler` repository.

---

## 1. Observation

During the read-only exploration, the following exact files, configurations, and directory listings were observed:

1. **Frontend Assets (`frontend/public`)**:
   - Directory listing of `/home/gojo/UE5/dueler/frontend/public` contains:
     - `arena_background.png` (a battle scene UI asset)
     - `pokemon-icons/` (directory containing 187 files, including PNG files like `1.png`, `10.png`, SVGs in `types/`, and a generated `manifest.json`)
   - `fetch-pokemon-icons.mjs` uses the standard HTTP fetch API:
     ```javascript
     const standardUrl = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`;
     ```

2. **Backend Server Configuration (`.env`)**:
   - `/home/gojo/UE5/dueler/.env` defines the following environment variables:
     ```env
     API_PORT=3001
     FRONTEND_URL=http://localhost:5173
     ```

3. **Existing Dev and Production Dependencies (`frontend/package.json`)**:
   - Key libraries currently registered:
     - `"framer-motion": "^11.15.0"`
     - `"lucide-react": "^1.17.0"`
     - `"react-router-dom": "^7.1.1"`
     - `"uuid": "^14.0.0"`
     - `"zustand": "^5.0.3"`
     - `"tailwindcss": "^4.0.0"`
     - `"@tailwindcss/vite": "^4.0.0"`

4. **Vite Proxy Configuration (`frontend/vite.config.ts`)**:
   - Proxy settings route backend traffic:
     ```typescript
     server: {
       port: 5173,
       proxy: {
         "/api": {
           target: "http://localhost:3001",
           changeOrigin: true,
         },
       },
     }
     ```

---

## 2. Logic Chain

1. **Wiping Strategy Safety**: Wiping `frontend/` with standard `rm -rf` without a backup deletes all custom static assets inside `frontend/public/` (specifically `arena_background.png` and `pokemon-icons/`).
2. **Asset Recovery Risk**: Since our runtime environment operates under `CODE_ONLY` network rules and potentially offline sandbox configurations, running `node fetch-pokemon-icons.mjs` to re-download all sprite assets from `raw.githubusercontent.com` will fail.
3. **Backup Requirement**: Therefore, the wiping strategy must involve a temporary step to copy the custom static folders to `/home/gojo/UE5/dueler/frontend_backup` before wiping the directory, and then copying them back after `npm create vite` runs.
4. **Backend Connectivity**: The backend runs on port 3001 (based on `.env` `API_PORT=3001`). Therefore, the new `vite.config.ts` must maintain a proxy configuration forwarding `/api` requests to `http://localhost:3001`.
5. **Path Aliasing**: Modern React imports in this codebase use the `@/` prefix (mapping to `./src/*`). The configuration for both Vite and TypeScript (`tsconfig.json`/`tsconfig.app.json`) must include path aliases to prevent import compilation failures.
6. **Tailwind Configurations**: The user explicitly requested installing `tailwindcss`, `postcss`, and `autoprefixer`. In Tailwind v3, these three packages work through PostCSS. In Tailwind v4, this can be handled via the `@tailwindcss/postcss` plugin or natively with `@tailwindcss/vite` (which was utilized in the old code). Outlining both options gives the implementer maximum flexibility.

---

## 3. Caveats

1. **Package Manager Choice**: The current frontend contains a `package-lock.json` and no `yarn.lock`, `pnpm-lock.yaml`, or `bun.lockb`. Thus, `npm` is assumed and recommended. If the implementer decides to use another package manager, the install command syntaxes should be adapted.
2. **Node Version**: The scripts assume a Node.js runtime environment compatibile with Vite v6 (`node >= 18`).
3. **Sandbox Offline Constraints**: If the system running the commands lacks internet access, the package installations may require an active npm cache or proxy.

---

## 4. Conclusion

Milestone 2 can be successfully completed by following a four-stage process:
1. **Backup**: Save the custom `public/` directory (containing icons and backgrounds) to `/home/gojo/UE5/dueler/frontend_backup/`.
2. **Wipe & Scaffold**: Wipe the `frontend/` folder, run `npm create vite@latest . -- --template react-ts`, and restore the backup.
3. **Install**: Run the production and dev dependency commands, including `@types/uuid` and `@types/node`.
4. **Configure**: Update `vite.config.ts`, build configurations (PostCSS / Tailwind v3 or v4), and path mappings in the tsconfig file.

Actionable step-by-step instructions have been detailed in `analysis.md`.

---

## 5. Verification Method

To verify the setup:

1. **Build Test**:
   ```bash
   npm run build
   ```
   *Expect: Compilation succeeds with 0 TS errors and outputs a production-ready `/dist` folder.*

2. **Asset Checks**:
   Check if the backed-up assets exist in their proper paths:
   ```bash
   ls -la /home/gojo/UE5/dueler/frontend/public/pokemon-icons/manifest.json
   ls -la /home/gojo/UE5/dueler/frontend/public/arena_background.png
   ```
   *Expect: Both commands return details of the existing files without "No such file or directory" errors.*

3. **Vite Dev Server Proxy Check**:
   Run the dev server:
   ```bash
   npm run dev
   ```
   And run a curl request on the local port to verify proxy configuration resolves to the backend:
   ```bash
   curl -I http://localhost:5173/api/health
   ```
   *Expect: Returns a response from the backend port (e.g. 200 OK or 404/500 if backend is down, but not connection refused from Vite).*
