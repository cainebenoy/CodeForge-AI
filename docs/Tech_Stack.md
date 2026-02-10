# CodeForge AI — Technology Stack & Architecture

**Document Purpose:** This document defines the technical choices, infrastructure, and data flow for CodeForge AI. It is the single source of truth for architectural decisions and reflects the current implemented state of the system.

## 1. High-Level Architecture

The system follows a **Hybrid Monorepo** pattern:

- **Web/App:** A Next.js 14 application handling UI, User Auth, and simple logic.
- **Agent Engine:** A dedicated Python (FastAPI) service handling long-running AI tasks, reasoning, and code generation.
- **Task Queue:** Celery workers with Redis broker for persistent background job execution.
- **Database:** Supabase (PostgreSQL) with pgvector for RAG, Realtime for live updates.

```
┌─────────────────────────────────────────────────────────────┐
│  User Browser                                               │
└──────────────────┬────────────────────────────┬─────────────┘
                   │                            │
                   ▼                            ▼
┌──────────────────────────────┐   ┌────────────────────────┐
│  Next.js 14 (Vercel)         │   │  SSE Stream             │
│  • Server Components (RSC)   │   │  /v1/jobs/{id}/stream   │
│  • Tailwind + Shadcn/UI      │   └────────────┬───────────┘
│  • Monaco Editor             │                │
└──────────────┬───────────────┘                │
               │                                │
               ▼                                │
┌──────────────────────────────┐                │
│  FastAPI Agent Engine        │◄───────────────┘
│  • 6 AI Agents               │
│  • LangGraph orchestration   │
│  • Circuit breaker + retry   │
│  • CSRF / Rate limiting      │
└──────┬───────────┬───────────┘
       │           │
       ▼           ▼
┌────────────┐  ┌────────────────────────────────────┐
│  Redis     │  │  Supabase (PostgreSQL)              │
│  • Celery  │  │  • Auth (JWT, GitHub OAuth)         │
│    broker  │  │  • RLS (user isolation)             │
│  • Job     │  │  • pgvector (RAG embeddings)        │
│    store   │  │  • Realtime (agent_jobs, projects)  │
└─────┬──────┘  └────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────┐
│  Celery Workers                    │
│  • execute_single_agent_task       │
│  • execute_pipeline_task           │
│  • Cooperative cancellation        │
│  • Crash recovery (acks_late)      │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  LLM Providers (Model Router)     │
│  • OpenAI GPT-4o                   │
│  • Google Gemini 1.5 Pro           │
│  • Anthropic Claude 3.5 Sonnet     │
└────────────────────────────────────┘
```

## 2. Frontend Stack (The "Shell")

**Focus:** Performance, interactivity, and collaborative feel.

### Core Framework

- **Next.js 14+ (App Router):** Chosen for Server Components and Vercel integration.
- **Language:** TypeScript (Strict mode).
- **State Management:**
  - **Server State:** `React Query` (TanStack Query) for fetching project data, agent status.
  - **Local State:** `Zustand` for managing UI states (sidebar toggles, active file, current agent).
  - **URL State:** Search params for shareable context (`?file=src/app/page.tsx`).

### UI & Styling

- **Tailwind CSS:** For rapid styling with semantic tokens (`bg-background`, `text-foreground`).
- **Shadcn/UI:** For accessible, copy-pasteable component primitives (Dialogs, Cards, Forms).
- **Framer Motion:** For smooth transitions between Agent steps (e.g., "Thinking" animations).
- **Lucide React:** Icon set.

### Specialized Components

- **Code Editor:** `@monaco-editor/react`. The VS Code editor component for Builder Mode code review and Student Mode sandbox.
- **Diagrams:** `React Flow` (or `Mermaid.js` rendered via client). Used by the Wireframe Agent to visualize component trees.
- **Markdown Rendering:** `react-markdown` + `remark-gfm` for rendering Spec Documents and Chat responses.

## 3. Backend & AI Engine (The "Brain")

**Focus:** Deterministic output, structured data generation, and resilient execution.

### Service A: Next.js API (Serverless)

- **Role:** CRUD operations, User Auth, Supabase Realtime subscriptions.
- **Communication:** Interacts directly with Supabase via `@supabase/ssr`.

### Service B: Agent Engine (Python / FastAPI)

- **Role:** The heavy lifting. Runs the **6 Agents** (Research, Wireframe, Code, QA, Pedagogy, Roadmap).
- **Why Python?** Superior ecosystem for AI orchestration (LangChain, LangGraph, Pydantic).
- **Core Libraries:**
  - **FastAPI 0.115+:** High-performance async API with ASGI middleware.
  - **LangChain (LCEL):** Chains with `prompt | llm | PydanticOutputParser` pattern for structured output.
  - **LangGraph:** StateGraph with conditional edges for multi-agent pipelines (e.g., Code → QA retry loop).
  - **Pydantic v2:** **CRITICAL.** Strict mode (`extra="forbid"`) forces LLMs to output validated JSON schemas.
  - **Celery:** Persistent background task execution with Redis broker and crash recovery.

### LLM Strategy (The "Model Router")

Implemented in `backend/app/agents/core/llm.py`. Each agent type routes to the optimal LLM:

| Agent Type | Model             | Provider  | Rationale                                  |
| ---------- | ----------------- | --------- | ------------------------------------------ |
| Research   | GPT-4o            | OpenAI    | High reasoning for requirements analysis   |
| QA         | GPT-4o            | OpenAI    | Thorough code review & edge case detection |
| Wireframe  | GPT-4o            | OpenAI    | Structured architecture understanding      |
| Code       | Gemini 1.5 Pro    | Google    | 1M token context for full file awareness   |
| Pedagogy   | Claude 3.5 Sonnet | Anthropic | Best at Socratic explanation               |
| Roadmap    | Claude 3.5 Sonnet | Anthropic | Curriculum design & learning paths         |

**Resilience:** All LLM calls are wrapped with `resilient_llm_call()` which provides:

- Per-provider circuit breaker (CLOSED → OPEN → HALF_OPEN states)
- Exponential backoff with jitter (max 3 retries)
- Transient error detection (429, 500, 502, 503, timeouts)

## 4. Task Queue & Background Processing

### Celery + Redis

- **Broker:** Redis (configurable via `CELERY_BROKER_URL`, defaults to `REDIS_URL`)
- **Tasks:** `execute_single_agent_task`, `execute_pipeline_task`
- **Crash Recovery:** `task_acks_late=True` ensures tasks are re-queued if a worker dies mid-execution
- **Time Limits:** Soft/hard limits from `AGENT_TIMEOUT` setting (default 300s)
- **Cooperative Cancellation:** Tasks check job status in the store; cancelled jobs stop gracefully
- **Fallback:** When Celery/Redis is unavailable, falls back to FastAPI `BackgroundTasks`
- **Monitoring:** Flower dashboard on port 5555 (`docker compose --profile monitoring up`)

### Job Lifecycle

```
queued → running → completed | failed | cancelled | waiting_for_input
```

- Jobs tracked in-memory (`InMemoryJobStore` with thread-safe locking) and synced to `agent_jobs` Supabase table
- Paginated listing with `{items, total, has_more}` response format
- SSE streaming at `/v1/jobs/{job_id}/stream` for real-time progress events

## 5. Database & Storage (The "Memory")

**Provider:** **Supabase** (Managed PostgreSQL).

### Core Data

- **PostgreSQL:** Relational data (Users, Projects, Files, Sessions).
- **Supabase Auth:** Handles JWTs, Social Login (GitHub), and Row Level Security (RLS).
- **Supabase Realtime:** Live updates on `projects` and `agent_jobs` tables via Postgres changes.

### Tables

| Table                | Purpose                                              |
| -------------------- | ---------------------------------------------------- |
| `profiles`           | User accounts (extends `auth.users`)                 |
| `projects`           | Projects with Agent outputs as JSONB                 |
| `project_files`      | Virtual file system with unique `(project_id, path)` |
| `learning_roadmaps`  | Student mode curriculum                              |
| `daily_sessions`     | Learning session transcripts + duration tracking     |
| `agent_jobs`         | Persistent job tracking with Realtime publication    |
| `pattern_embeddings` | RAG vector store (pgvector, 1536 dims)               |

### Project Status Values

```
'planning' | 'in-progress' | 'building' | 'completed' | 'archived'
```

Enforced by CHECK constraint (migration `0006`).

### AI Memory (RAG)

- **pgvector:** Vector embeddings for "Long Term Memory" (IVFFlat index, 100 lists).
- **`match_patterns` RPC:** Semantic similarity search for previous successful patterns.
- _Usage:_ If a user builds a "SaaS", the Research and Code agents are primed with similar successful architectural patterns.

## 6. Student Mode Execution Environment (Sandboxing)

**Challenge:** How do we let students run code securely in the browser?

### Approach A: Client-Side Execution (MVP)

- **JavaScript/React:** Use the browser's own JS engine.
  - _Tool:_ `Sandpack` (by CodeSandbox). Spins up an in-browser bundler.
  - _Pros:_ Zero backend cost, fast.
  - _Cons:_ Cannot run backend code (Python/Node servers).

### Approach B: Server-Side Execution (Phase 2)

- **Remote Containers:** Spin up a micro-VM for the student.
  - _Tool:_ **Daytona** or **E2B** (Code Interpreter SDK).
  - _Pros:_ Can run full-stack apps (Node + Postgres).
  - _Cons:_ Cost per minute.

**Decision for MVP:** Use **Sandpack** for frontend tutorials. For backend concepts, use "Code Review Only" mode initially.

## 7. Integrations & DevOps

### Version Control & Export

- **GitHub API (Git Data API):** Create repos and push generated code.
  - Batch commit: blobs → tree → commit → ref for initial push.
  - Per-request token handling (never stored server-side).
  - Repo name and file path validation.

### Infrastructure

- **Hosting:**
  - **Frontend:** Vercel (Auto-deploy from Git).
  - **Python Engine:** Railway/Render (containerized FastAPI with Dockerfile).
  - **Database:** Supabase (managed PostgreSQL with pgvector).
- **Task Queue:** **Celery** with **Redis** broker.
  - _Flow:_ Next.js calls `POST /v1/run-agent` → FastAPI dispatches Celery task → Worker executes agent → Result stored in Supabase → Realtime notification to client.
- **Monitoring:** Flower for Celery queue inspection (port 5555).

### Docker Compose

The `docker-compose.yml` includes:

- `backend` — FastAPI app (port 8000)
- `redis` — Redis 7 Alpine (port 6379)
- `celery_worker` — Celery worker pool
- `flower` — Queue monitoring dashboard (port 5555, monitoring profile)

## 8. Security Architecture

### 1. Authentication & Authorization

- JWT Bearer tokens verified against Supabase (`SUPABASE_JWT_SECRET`)
- Row Level Security (RLS) on all database tables — users can only access their own data
- CSRF double-submit cookie protection with Bearer token bypass for API clients

### 2. Rate Limiting

- Token bucket algorithm (60 req/min default, per-IP + per-user)
- Graceful 429 responses with `Retry-After` headers

### 3. Input Validation

- Pydantic v2 strict mode with `extra="forbid"` on all schemas
- Custom validators (path traversal, UUID format, email, string sanitization)
- File size limits, context size limits, pagination caps

### 4. Error Sanitization

- Internal error details logged server-side only
- Client responses contain generic messages (no stack traces, no internal identifiers)
- `ExternalServiceError` stores raw message in `_internal_message` — never exposed to clients

### 5. Prompt Injection Mitigation

- Strict System Prompts with persona enforcement
- Pydantic schema enforcement prevents free-form LLM outputs

### 6. Infinite Loop Protection

- LangGraph recursion limit (configurable `MAX_AGENT_ITERATIONS`, default 3)
- Agent timeout enforcement (configurable `AGENT_TIMEOUT`, default 300s)
- Circuit breaker opens after repeated LLM provider failures

### 7. Secret Management

- All secrets loaded from environment variables (`Pydantic Settings`)
- Startup validation ensures required keys are present (skipped in test env)
- API keys never exposed in logs, errors, or client responses
- `repr=False` on sensitive settings fields
