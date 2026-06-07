# Handoff Report - Milestone 2 Strategy

## 1. Observation

* **Directory Structure**: Evaluated directory `/home/gojo/UE5/dueler/frontend` and found crucial assets under `/home/gojo/UE5/dueler/frontend/public`.
* **Important Asset Location**: We ran `find_by_name` on `frontend/public` and observed `arena_background.png` and `pokemon-icons/` which contains a `types` subdirectory and `manifest.json`.
* **Asset Fetch Mechanism**: Read `/home/gojo/UE5/dueler/fetch-pokemon-icons.mjs` which writes to `frontend/public/pokemon-icons` using external fetch requests to:
  * `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`
  * `https://raw.githubusercontent.com/duiker101/pokemon-type-svg-icons/master/icons/${type}.svg`
* **Vite Proxy Settings**: Checked the original `/home/gojo/UE5/dueler/frontend/vite.config.ts` and noted `/api` targets `http://localhost:3001` (lines 16-19).
* **Package Specifications**: Verified current dependency and configuration references (e.g., Lucide-react, Zustand, Framer-motion, uuid, react-router-dom) in `/home/gojo/UE5/dueler/frontend/package.json` (lines 12-32).

---

## 2. Logic Chain

1. **Premise**: Wiping `/home/gojo/UE5/dueler/frontend` using a basic `rm -rf` would destroy the static assets stored under `/home/gojo/UE5/dueler/frontend/public` (observed in `Observation: Important Asset Location`).
2. **Inference**: Re-downloading these sprites relies on the internet via `fetch-pokemon-icons.mjs` (observed in `Observation: Asset Fetch Mechanism`). Since network conditions might be restricted or downloading hundreds of assets introduces unnecessary overhead and latency, these assets should not be deleted.
3. **Conclusion**: A safe strategy requires backing up `/home/gojo/UE5/dueler/frontend/public` before wiping, and restoring it afterward.
4. **Integration Inference**: To successfully set up the Tailwind CSS via PostCSS, a new `postcss.config.js` and `tailwind.config.js` must be generated, and the main stylesheet must incorporate `@tailwind` base, components, and utilities (or `@import "tailwindcss"` in Tailwind v4 format).
5. **Route/Proxy Inference**: The new configuration must proxy `/api` requests to backend port `3001` to maintain parity with the original server setup (observed in `Observation: Vite Proxy Settings`).

---

## 3. Caveats

* **Network limitations**: The explorer is running in `CODE_ONLY` network mode, which means we cannot run package installs or verify actual downloads. We assume the environment where the worker implements this will have internet access to run `npm install`.
* **Tailwind v4 vs v3**: Tailwind v4 can run without PostCSS (via `@tailwindcss/vite` plugin), but the prompt requested PostCSS/Autoprefixer. We detailed a PostCSS-based setup to satisfy this request.

---

## 4. Conclusion

The strategy is ready for implementation:
* Backup `frontend/public/` by renaming the parent folder from `frontend` to `frontend_old`.
* Reinitialize a clean React + TS + Vite setup.
* Restore `public/` folder contents from the backup directory.
* Configure Vite proxy for server integration, setup PostCSS with Tailwind CSS, and resolve required dependencies and types via standard `npm` calls.

---

## 5. Verification Method

To verify the strategy after execution:
1. **Directory Inspection**: Ensure the path `/home/gojo/UE5/dueler/frontend/public/pokemon-icons/manifest.json` and associated sprites exist.
2. **Dependency Verification**: Check `frontend/package.json` to verify packages `tailwindcss`, `postcss`, `autoprefixer`, `lucide-react`, `framer-motion`, `uuid`, `react-router-dom`, `zustand` and type packages are installed.
3. **Build Execution**: Run the build step inside the newly initialized directory:
   ```bash
   cd /home/gojo/UE5/dueler/frontend
   npm run build
   ```
   If the build runs without TypeScript errors and CSS imports compile correctly, the setup is verified.
