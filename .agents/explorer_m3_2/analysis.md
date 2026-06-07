# Milestone 3 Strategy: Recreate Components

## 1. Strategy Overview

Milestone 3 focuses on recreting a series of high-quality UI components, layout structures, and animated feedback elements. The target environment is a modern client-side React 19 monorepo running on **Vite**, **Tailwind CSS v3.4.x**, and **React Router v7 (react-router-dom)**. 

Since many of the specification sheets are designed with Next.js conventions, this document establishes a definitive strategy for:
1. **Component Placement**: Standardizing directory structure and target file paths.
2. **Missing Dependencies**: Auditing and installing essential shadcn/Radix packages and utility libraries.
3. **Routing Adaptations**: Transitioning Next.js file-based routes and navigation components to `react-router-dom` counterparts.
4. **Custom Styling and Animations**: Mapping HSL theme variables, keyframes, cybernetic grid hover effects, and modern CSS utilities to Tailwind and raw stylesheets.

---

## 2. Component Catalog

Below is the complete catalog of components defined in the `info/` directory, mapped to their target file paths, sub-components, internal hooks, and custom style dependencies.

| Component Name | Spec File | Target File Path | Sub-Components / Hooks / Utilities | Package Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **Gooey Filter** | `background.md` | `frontend/src/components/ui/gooey-filter.tsx` | - | None |
| **Pixel Trail** | `background.md` | `frontend/src/components/ui/pixel-trail.tsx` | `PixelDot` (Memoized), `useDimensions` (hook), `cn` (utility) | `framer-motion`, `uuid` |
| **Screen Size Tracker** | `background.md` | `frontend/src/hooks/use-screen-size.ts` | `ComparableScreenSize` wrapper class | None |
| **Debounced Dimensions** | `background.md` | `frontend/src/hooks/use-debounced-dimensions.ts` | `useDimensions` | None |
| **Neon Button** | `buttons.md` | `frontend/src/components/ui/neon-button.tsx` | `buttonVariants`, `cn` | `class-variance-authority` |
| **Card Stack** | `card.md` | `frontend/src/components/ui/card-stack.tsx` | `DefaultFanCard`, `wrapIndex`, `signedOffset`, `cn` | `framer-motion`, `lucide-react` |
| **Dropdown Component** | `dropdown.md` | `frontend/src/components/ui/dropdown-01.tsx` | Custom options lists, inline grid background | `framer-motion`, `lucide-react` |
| **Avatar Primitive** | `empty_state.md`, `sidebar.md` | `frontend/src/components/ui/avatar.tsx` | `Avatar`, `AvatarImage`, `AvatarFallback`, `cn` | `@radix-ui/react-avatar` |
| **Empty State Layout** | `empty_state.md` | `frontend/src/components/ui/empty.tsx` | `Empty`, `EmptyHeader`, `EmptyTitle`, `EmptyDescription`, `EmptyContent`, `EmptyMedia`, `emptyMediaVariants`, `cn` | `class-variance-authority` |
| **Button Primitive** | `empty_state.md`, `tooltip.md` | `frontend/src/components/ui/button.tsx` | `Button`, `buttonVariants` (standard shadcn button), `cn` | `@radix-ui/react-slot`, `class-variance-authority` |
| **Not Found Page** | `empty_state.md` | `frontend/src/components/ui/not-found-page.tsx` | Assembled using `Empty` layout primitives, Radix `Avatar`, and shadcn `Button` | Standard React components |
| **Cybernetic Bento Grid** | `features.md` | `frontend/src/components/ui/cybernetic-bento-grid.tsx` | `BentoItem` (mouse tracker component) | None (Requires custom CSS) |
| **Menu Toggle Icon** | `menu_button.md` | `frontend/src/components/ui/menu-toggle-icon.tsx` | `cn` (uses transition-all on svg lines) | None |
| **Floating Header** | `navbar.md` | `frontend/src/components/ui/navbar.tsx` | `Header`, `menuItems`, dynamic scroll height listener | `lucide-react` |
| **Liquid Glass Buttons** | `navbar.md` | `frontend/src/components/ui/liquid-glass-button.tsx` | `Button` (Slot-based), `LiquidButton` (distorted blur), `MetalButton` (shine-effect metallic), `GlassFilter`, `ShineEffect`, `cn` | `@radix-ui/react-slot`, `class-variance-authority` |
| **Container Scroll** | `scroll_animation.md` | `frontend/src/components/ui/container-scroll-animation.tsx` | `ContainerScroll`, `Header`, `Card`, scroll transforms | `framer-motion` |
| **Collapsible Sidebar** | `sidebar.md` | `frontend/src/components/ui/sidebar.tsx` | `SessionNavBar`, animations, react-router integrations | `framer-motion`, `lucide-react` |
| **Scroll Area Primitive** | `sidebar.md` | `frontend/src/components/ui/scroll-area.tsx` | `ScrollArea`, `ScrollBar`, `cn` | `@radix-ui/react-scroll-area` |
| **Separator Primitive** | `sidebar.md` | `frontend/src/components/ui/separator.tsx` | `Separator`, `cn` | `@radix-ui/react-separator` |
| **Dropdown Menu Primitive** | `sidebar.md` | `frontend/src/components/ui/dropdown-menu.tsx` | Dropdown primitives (`Trigger`, `Content`, `Item`, `Separator`, `Portal`) | `@radix-ui/react-dropdown-menu`, `lucide-react` |
| **Skeleton Primitive** | `sidebar.md` | `frontend/src/components/ui/skeleton.tsx` | `Skeleton`, `cn` | None |
| **Badge Primitive** | `sidebar.md` | `frontend/src/components/ui/badge.tsx` | `Badge`, `badgeVariants`, `cn` | `class-variance-authority` |
| **Slider Primitive** | `slider.md` | `frontend/src/components/ui/slider.tsx` | `Slider`, `renderThumb`, tooltip overlays, `cn` | `@radix-ui/react-slider` |
| **Slider with Input hook** | `slider.md` | `frontend/src/hooks/use-slider-with-input.ts` | `useSliderWithInput` input field syncing hook | None |
| **Input Primitive** | `slider.md` | `frontend/src/components/ui/input.tsx` | `Input`, `cn` | None |
| **Label Primitive** | `slider.md` | `frontend/src/components/ui/label.tsx` | `Label`, `cn` | None |
| **Morphing Square Spinner** | `spinner.md` | `frontend/src/components/ui/morphing-square.tsx` | `MorphingSquare`, infinite animations, `cn` | `class-variance-authority`, `framer-motion` |
| **Tooltip Primitive** | `slider.md`, `tooltip.md` | `frontend/src/components/ui/tooltip.tsx` | `Tooltip`, `TooltipContent`, `TooltipProvider`, `TooltipTrigger`, `cn` | `@radix-ui/react-tooltip` |

---

## 3. Package Dependencies

The current `frontend/package.json` specifies several core packages (e.g. `framer-motion`, `react-router-dom`, `lucide-react`, `uuid`, `zustand`), but is missing the standard Tailwind merging helpers and Radix UI primitives. 

To support the component implementations in Milestone 3, the following packages must be added:

### Core Dependencies to Install:
```bash
npm install clsx tailwind-merge @radix-ui/react-slot @radix-ui/react-avatar @radix-ui/react-scroll-area @radix-ui/react-separator @radix-ui/react-dropdown-menu @radix-ui/react-slider @radix-ui/react-tooltip class-variance-authority
```

### Dev Dependencies to Install:
```bash
npm install -D tailwindcss-animate
```

### Rationale:
1. **`clsx` & `tailwind-merge`**: Used to build the standard `cn` class concatenation utility (`src/lib/utils.ts`). Essential for combining static and dynamic Tailwind classes without style override conflicts.
2. **`class-variance-authority`**: Powers variant-based styling configs (e.g., button colors/sizes, empty state layouts, badge types).
3. **`@radix-ui/react-*`**: Provides unstyled, accessible keyboard-navigable primitives (such as slot, avatar, scroll-area, separator, dropdown, slider, and tooltip).
4. **`tailwindcss-animate`**: Installs utility classes matching Radix open/close transitions (e.g. `animate-in`, `fade-in-0`, `zoom-in-95`).

---

## 4. Navigation & Routing Adaptation (Next.js to React Router)

Several specifications (`sidebar.md`, `navbar.md`, `card.md`, `scroll_animation.md`) are coded for Next.js features like file routing and optimized image tags. The following outlines how they must be refactored for a client-side Vite + `react-router-dom` configuration.

### 4.1. Link Component (`<Link>`)
* **Next.js**: `import Link from 'next/link'` -> `<Link href="/dashboard">`
* **React Router**: `import { Link } from 'react-router-dom'` -> `<Link to="/dashboard">`
* *Refactoring Action*: Replace all `href` props on `<Link>` components with the `to` prop.

### 4.2. Pathname Tracking (`usePathname`)
* **Next.js**: `import { usePathname } from "next/navigation"; const pathname = usePathname();`
* **React Router**: 
  ```typescript
  import { useLocation } from "react-router-dom";
  // Inside Component:
  const location = useLocation();
  const pathname = location.pathname;
  ```
* *Refactoring Action*: Refactor the active nav link checkers in `sidebar.tsx` (`pathname?.includes("dashboard")`, etc.) to use `useLocation().pathname`.

### 4.3. Image Components (`Image`)
* **Next.js**: `import Image from "next/image"` -> `<Image src={...} width={...} height={...} />`
* **React Router**: Replace with standard HTML `<img>` elements.
  ```tsx
  <img src={src} className={className} alt={alt} draggable={false} />
  ```
* *Refactoring Action*: Replace the Next.js `Image` imports and tags in the scroll animation demo (`HeroScrollDemo`) and sidebar.

### 4.4. Router Configuration Layout (`App.tsx`)
In Vite, routing must be declared programmatically. Wrap the application shell in a standard `<BrowserRouter>` structure using nested layouts to keep the sidebar persistent while views swap inside the `<Outlet />`.

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { SessionNavBar } from "./components/ui/sidebar";
import { Header } from "./components/ui/navbar";

// Placeholder Views for Sidebar Paths
const DashboardView = () => <div className="p-8"><h1>Dashboard View</h1></div>;
const ReportsView = () => <div className="p-8"><h1>Reports View</h1></div>;
const ChatView = () => <div className="p-8"><h1>Chat View (BETA)</h1></div>;
const DealsView = () => <div className="p-8"><h1>Deals View</h1></div>;
const AccountsView = () => <div className="p-8"><h1>Accounts View</h1></div>;
const CompetitorsView = () => <div className="p-8"><h1>Competitors View</h1></div>;
const KnowledgeBaseView = () => <div className="p-8"><h1>Knowledge Base</h1></div>;
const FeedbackView = () => <div className="p-8"><h1>Feedback View</h1></div>;
const DocumentReviewView = () => <div className="p-8"><h1>Document Review</h1></div>;
const ProfileView = () => <div className="p-8"><h1>Profile Settings</h1></div>;

// Layout containing Sidebar and main view container
function AppLayout() {
  return (
    <div className="flex h-screen w-screen flex-row overflow-hidden bg-background text-foreground">
      <SessionNavBar />
      <main className="flex h-screen grow flex-col overflow-auto pl-[3.05rem] transition-all duration-200">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* App Shell Route */}
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardView />} />
          <Route path="dashboard" element={<DashboardView />} />
          <Route path="reports" element={<ReportsView />} />
          <Route path="chat" element={<ChatView />} />
          <Route path="deals" element={<DealsView />} />
          <Route path="accounts" element={<AccountsView />} />
          <Route path="competitors" element={<CompetitorsView />} />
          <Route path="library/knowledge" element={<KnowledgeBaseView />} />
          <Route path="feedback" element={<FeedbackView />} />
          <Route path="review" element={<DocumentReviewView />} />
          <Route path="settings/profile" element={<ProfileView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 5. Tailwind CSS & Styling Strategy

To support the visual designs (cybernetic grids, glass effects, neon glows, and custom layout variables) without modifying core layout classes, styling configurations must be written to two files: `frontend/tailwind.config.js` and `frontend/src/index.css`.

### 5.1. Custom Tailwind Config Additions (`frontend/tailwind.config.js`)
Merge shadcn variables, theme radius variables, custom keyframes for accordions/menus, and register `tailwindcss-animate` inside the export block:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        unbounded: ["Unbounded", "sans-serif"],
        outfit: ["Outfit", "sans-serif"],
        shareTechMono: ["'Share Tech Mono'", "monospace"],
        rajdhani: ["Rajdhani", "sans-serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [
    require("tailwindcss-animate")
  ],
};
```

*Note on Tailwind CSS Version differences*: The liquid glass button spec references new Tailwind v4 classes (`bg-linear-to-t`, `inset-shadow-2xs`). In Tailwind v3, these should be rewritten to:
* `bg-linear-to-t` -> `bg-gradient-to-t`
* `dark:inset-shadow-2xs` -> simulated with standard box shadows or custom theme additions: `shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]`.

---

### 5.2. Core CSS Utilities & Variables (`frontend/src/index.css`)
Append the following styling variables and specific cybernetic utilities to the global CSS stylesheet:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 10% 3.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
  }
}

/* Custom CSS utilities for Milestone 3 components */

/* Cybernetic Bento Grid styles (features.md) */
.main-container {
  min-height: 100vh;
  width: 100%;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem 1rem;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}

.bento-item {
  position: relative;
  border-radius: 1rem;
  background-color: #171717; /* neutral-900 */
  border: 1px solid #262626; /* neutral-800 */
  padding: 1.5rem;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.bento-item:hover {
  border-color: #404040; /* neutral-700 */
}

/* Radial Glow Cursor Follow Effect */
.bento-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    600px circle at var(--mouse-x, 0px) var(--mouse-y, 0px),
    rgba(255, 255, 255, 0.06),
    transparent 40%
  );
  z-index: 1;
  pointer-events: none;
}

/* Scroll area scrollbar hiding for clean layouts */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
```

---

## 6. Recommended Execution Sequence

To implement this component recreation strategy smoothly, execute the workspace changes in the following order:

1. **Step 1: Install Package Dependencies**: Run `npm install` for the Radix primitives, `class-variance-authority`, merging helpers, and `tailwindcss-animate`.
2. **Step 2: Add Global Classes and Settings**:
   - Save the `cn` helper to `frontend/src/lib/utils.ts`.
   - Update `frontend/tailwind.config.js` with theme variables and keyframes.
   - Update `frontend/src/index.css` with CSS custom variables and cybernetic bento grid rules.
3. **Step 3: Create Core Shared UI Components**:
   - Implement `button.tsx`, `avatar.tsx`, `separator.tsx`, `scroll-area.tsx`, `dropdown-menu.tsx`, and `tooltip.tsx`.
4. **Step 4: Create Complex Component Shells**:
   - Implement custom components (`neon-button.tsx`, `slider.tsx`, `card-stack.tsx`, `gooey-filter.tsx`, `pixel-trail.tsx`, `morphing-square.tsx`, `menu-toggle-icon.tsx`, `cybernetic-bento-grid.tsx`, `empty.tsx`, `liquid-glass-button.tsx`).
5. **Step 5: Create layout and Shell Views**:
   - Implement `sidebar.tsx` and `navbar.tsx`.
   - Implement `not-found-page.tsx`.
6. **Step 6: Routing Wireframe & Demos**:
   - Update `frontend/src/App.tsx` with layout routes, sidebar links, and mount points for components.
