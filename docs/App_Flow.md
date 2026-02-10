# CodeForge AI — Detailed App Flow & User Journey

**Document Purpose:** This file maps the specific UI states, user actions, and system responses for the CodeForge platform. It serves as the blueprint for frontend development (Next.js) and Agent orchestration. Backend flows are fully implemented; frontend UI is in progress.

## 1. Global Onboarding Flow

**Goal:** Route users to the correct mode ("Build" vs. "Learn") immediately.

### 1.1 Landing Page

- **Hero Section:** "Your AI Engineering Team" (Headline).
- **Primary CTA:** "Start Building" (Direct to Builder Mode).
- **Secondary CTA:** "Start Learning" (Direct to Student Mode).

### 1.2 Authentication (Supabase Auth)

- **Provider:** GitHub (preferred for devs) or Email/Password.
- **Post-Auth Redirect:**
  - _New User:_ Onboarding Questionnaire.
  - _Returning User:_ Dashboard.

### 1.3 New User Onboarding

- **Question:** "What is your primary goal?"
  - [Option A] "I have an idea I need to ship ASAP." -> **Sets `default_mode = 'builder'`**
  - [Option B] "I want to learn how to build professional apps." -> **Sets `default_mode = 'student'`**

## 2. Builder Mode Workflow (The "Production" Path)

**Goal:** From idea to GitHub repository with minimal friction.

### Step 1: The Brief (Input)

- **UI State:** Clean, distraction-free form (similar to Typeform or Perplexity).
- **Input Fields:**
  1. **Project Name:** (e.g., "DogWalker CRM")
  2. **One-Liner:** (e.g., "A CRM for dog walkers to manage clients and schedules.")
  3. **Target Audience:** (e.g., "Freelance dog walkers.")
  4. **Tech Stack Preferences:** (Tags: Next.js, Supabase, Tailwind).
- **Action:** User clicks "Hire Team" (Submit).
- **System Response:** Creates project in Supabase → Calls `POST /v1/run-agent` with `agent_type: "research"` → Transition to "War Room" loading state.

### Step 2: Research & Spec Generation

- **Agent:** Research Agent (GPT-4o).
- **UI State:** Split View.
  - _Left Panel:_ Chat Interface (Agent asking clarifying questions).
  - _Right Panel:_ Live Document (`requirements.md`) rendering in real-time.
- **Backend Flow:**
  1. Job created with status `queued` → dispatched to Celery worker
  2. Agent detects ambiguity → sets job status to `waiting_for_input` with `ClarificationQuestion` list
  3. Frontend receives update via SSE stream or Supabase Realtime on `agent_jobs` table
  4. User responds via `POST /v1/jobs/{job_id}/respond` with answers
  5. Agent resumes with clarifications → generates final `RequirementsDoc`
  6. Result stored in `projects.requirements_spec` (JSONB)
- **Interaction Loop:**
  1. Agent: "Should the CRM handle payments, or just scheduling?"
  2. User: "Just scheduling for MVP."
  3. System: Updates spec to remove Stripe integration.
- **Exit Condition:** User clicks "Approve Spec."

### Step 3: Wireframe & Architecture

- **Agent:** Wireframe Agent (GPT-4o).
- **UI State:** Tree Visualization (React Flow or simple nested list).
- **Visuals:**
  - **Site Map:** `Home -> Dashboard -> Settings`.
  - **Component Tree:** `Dashboard -> [StatCard, ClientTable, Calendar]`.
  - **Schema Preview:** Shows table relationships (e.g., `User` 1:N `Dogs`).
- **Backend Flow:** Agent reads `requirements_spec` from Supabase → generates `WireframeSpec` → stores in `projects.architecture_spec`
- **Action:** User clicks "Confirm Architecture."

### Step 4: The Build (Code Generation)

- **Agent:** Code Agent (Gemini 1.5 Pro — 1M token context).
- **UI State:** IDE Simulation (Monaco Editor).
  - _Sidebar:_ File tree populating dynamically.
  - _Editor:_ Shows code generation progress.
  - _Terminal:_ Mock terminal showing build status.
- **Backend Flow:** Agent reads `requirements_spec` + `architecture_spec` → generates code files → stores in `project_files` table with unique `(project_id, path)` constraint
- **User Control:** User can track progress via SSE stream (progress percentage updates).

### Step 5: QA & Export

- **Agent:** QA Agent (GPT-4o).
- **Backend Flow:**
  - QA Agent reviews generated code → produces `QAResult` with severity-scored issues
  - If QA fails (`passed: false`): Code→QA retry loop triggers (up to `MAX_AGENT_ITERATIONS`)
  - If QA passes: Pipeline completes with status `completed`
- **UI State:** Dashboard View.
- **Outputs:**
  - **QA Report:** List of issues with severity (`critical`, `warning`, `info`) and suggestions
  - **Repo Link:** "Export to GitHub" → `POST /v1/projects/{id}/export/github` (creates repo, pushes all files via Git Data API batch commit)
  - **Refactor:** User can select code and request AI refactoring via `POST /v1/projects/{id}/files/refactor`

### Full Pipeline (Alternative Flow)

Instead of running agents individually, users can trigger the full pipeline via `POST /v1/run-pipeline`:

```
Research → Wireframe → Code → QA (with code→QA retry loop)
```

- Single job ID tracks the entire pipeline
- Progress updates at each stage via SSE or Realtime
- LangGraph state machine manages transitions and conditional edges

## 3. Student Mode Workflow (The "Learning" Path)

**Goal:** Teach engineering decision-making through a guided project.

### Step 1: Skill Assessment

- **UI:** Chat-based Adaptive Quiz.
- **Flow:**
  1. System: "Have you used React before?" (Yes/No).
  2. System: "If you wanted to pass data from a parent to a child, what would you use?" (Multiple Choice: Props, Context, Redux).
- **Output:** Sets `skill_level` (`beginner`/`intermediate`/`advanced`) in `profiles` table.

### Step 2: Project Selection

- **UI:** Card Grid.
- **Content:**
  - _Beginner:_ "To-Do List" (Focus: State).
  - _Intermediate:_ "Trello Clone" (Focus: Drag-n-Drop, DB).
  - _Advanced:_ "Real-time Chat" (Focus: Sockets, Auth).
- **Selection:** User picks project → creates project with `mode: 'student'`.

### Step 3: Roadmap Generation

- **Agent:** Roadmap Agent (Claude 3.5 Sonnet).
- **Backend Flow:**
  - `POST /v1/student/roadmap` with project context + skill level
  - Agent generates `LearningRoadmap` with modules, steps, estimated hours, prerequisites
  - Stored in `learning_roadmaps` table
- **UI:** Kanban Board (Modules).
  - [Unlocked] Module 1: Project Setup & Tailwind.
  - [Locked] Module 2: Database Schema (Supabase).
  - [Locked] Module 3: Drag and Drop Logic.

### Step 4: The Daily Session (Core Interaction)

- **UI:** Split Screen IDE.
  - _Left:_ Mentor Chat (Pedagogy Agent).
  - _Right:_ Code Editor (Sandboxed).
- **Backend Flow:** `POST /v1/student/ask` with student code + question → Pedagogy Agent responds with Socratic guidance
- **Session Tracking:** Transcripts stored in `daily_sessions` table with concepts covered + duration
- **Progress:** `GET /v1/student/progress/{project_id}` returns module completion percentages

### Step 5: The "Choice Framework" Moment (Key Feature)

- **Trigger:** User reaches a major architectural decision node (e.g., "How do we store the cards?").
- **Backend Flow:** `POST /v1/student/choice-framework` → Pedagogy Agent generates 3 options with pros/cons/difficulty
- **UI State:** **Modal Overlay / Focus Mode**.
- **The Cards:** Three distinct options appear.
  - **Option A (Beginner):** "Local Storage."
  - **Option B (Intermediate):** "PostgreSQL (Supabase)."
  - **Option C (Advanced):** "Custom JSON File Server."
- **Selection:** User clicks option → `POST /v1/student/choice-framework/select` → saves choice
- **Outcome:** The Pedagogy Agent generates subsequent tutorial steps dynamically based on the selection.

### Step 6: Review & Certification

- **Trigger:** Project Completion.
- **UI:** "Code Review" Report.
- **Content:**
  - "You used `useEffect` correctly 90% of the time."
  - "Security Warning: You committed API keys (simulated)."
- **Reward:** "Project Badge" added to User Profile.

## 4. Job Lifecycle & Progress Tracking

### Job Status Flow

```
queued → running → completed
                 → failed (with error message)
                 → cancelled (via POST /v1/jobs/{id}/cancel)
                 → waiting_for_input (clarification needed)
```

### Real-Time Progress Updates (Dual Channel)

**Channel 1 — SSE (Server-Sent Events):**

```
GET /v1/jobs/{job_id}/stream

event: progress
data: {"progress": 45.0, "status": "running"}

event: complete
data: {"result": {...}, "status": "completed"}

event: waiting
data: {"questions": [...], "status": "waiting_for_input"}
```

**Channel 2 — Supabase Realtime:**

```typescript
supabase
  .channel(`agent-jobs:${projectId}`)
  .on(
    "postgres_changes",
    {
      event: "UPDATE",
      schema: "public",
      table: "agent_jobs",
      filter: `project_id=eq.${projectId}`,
    },
    (payload) => handleJobUpdate(payload.new),
  )
  .subscribe();
```

Frontend can subscribe to either or both channels.

## 5. Shared UI Elements & States

### 5.1 The "Thinking" State

- **Context:** Used in both modes when Agents are processing.
- **Visual:** Not a spinner. A text log showing "Thought Steps."
  - _Example:_ "Reading requirements... Checking Supabase docs... Generating schema..."
- **Purpose:** Builds trust and explains _how_ the AI is working.
- **Backend:** Progress events streamed via SSE with percentage updates.

### 5.2 The "Revision" Request

- **Context:** User wants to change something.
- **Interaction:**
  - User highlights text (Builder Mode) or code (Student Mode).
  - Context menu appears: "Refine with AI."
  - Input box: "Make this more accessible."
- **Backend:** `POST /v1/projects/{id}/files/refactor` with file path, instructions, and optionally `apply: true` to auto-save.

## 6. Edge Cases & Error Handling

- **LLM Provider Failure:**
  - _Backend:_ Circuit breaker detects transient errors (429, 500, 502, 503, timeouts). `resilient_llm_call()` retries with exponential backoff (max 3 retries). If provider is down, circuit opens and fails fast for 60s.
  - _UI:_ "Brain Freeze. Retrying..." (progress bar shows retry attempt).
  - _Fallback:_ Unknown agent types fall back to GPT-4o.
- **Ambiguous Requirements:**
  - _Backend:_ Research Agent sets job status to `waiting_for_input` with clarification questions.
  - _UI:_ Chat interface shows questions. User responds → agent resumes.
- **Code Syntax Errors:**
  - _Backend:_ QA Agent reviews code. If `passed: false`, the code→QA retry loop re-generates code (up to the iteration limit).
- **Job Cancellation:**
  - _Backend:_ `POST /v1/jobs/{job_id}/cancel` revokes Celery task and sets status to `cancelled`.
  - _UI:_ "Cancelled" badge on job card.
- **Worker Crash:**
  - _Backend:_ Celery `task_acks_late=True` ensures the task is re-queued to another worker automatically.
