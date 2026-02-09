# CodeForge AI — Frontend Engineering Guidelines

**Document Purpose:** To establish strict coding standards, directory structures, and UI patterns for the CodeForge frontend (Next.js 14+). This ensures consistency, maintainability, and high performance for the MVP and beyond.

## 1. Core Principles

1. **Server-First Mental Model:** Default to React Server Components (RSC). Only use `'use client'` when interactivity (hooks, event listeners) is strictly required.
2. **Zero-Layout Shift:** The UI must be stable. Agent streaming responses must push content down smoothly without jumping.
3. **Url as the Source of Truth:** For shareable states (e.g., Project ID, current file selection), store state in the URL search params, not just local state.
4. **Composition over Inheritance:** Build complex UIs by composing small, single-responsibility components (Shadcn/UI pattern).

## 2. Directory Structure (Next.js App Router)

We follow a **Feature-First** architecture combined with atomic design principles for shared components.

```
/src
  /app                   # Next.js App Router
    /(auth)              # Route Group: Login/Signup layouts
    /(dashboard)         # Route Group: Main App layout (Sidebar + Nav)
      /builder           # Builder Mode Routes
        /[projectId]
          /page.tsx      # Main Builder Canvas
          /layout.tsx    # Project Context Provider
      /student           # Student Mode Routes
    /api                 # Next.js Serverless Functions
  /components
    /ui                  # Shadcn Primitive Components (Button, Input)
    /shared              # Reusable compounds (UserAvatar, Logo)
    /features
      /builder           # Builder-specific components (SpecViewer, FileTree)
      /student           # Student-specific components (SandpackWrapper, QuizCard)
      /editor            # Monaco Editor wrappers
      /chat              # Agent Chat Interface
  /lib
    /hooks               # Custom React Hooks
    /utils.ts            # CN helper and formatters
    /api                 # API Client (Axios/Fetch wrappers)
    /store               # Zustand Stores
    /types               # TypeScript Interfaces
  /styles                # Global CSS
```

## 3. Component Strategy

### 3.1 Server vs. Client Components

- **Server Components:**
    - Fetching Project Data from Supabase.
    - Rendering static markdown content (Spec Docs).
    - Layout shells (Sidebars, Navbars).
- **Client Components:**
    - The Code Editor (Monaco).
    - Chat Input forms.
    - The "Choice Framework" Card selection (requires interactivity).
    - Any component using `useState`, `useEffect`, or `useStore`.

### 3.2 Component Naming Convention

- **PascalCase** for filenames and components: `ProjectCard.tsx`.
- **kebab-case** for utility files: `date-formatter.ts`.
- **Props Interface:** Must be exported and named `${ComponentName}Props`.

```
// Good Example
interface ProjectCardProps {
  id: string;
  title: string;
}

export function ProjectCard({ id, title }: ProjectCardProps) {
  return <div>{title}</div>;
}
```

## 4. Design System: "Deep Tech Minimal"

**Aesthetic Goal:** A high-precision, cockpit-like interface similar to Vercel, Linear, or Raycast. It should feel like a tool for professionals, not a toy.

### 4.1 Adaptive Theme Strategy (Light & Dark)

We use **Semantic CSS Variables** (via Shadcn/Tailwind) to support two distinct vibes while maintaining the "Engineering" aesthetic.

- **Dark Mode ("Cockpit"):** High contrast, Obsidian backgrounds (`zinc-950`), subtle borders. Best for long coding sessions.
- **Light Mode ("Laboratory"):** Clean, Paper-like (`zinc-50`), crisp borders. Best for documentation and bright environments.

**Semantic Token Mapping:**

| Token | Light Mode (Value) | Dark Mode (Value) | Usage |
| --- | --- | --- | --- |
| `bg-background` | `white` | `zinc-950` | Main canvas background. |
| `bg-muted` | `zinc-100` | `zinc-900` | Secondary backgrounds, sidebars, card surfaces. |
| `border-border` | `zinc-200` | `zinc-800` | Structural dividers. |
| `text-foreground` | `zinc-900` | `zinc-50` | Primary text. |
| `text-muted-foreground` | `zinc-500` | `zinc-400` | Secondary text, metadata. |

**Signal Colors (Agents):***Adjust luminance for readability on light backgrounds.*

- **Research Agent (Amber):**
    - Dark: `text-amber-400` / `border-amber-400/20`
    - Light: `text-amber-600` / `border-amber-600/20`
- **Code Agent (Emerald):**
    - Dark: `text-emerald-400` / `border-emerald-400/20`
    - Light: `text-emerald-600` / `border-emerald-600/20`
- **Pedagogy Agent (Violet):**
    - Dark: `text-violet-400` / `border-violet-400/20`
    - Light: `text-violet-600` / `border-violet-600/20`

### 4.2 Visual Hierarchy (Borders > Shadows)

- **Definition:** Use **1px borders** to define hierarchy.
    - *Dark:* `border-white/10` (Subtle)
    - *Light:* `border-zinc-200` (Crisp)
- **Active States:** Use **"Glow Borders"** (Dark) or **"Ring Focus"** (Light) instead of size changes.
- **Separators:** Use `divide-border` for lists to automatically adapt.

### 4.3 The "Glass" Layer (AI Overlays)

We use Glassmorphism *sparingly* to distinguish the "AI Layer" from the "Application Layer."

- **Usage:** Only for Floating Chat, Toasts, or the "Choice Framework" Cards.
- **Class:** `bg-background/80 backdrop-blur-md border border-border`
- **Effect:** This makes the AI feel like a "HUD" (Heads Up Display) overlaid on top of your work, regardless of theme.

### 4.4 Typography as UI

- **Headings:** `Inter` or `Geist Sans`. Tight tracking (`tracking-tight`) for a technical feel.
- **Badges/Status/Metadata:** **ALWAYS** use Monospace (`JetBrains Mono`).
    - *Why?* It reinforces the engineering aesthetic. A status badge saying `[BUILDING]` looks more professional in mono.

## 5. State Management Patterns

### 5.1 Global Client State (Zustand)

Use Zustand for UI state that persists across components but doesn't need to be in the URL.

**Store: `useBuilderStore`**

- `activeFile`: string | null (Path of currently open file in editor)
- `isSidebarOpen`: boolean
- `activeAgent`: 'research' | 'wireframe' | 'code' | 'qa'
- `generatedFiles`: Record<string, string> (The virtual file system)

### 5.2 Server State (TanStack Query)

Use React Query for data that comes from the backend.

- `useProject(id)`: Fetches project metadata.
- `useProjectFiles(id)`: Fetches the file tree.
- **Invalidation:** When the Agent finishes generating code, invalidate `['project-files', id]` to refresh the file tree.

### 5.3 URL State

For shareable context, use `searchParams`.

- `/builder/[id]?file=src/app/page.tsx` -> Opens specific file.
- `/student/[id]?module=2&step=4` -> Opens specific tutorial step.

## 6. Critical Feature Implementation Guidelines

### 6.1 The Code Editor (Monaco)

- **Wrapper:** Create a `CodeEditor` wrapper around `@monaco-editor/react`.
- **Dynamic Theming:**
    - Listen to `useTheme()` hook.
    - If **Dark**: Load custom "CodeForge Dark" theme (based on VS Code Dark).
    - If **Light**: Load custom "CodeForge Light" theme (based on GitHub Light).
- **Read-Only Mode:** During generation, lock the editor to "Read Only" so users don't conflict with the AI stream.
- **Diff View:** When the user requests a change ("Refactor this"), use `MonacoDiffEditor` to show Before/After.

### 6.2 Agent Streaming UI

- **The "Typewriter" Effect:** Do not just dump text.
- **Implementation:**
    - The backend streams chunks.
    - Frontend appends chunks to a buffer string.
    - `react-markdown` renders the buffer.
- **Auto-Scroll:** Implementing a "Stick to Bottom" hook for the chat window that disables if the user manually scrolls up.

### 6.3 The Student Sandbox (Sandpack)

- **Configuration:**
    - Use `SandpackProvider` with a custom `template="react"`.
    - **Theming:** Pass the `theme` prop to Sandpack (supports `auto` to match system preference).
    - **Files:** Inject the `generatedFiles` from the Zustand store into the Sandpack `files` prop.
- **Security:** Sandpack runs in an iframe on a separate domain (codesandbox.io), keeping our main app secure.

## 7. Performance & Optimization

### 7.1 Font Loading

- Use `next/font/google`.
- **Primary:** `Inter` or `Geist Sans` (UI).
- **Monospace:** `JetBrains Mono` or `Geist Mono` (Code & Data).

### 7.2 Lazy Loading

- Lazy load heavy client components:
    - `const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })`
    - `const Sandpack = dynamic(() => import('@codesandbox/sandpack-react'), { ssr: false })`

### 7.3 Image Optimization

- Use `next/image` for all raster assets.
- For User Avatars, use Shadcn `Avatar` component with a fallback to initials.

## 8. Accessibility (a11y)

- **Keyboard Nav:** Ensure the Code Editor trap doesn't prevent `Esc` to exit.
- **Forms:** All inputs must have associated `<Label>` components.
- **Contrast:** Ensure syntax highlighting in the editor meets WCAG AA standards.
- **Screen Readers:** Use `aria-live="polite"` for the Agent chat responses so screen readers announce new text chunks.