# Milestone 2 Analysis: Wipe and Initialize Vite App

This report analyzes the current `/home/gojo/UE5/dueler/frontend` directory structure and recommends a detailed, safe strategy to wipe and initialize a clean React + Vite + TypeScript application with Tailwind CSS (PostCSS), Zustand, and Router configurations.

---

## 1. Directory Structure and Asset Assessment

The current `frontend` directory contains both active configuration files, source code components, and a large set of downloaded Pokémon asset images.

### Key Files in `frontend` Root
* **`package.json`**: Defines dependencies (currently includes `@tailwindcss/vite`, `@types/react`, `@types/react-dom`, `@types/uuid`, etc.).
* **`vite.config.ts`**: Currently configured with Vite `@tailwindcss/vite` plugin (Tailwind v4 alpha/beta style), React plugin, `@` path alias, and an `/api` proxy targeting `http://localhost:3001`.
* **`tsconfig.json`**: Simple TypeScript configuration defining compilation rules and path mappings.
* **`index.html`**: Contains header link preconnects for Google Fonts (`Unbounded`, `Outfit`, `Share Tech Mono`, `Rajdhani`) and links `/src/main.tsx`.

### Critical Assets in `frontend/public`
These assets must be preserved because they were fetched externally and cannot be easily recreated offline or under restricted network conditions:
* **`frontend/public/arena_background.png`**: The custom battlefield background image.
* **`frontend/public/pokemon-icons/`**: Directory containing:
  * Over 250 standard and shiny Pokémon sprite PNGs (e.g., `1.png`, `shiny-1.png`).
  * `manifest.json`: An index mapping Pokémon IDs to names and types.
  * `types/`: A subfolder containing type icons as SVG files (e.g., `normal.svg`, `fire.svg`).

---

## 2. Safe Wiping Strategy

Directly running `rm -rf frontend/` is dangerous and will delete local copies of sprite and background assets. We propose a "Move and Restore" strategy.

1. **Rename the directory** to create a backup. This is instantaneous, avoids disk-copy overhead, and ensures a zero-loss fallback.
   ```bash
   mv /home/gojo/UE5/dueler/frontend /home/gojo/UE5/dueler/frontend_old
   ```
2. **Initialize the new app** as detailed in Section 3.
3. **Restore the assets** by copying them from the backup folder back to the new structure:
   ```bash
   rm -rf /home/gojo/UE5/dueler/frontend/public
   cp -r /home/gojo/UE5/dueler/frontend_old/public /home/gojo/UE5/dueler/frontend/public
   ```
4. **Delete the backup** only after verification:
   ```bash
   rm -rf /home/gojo/UE5/dueler/frontend_old
   ```

---

## 3. Initialization Steps

To initialize a clean React + Vite + TypeScript application in `frontend/`:

1. Navigate to the project root directory:
   ```bash
   cd /home/gojo/UE5/dueler
   ```
2. Run the Vite creator using `npm`:
   ```bash
   npm create vite@latest frontend -- --template react-ts
   ```
3. Move into the frontend directory:
   ```bash
   cd frontend
   ```
4. Run npm install to resolve default dependencies (React, TypeScript, Vite, etc.):
   ```bash
   npm install
   ```

---

## 4. Package Installation Commands

Install the requested libraries and their associated TypeScript declaration types.

### Production Dependencies
* `lucide-react` (icons)
* `framer-motion` (premium animation system)
* `uuid` (unique identifier generation)
* `react-router-dom` (routing)
* `zustand` (state management)

### Development Dependencies
* `tailwindcss` (Tailwind CSS)
* `postcss` (PostCSS processor)
* `autoprefixer` (browser vendor prefixing)
* `@types/node` (node typings for `path` in `vite.config.ts`)
* `@types/uuid` (typings for `uuid` library)

### Combined Command
```bash
npm install lucide-react framer-motion uuid react-router-dom zustand
npm install -D tailwindcss postcss autoprefixer @types/node @types/uuid
```
*(Note: `@types/react` and `@types/react-dom` are installed automatically by the Vite `react-ts` template).*

---

## 5. Configuration Setup

### PostCSS Configuration
Create `postcss.config.js` in the `frontend/` root:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### Tailwind CSS Configuration
Create `tailwind.config.js` in the `frontend/` root. This registers content paths and custom fonts matching the app design system:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "system-ui", "-apple-system", "sans-serif"],
        display: ["Unbounded", "sans-serif"],
        mono: ["Share Tech Mono", "monospace"],
        rajdhani: ["Rajdhani", "sans-serif"],
      },
    },
  },
  plugins: [],
};
```

### Vite Configuration
Replace the contents of `vite.config.ts` to include standard React, path aliases, and the development proxy settings:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
```

### CSS Setup
Replace `src/index.css` content with the base Tailwind imports:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```
If using Tailwind CSS v4, use:
```css
@import "tailwindcss";
```

### Path Mapping in tsconfig.json
Ensure the `tsconfig.json` (or `tsconfig.app.json` if Vite v6 structure is used) allows mapping of `@/*` to `./src/*`:
```json
"compilerOptions": {
  "baseUrl": ".",
  "paths": {
    "@/*": ["./src/*"]
  }
}
```
