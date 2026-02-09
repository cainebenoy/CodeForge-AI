# CodeForge AI — Master Implementation Plan

**Document Purpose:** A step-by-step execution roadmap to take CodeForge from zero to Public Beta in 10 weeks. It prioritizes the "Builder Mode" core first, then layers "Student Mode" on top.

**Total Timeline:** 10 Weeks
**Team Assumption:** 1 Full Stack Engineer (You) + AI Agents

## Phase 1: The Foundation (Weeks 1-2)

**Goal:** A working "Skeleton" where a user can log in, create a project, and see a dashboard. The Python Engine is connected to the Next.js App.

### Week 1: Infrastructure & Auth

- **Day 1: Repo Setup**
    - Initialize Next.js 14 App Router project (`create-next-app`).
    - Setup Tailwind CSS + Shadcn/UI.
    - Configure ESLint and Prettier.
    - Commit initial structure.
- **Day 2: Supabase Init**
    - Create Supabase Project.
    - Run SQL scripts from `CodeForge_Backend_Schema.md` (Tables + RLS).
    - Setup Supabase Auth (GitHub + Email).
    - Create `supabase-client.ts` helper in Next.js.
- **Day 3: Frontend Shell**
    - Build `/(auth)/login` page.
    - Build `/(dashboard)/page.tsx` (Project List).
    - Build `/(dashboard)/[projectId]/layout.tsx` (Sidebar + Header).
- **Day 4-5: Python Engine Skeleton**
    - Initialize FastAPI project in a separate directory (or repo).
    - Setup Poetry/Pipenv.
    - Create a simple `/health` endpoint.
    - Deploy Python Engine to **Railway/Render**.
    - Deploy Next.js to **Vercel**.
    - **Verify:** Next.js can call Python `/health` and get a 200 OK.

### Week 2: Agent Orchestration Core

- **Day 1: LangChain Setup**
    - Install `langchain`, `pydantic`, `instructor`.
    - Configure API Keys (OpenAI, Gemini).
- **Day 2: Database Connection**
    - Install `supabase-py` in Python service.
    - Create a function to fetch `project_id` context from Supabase.
- **Day 3: The Job Queue**
    - Setup a simple async pattern (using FastAPI `BackgroundTasks` or Redis/BullMQ).
    - Endpoint: `POST /run-agent` (Accepts `project_id`, returns `job_id`).
- **Day 4-5: Realtime Feedback Loop**
    - Implement Supabase Realtime in Next.js.
    - **Test:** Next.js triggers a job -> Python updates a row in `projects` table -> Next.js UI updates automatically without reload.

## Phase 2: The "Builder Mode" Logic (Weeks 3-6)

**Goal:** A user can input an idea and get a full Spec + File Structure.

### Week 3: The Research Agent

- **Day 1: Prompt Engineering**
    - Write System Prompt for "Product Manager Persona."
    - Define `RequirementsDoc` Pydantic model.
- **Day 2: Chat Interface**
    - Build the Chat UI in Next.js (Streaming text).
    - Implement the "Clarification Loop" (Agent asks user questions).
- **Day 3-4: Document Rendering**
    - Build `SpecViewer` component (Markdown renderer).
    - Store the generated JSON in `projects.requirements_spec`.
- **Day 5: Integration Test**
    - Input: "Uber for Cats" -> Output: Full JSON Spec displayed in UI.

### Week 4: The Wireframe Agent & Visualization

- **Day 1: Architecture Logic**
    - Write System Prompt for "System Architect."
    - Define `WireframeSpec` Pydantic model.
- **Day 2: The Tree View**
    - Build `FileTree` component (using `lucide-react` icons).
    - Visualize the component hierarchy from the JSON output.
- **Day 3-5: Iteration UI**
    - Allow user to "Reject" or "Regenerate" parts of the spec.
    - Update the `projects` table state accordingly.

### Week 5: Code Generation (The Heavy Lift)

- **Day 1: The Code Agent**
    - Switch to **Gemini 1.5 Pro** or **DeepSeek Coder** (Large Context).
    - Prompt Strategy: "You are a Senior React Dev. Write file X based on Spec Y."
- **Day 2: Virtual File System**
    - Implement logic to write rows to `project_files` table.
    - Ensure strict path uniqueness (`src/app/page.tsx`).
- **Day 3-5: Streaming Code**
    - **Critical:** Implement streaming response for code generation.
    - UI: Show file being typed out line-by-line in the Monaco Editor.

### Week 6: The Editor & Refinement

- **Day 1-2: Monaco Integration**
    - Implement `@monaco-editor/react`.
    - Connect it to `useProjectFiles` hook (TanStack Query).
- **Day 3: "Refactor" Feature**
    - Select code -> Right Click -> "Refactor with AI".
    - Send selection to Python -> Return diff -> Apply change.
- **Day 4-5: Polish Builder Mode**
    - Fix UI glitches.
    - Improve loading states ("Thinking...").

## Phase 3: Student Mode & Pedagogy (Weeks 7-9)

**Goal:** Implement the "Learning Layer" and "Choice Framework."

### Week 7: Curriculum Generation

- **Day 1: Assessment UI**
    - Build the "Skill Quiz" component.
    - Store `skill_level` in `profiles`.
- **Day 2: Roadmap Logic**
    - Create `RoadmapGenerator` agent.
    - Input: `RequirementsDoc` + `skill_level`.
    - Output: `LearningRoadmap` JSON (Weeks/Modules).
- **Day 3-5: Kanban UI**
    - Build the Roadmap view (Locked/Unlocked modules).
    - Implement "Start Module" action.

### Week 8: The "Choice Framework" (Killer Feature)

- **Day 1: Trigger Logic**
    - Define "Decision Nodes" in the roadmap (e.g., "Database Selection").
    - Pedagogy Agent prompt to generate 3 options (Fast/Good/Educational).
- **Day 2: The Card UI**
    - Build the 3-Card overlay component.
    - Make it interactive (Selection updates `learning_roadmaps` state).
- **Day 3-5: Context Adaptation**
    - **Hard Part:** Ensure subsequent AI tutorial steps respect the user's choice.
    - *Test:* Choose "Firebase" -> Ensure next step explains `firebase.init()`, NOT `prisma.connect()`.

### Week 9: Sandboxing & Interactive Session

- **Day 1-3: Sandpack Integration**
    - Implement `Sandpack` for the code view in Student Mode.
    - Inject `project_files` into the Sandpack virtual file system.
- **Day 4-5: Mentor Chat**
    - Implement the "Socratic" chat mode (Agent instructed NOT to give code answers).
    - "Check My Code" button (QA Agent linter).

## Phase 4: Launch Prep (Week 10)

**Goal:** Production Readiness.

### Week 10: Polish & Export

- **Day 1: GitHub Export**
    - Implement OAuth flow for GitHub.
    - Create `POST /api/export-to-github` (Create repo, push files).
- **Day 2: Security Audit**
    - Verify RLS policies.
    - Rate limit the API endpoints (Upstash Redis).
- **Day 3: Landing Page**
    - Update landing page with demo video.
    - Add "Waitlist" or Stripe "Subscribe" button.
- **Day 4: Analytics**
    - Install PostHog or Mixpanel.
    - Track: `agent_run_success`, `project_created`, `module_completed`.
- **Day 5: LAUNCH**
    - Post on Product Hunt / Twitter / LinkedIn.

## Checklist for Success

1. **Don't Over-Engineer the Editor:** Monaco is complex. Stick to basic syntax highlighting and read-only modes initially. Don't try to build a full VS Code in the browser (use Sandpack for that).
2. **Cache the Agents:** AI is slow and expensive. Use `pgvector` to find similar previous projects and reuse their architectural specs if possible.
3. **Strict JSON:** If the Python Agent fails to output valid JSON, the UI *will* break. Use `instructor` library retry logic aggressively.