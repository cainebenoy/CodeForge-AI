# CodeForge AI - Copilot Instructions

## Architecture Overview

CodeForge AI is a **hybrid monorepo** with two distinct layers that must remain loosely coupled:

- **Frontend (Next.js 14)**: Handles UI, auth, CRUD operations via Supabase
- **Agent Engine (Python FastAPI)**: Executes long-running AI tasks with LLM orchestration

Communication flows: `Next.js Server Actions → FastAPI → Celery/Redis → LLM Router → Supabase (realtime sync back to UI)`

## Critical Development Patterns

### 1. Server-First React Components

**Default to React Server Components (RSC).** Only use `'use client'` when you need:

- React hooks (`useState`, `useEffect`)
- Event handlers (`onClick`, `onChange`)
- Browser APIs or third-party client libs (Monaco Editor, Framer Motion)

```typescript
// ✅ Server Component - no directive needed
export default async function ProjectPage({ params }) {
  const project = await getProject(params.id); // Direct DB access
  return <ProjectViewer project={project} />;
}

// ✅ Client Component - explicit directive
'use client'
export function FileTree({ files }: FileTreeProps) {
  const [expanded, setExpanded] = useState(false);
  // ...
}
```

### 2. Pydantic-Enforced LLM Outputs

**ALL Agent responses must use strict Pydantic schemas.** This prevents hallucinated JSON structures.

```python
# Required pattern for Agent outputs
from pydantic import BaseModel, Field

class RequirementDoc(BaseModel):
    """Research Agent output - enforced schema"""
    features: list[str] = Field(description="Core MVP features")
    user_stories: list[str]
    tech_stack: list[str]

# Wrong: Free-form LLM JSON responses
# Right: Use LangChain PydanticOutputParser + resilient_llm_call()
```

### 3. State Management Strategy

- **Server State**: Use React Query (TanStack Query) for project data, files, agent status
- **Local UI State**: Use Zustand for sidebar toggles, current file selection, UI preferences
- **Shareable State**: Store in URL params (e.g., `?file=src/app/page.tsx`) for deep linking

```typescript
// React Query for server data
const { data: files } = useQuery({
  queryKey: ["project-files", projectId],
  queryFn: () => fetchProjectFiles(projectId),
});

// Zustand for local UI state
const useEditorStore = create((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
```

### 4. Real-Time Agent Progress

Dual-channel real-time updates:

1. **SSE Streaming** — `GET /v1/jobs/{job_id}/stream` for live progress events
2. **Supabase Realtime** — Subscribe to `agent_jobs` and `projects` table changes

```typescript
// Frontend subscribes to agent job updates
supabase
  .channel(`project:${id}`)
  .on(
    "postgres_changes",
    {
      event: "*",
      schema: "public",
      table: "agent_jobs",
      filter: `project_id=eq.${id}`,
    },
    (payload) => queryClient.invalidateQueries(["jobs", id]),
  )
  .on(
    "postgres_changes",
    { event: "UPDATE", schema: "public", table: "projects" },
    (payload) => queryClient.invalidateQueries(["project", id]),
  )
  .subscribe();
```

## Security Requirements (MANDATORY)

**These security practices must be followed in ALL code changes:**

1. **Rate Limiting**: Apply rate limiting on all public endpoints (IP + user-based). Use sensible defaults (60 requests/minute per IP and per authenticated user). Return graceful 429 responses with retry-after hint, without leaking internal details.

2. **Input Validation**: Implement strict input validation and sanitization on all user inputs using schema-based validation (JSON schema, zod, pydantic, Joi). Enforce type checks, length limits, format checks, and reject any unexpected or extra fields instead of silently ignoring them.

3. **SQL Injection Prevention**: Use parameterized queries or query builders for all database access; never build SQL strings via string concatenation. Validate and constrain all user-controlled identifiers and search parameters.

4. **Secret Management**: Handle API keys and secrets securely:
   - Remove all hard-coded secrets from source code
   - Load from environment variables or secret managers
   - Never expose secrets to client (browser, mobile, logs, error messages)
   - Implement regular key rotation
   - Use separate keys for dev, staging, and production

5. **Authentication**: Enforce authentication and session management on all non-public endpoints. No anonymous access to sensitive data or actions.

6. **Authorization**: Implement object- and function-level authorization checks for every operation that reads or modifies data. Never rely on client-side checks alone.

7. **Data Minimization**: Avoid excessive data exposure by returning only the minimum fields required for each response.

8. **HTTPS Enforcement**: Enforce HTTPS-only communication in all environments. Do not introduce or rely on plain HTTP endpoints except for local development. Never hard-code `http://` URLs for production calls.

9. **Error Handling**: Implement secure error handling and logging:
   - Do not expose stack traces, internal identifiers, or secrets in API responses
   - Log errors server-side with enough context to debug
   - Avoid logging sensitive personal data and secrets
   - Use structured logging where possible

10. **Dependency Management**: Keep dependencies updated and minimize attack surface:
    - Prefer maintained libraries
    - Remove unused packages
    - Do not add untrusted or low-reputation dependencies
    - Choose smallest, most focused, well-maintained options

11. **CSRF Protection**: Enable CSRF protection for state-changing operations in browser-based apps. Set secure, HttpOnly, SameSite cookies for sessions and auth tokens.

12. **Output Encoding**: Implement output encoding where user data is rendered into HTML, JavaScript, or SQL contexts to prevent injection attacks.

13. **Resource Limits**:
    - Limit payload sizes
    - Cap pagination (max page size)
    - Enforce timeouts on long-running operations and external API calls
    - Prevent resource exhaustion

14. **Data Privacy**: Avoid storing more user data than necessary ("collect less, store even less"):
    - Avoid adding new fields containing PII, credentials, payment data, or secrets unless absolutely required
    - If sensitive data must be stored, encrypt it at rest
    - Restrict access by role

15. **Attack Surface Reduction**: Remove unnecessary HTTP methods, headers revealing versions, and default accounts. Disable unnecessary database functionality.

16. **Security Documentation**: Add clear, concise comments around security-critical sections (auth, validation, crypto, permission checks, key handling) explaining **why** something is done, not just what it does.

17. **Backward Compatibility**: When modifying or adding code, do not break existing functionality or contracts. Preserve current API shapes and behaviors unless explicitly instructed. Update tests or add new ones to cover security-related logic.

## Directory Structure Conventions

```
/src/app                    # Next.js routes (App Router)
  /(auth)                   # Route group: auth pages
  /(dashboard)/builder      # Builder mode routes
/src/components
  /ui                       # Shadcn primitives (Button, Card)
  /features/builder         # Builder-specific compounds (SpecViewer, FileTree)
  /features/editor          # Monaco Editor wrappers
/src/lib
  /hooks                    # Custom React hooks
  /api                      # Supabase client, API wrappers
  /store                    # Zustand stores

# Python Agent Engine (separate service)
/app/agents                 # 6 agents: research, wireframe, code, qa, pedagogy, roadmap
/app/agents/core            # LLM router, memory, resilience (circuit breaker)
/app/agents/graph           # LangGraph workflows (state, nodes, workflows)
/app/schemas                # Pydantic v2 schemas (protocol.py)
/app/api/endpoints          # FastAPI route handlers
/app/middleware             # CSRF, rate limiter, request tracking
/app/services               # Database, validation, job queue, GitHub
/app/workers                # Celery task queue (celery_app, tasks)
```

## Database Schema Key Points

**Virtual File System**: Files stored as rows in `project_files` table with unique `(project_id, path)` constraint.

```sql
-- Prevents duplicate file paths
unique(project_id, path)
```

**Agent Outputs**: Stored as JSONB in `projects` table:

- `requirements_spec` (Research Agent)
- `architecture_spec` (Wireframe Agent)

**Agent Jobs**: Tracked in `agent_jobs` table with Supabase Realtime publication.

- Status: `queued` → `running` → `completed`/`failed`/`cancelled`
- Progress: 0-100%, result/error as JSONB

**Row Level Security (RLS)**: All tables enforce user-based access. Never bypass RLS in application code.

## LLM Model Selection Strategy

Use the **Model Router** pattern (`app/agents/core/llm.py`) to optimize cost vs. capability:

| Agent     | Model             | Provider  | Reason                                   |
| --------- | ----------------- | --------- | ---------------------------------------- |
| Research  | GPT-4o            | OpenAI    | High reasoning for requirements          |
| Wireframe | GPT-4o            | OpenAI    | Architecture design                      |
| Code      | Gemini 1.5 Pro    | Google    | 1M token context for full file awareness |
| QA        | GPT-4o            | OpenAI    | Code review reasoning                    |
| Pedagogy  | Claude 3.5 Sonnet | Anthropic | Socratic mentoring style                 |
| Roadmap   | Claude 3.5 Sonnet | Anthropic | Curriculum design                        |

```python
# Actual routing logic in llm.py
MODEL_ROUTER = {
    "research": ("gpt-4o", "openai"),
    "wireframe": ("gpt-4o", "openai"),
    "code": ("gemini-1.5-pro", "google"),
    "qa": ("gpt-4o", "openai"),
    "pedagogy": ("claude-3-5-sonnet", "anthropic"),
    "roadmap": ("claude-3-5-sonnet", "anthropic"),
}
```

## Critical Async Patterns

**Agent jobs are long-running** (30s - 5min). Use **Celery + Redis** persistent task queue:

```python
# POST /run-agent dispatches to Celery, returns immediately
@app.post("/v1/run-agent")
async def run_agent(request: AgentRequest):
    job_id = str(uuid4())
    execute_agent_task.delay(job_id, request.project_id, request.agent_type)
    return {"job_id": job_id}
```

- **Celery** dispatches to Redis broker, workers pick up tasks asynchronously
- **`task_acks_late`** ensures no task loss on worker crashes
- **BackgroundTasks** used as fallback if Celery unavailable
- Frontend gets updates via SSE (`/v1/jobs/{job_id}/stream`) or Supabase Realtime

## Component Styling Rules

Use **semantic Tailwind tokens** for theme adaptivity (light/dark mode):

```tsx
// ✅ Correct - adapts to theme
<div className="bg-background text-foreground border-border">

// ❌ Wrong - hardcoded colors break dark mode
<div className="bg-white text-black border-gray-200">
```

**Agent Signal Colors** (use for UI feedback):

- Research Agent: `text-amber-400` / `border-amber-400/20`
- Wireframe Agent: `text-blue-400` / `border-blue-400/20`
- Code Agent: `text-emerald-400` / `border-emerald-400/20`
- QA Agent: `text-teal-400` / `border-teal-400/20`
- Pedagogy Agent: `text-violet-400` / `border-violet-400/20`
- Roadmap Agent: `text-rose-400` / `border-rose-400/20`

## Key Files to Reference

- [`docs/Tech_Stack.md`](../docs/Tech_Stack.md) - Full architecture & LLM strategy
- [`docs/Backend_Schema.md`](../docs/Backend_Schema.md) - Database schema & Pydantic models
- [`docs/Frontend_Guidelines.md`](../docs/Frontend_Guidelines.md) - Component patterns & design system
- [`docs/Implementation_Details.md`](../docs/Implementation_Details.md) - Implementation progress & status
- [`docs/App_Flow.md`](../docs/App_Flow.md) - User journeys & UI states

## Common Pitfalls to Avoid

1. **Don't use client components by default** - RSC first, `'use client'` only when necessary
2. **Don't trust raw LLM JSON** - Always enforce with Pydantic schemas + PydanticOutputParser
3. **Don't poll for agent status** - Use SSE streaming or Supabase Realtime subscriptions
4. **Don't hardcode colors** - Use Tailwind semantic tokens (`bg-background`, `text-foreground`)
5. **Don't bypass RLS** - Always use authenticated Supabase client
6. **Don't create duplicate file paths** - Check unique constraint before inserting into `project_files`
7. **Don't call LLMs without resilience** - Always wrap with `resilient_llm_call()` (circuit breaker + retry)
8. **Don't skip input validation** - All endpoints use Pydantic v2 models with `extra='forbid'`

## Development Workflow

```bash
# Frontend (Next.js)
pnpm dev                    # Starts on localhost:3000
pnpm build                 # Production build
pnpm lint                  # ESLint + Prettier

# Backend (Python Agent Engine)
pip install -r requirements.txt  # Install dependencies
uvicorn app.main:app --reload    # Starts on localhost:8000
pytest                           # Run tests (297 tests)

# Celery Worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Docker Compose (all services)
docker-compose up --build  # Redis + FastAPI + Celery + Flower
```

**Deployment**:

- Frontend → Vercel (auto-deploy on push to `main`)
- Backend → Railway/Render (containerized FastAPI + Celery worker)
- Database → Supabase (managed PostgreSQL)
- Redis → Railway Redis or Upstash
