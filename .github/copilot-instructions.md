# CodeForge AI - Copilot Instructions

## Architecture Overview

CodeForge AI is a **hybrid monorepo** with two distinct layers that must remain loosely coupled:

- **Frontend (Next.js 14)**: Handles UI, auth, CRUD operations via Supabase
- **Agent Engine (Python FastAPI)**: Executes long-running AI tasks with LLM orchestration

Communication flows: `Next.js Server Actions → FastAPI → LLM Router → Supabase (realtime sync back to UI)`

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
# Right: Use instructor library or LangChain Pydantic parser
```

### 3. State Management Strategy

- **Server State**: Use React Query (TanStack Query) for project data, files, agent status
- **Local UI State**: Use Zustand for sidebar toggles, current file selection, UI preferences
- **Shareable State**: Store in URL params (e.g., `?file=src/app/page.tsx`) for deep linking

```typescript
// React Query for server data
const { data: files } = useQuery({
  queryKey: ['project-files', projectId],
  queryFn: () => fetchProjectFiles(projectId)
});

// Zustand for local UI state
const useEditorStore = create((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen }))
}));
```

### 4. Real-Time Agent Progress

Use Supabase Realtime to sync agent execution status without polling:

```typescript
// Frontend subscribes to project updates
supabase
  .channel(`project:${id}`)
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'projects' },
    (payload) => queryClient.invalidateQueries(['project', id])
  )
  .subscribe();

// Backend updates trigger UI refresh
await supabase.table('projects').update({
  'status': 'building',
  'requirements_spec': generated_spec
}).eq('id', project_id)
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
/agents                     # 4 agents: research, wireframe, code, pedagogy
/models                     # Pydantic schemas
/routers                    # FastAPI route handlers
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

**Row Level Security (RLS)**: All tables enforce user-based access. Never bypass RLS in application code.

## LLM Model Selection Strategy

Use the **Model Router** pattern to optimize cost vs. capability:

- **Research & QA**: GPT-4o or Claude 3.5 Sonnet (high reasoning)
- **Code Generation**: Gemini 1.5 Pro (large context ~1M tokens for full file awareness)
- **Routing/Classification**: Gemini Flash or GPT-4o-mini (cheap, fast)

```python
# Example routing logic
def get_optimal_model(task_type: str) -> str:
    if task_type in ["research", "qa"]:
        return "gpt-4o"
    elif task_type == "code":
        return "gemini-1.5-pro"
    else:
        return "gemini-flash"
```

## Critical Async Patterns

**Agent jobs are long-running** (30s - 5min). Use FastAPI `BackgroundTasks` or Redis queue:

```python
# POST /run-agent returns immediately with job_id
@app.post("/run-agent")
async def run_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    background_tasks.add_task(execute_agent_workflow, job_id, request.project_id)
    return {"job_id": job_id}
```

Frontend polls job status or (preferred) subscribes to Supabase Realtime updates.

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
- Code Agent: `text-green-400` / `border-green-400/20`
- Pedagogy Agent: `text-purple-400` / `border-purple-400/20`

## Key Files to Reference

- [`docs/Tech_Stack.md`](../docs/Tech_Stack.md) - Full architecture & LLM strategy
- [`docs/Backend_Schema.md`](../docs/Backend_Schema.md) - Database schema & Pydantic models
- [`docs/Frontend_Guidelines.md`](../docs/Frontend_Guidelines.md) - Component patterns & design system
- [`docs/Implementation_Details.md`](../docs/Implementation_Details.md) - 10-week build roadmap
- [`docs/App_Flow.md`](../docs/App_Flow.md) - User journeys & UI states

## Common Pitfalls to Avoid

1. **Don't use client components by default** - RSC first, `'use client'` only when necessary
2. **Don't trust raw LLM JSON** - Always enforce with Pydantic schemas
3. **Don't poll for agent status** - Use Supabase Realtime subscriptions
4. **Don't hardcode colors** - Use Tailwind semantic tokens (`bg-background`, `text-foreground`)
5. **Don't bypass RLS** - Always use authenticated Supabase client
6. **Don't create duplicate file paths** - Check unique constraint before inserting into `project_files`

## Development Workflow

```bash
# Frontend (Next.js)
npm run dev                 # Starts on localhost:3000
npm run build              # Production build
npm run lint               # ESLint + Prettier

# Backend (Python Agent Engine)
poetry install             # Install dependencies
uvicorn main:app --reload # Starts on localhost:8000
pytest                     # Run tests
```

**Deployment**:
- Frontend → Vercel (auto-deploy on push to `main`)
- Backend → Railway/Render (containerized FastAPI)
- Database → Supabase (managed PostgreSQL)
