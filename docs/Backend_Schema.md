# CodeForge AI — Backend Schema & Data Models

**Document Purpose:** To define the database structure (PostgreSQL/Supabase), Row Level Security (RLS) policies, the strict Pydantic schemas used for Agent inter-communication, and the complete API contracts.

## 1. Database Schema (Supabase PostgreSQL)

We use a relational model for core entities (Users, Projects) and a document model (JSONB) for flexible Agent outputs.

### Migrations

Applied in order via `supabase db push`:

| #   | File                                 | Purpose                                          |
| --- | ------------------------------------ | ------------------------------------------------ |
| 1   | `0001_init_schema.sql`               | Core tables, indexes, `updated_at` triggers      |
| 2   | `0002_rls_policies.sql`              | Row Level Security on all tables                 |
| 3   | `0003_vector_embeddings.sql`         | pgvector extension + `pattern_embeddings` table  |
| 4   | `0004_match_patterns_rpc.sql`        | `match_patterns()` RPC for RAG similarity search |
| 5   | `0005_add_duration_minutes.sql`      | Add `duration_minutes` to `daily_sessions`       |
| 6   | `0006_project_status_constraint.sql` | CHECK constraint on `projects.status`            |
| 7   | `0007_agent_jobs_realtime.sql`       | `agent_jobs` table, RLS, Realtime publication    |

### 1.1 Core Entities

### `profiles`

Extends the default `auth.users` table.

```sql
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  username text unique,
  full_name text,
  avatar_url text,
  skill_level text check (skill_level in ('beginner', 'intermediate', 'advanced')),
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);
```

### `projects`

The central hub for both Builder and Student modes.

```sql
create table public.projects (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  description text,
  mode text check (mode in ('builder', 'student')) not null,
  status text default 'planning' not null,

  -- Agent outputs (JSONB for flexibility)
  requirements_spec jsonb,    -- Output from Research Agent
  architecture_spec jsonb,    -- Output from Wireframe Agent

  -- Metadata
  tech_stack text[],
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,

  -- Status constraint (migration 0006)
  constraint projects_status_check
    check (status in ('planning', 'in-progress', 'building', 'completed', 'archived'))
);
```

**Status values:** `'planning'` | `'in-progress'` | `'building'` | `'completed'` | `'archived'`

### `project_files`

The virtual file system. Storing files individually allows specific file fetching for the IDE.

```sql
create table public.project_files (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  path text not null,         -- e.g., "src/app/page.tsx"
  content text,               -- The actual code
  language text,              -- 'typescript', 'python', 'css', etc.
  version int default 1 not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,

  unique(project_id, path)    -- Prevent duplicate paths per project
);
```

### `agent_jobs`

Persistent job tracking with Realtime publication for live frontend updates.

```sql
create table public.agent_jobs (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  agent_type text not null,
  status text default 'queued' not null
    check (status in ('queued', 'running', 'completed', 'failed', 'waiting_for_input', 'cancelled')),
  progress float default 0.0 not null,
  result jsonb,
  error text,
  celery_task_id text,        -- For Celery task revocation
  created_at timestamptz default now() not null,
  started_at timestamptz,     -- Auto-set when status → 'running'
  completed_at timestamptz    -- Auto-set when status → terminal state
);
```

**Job status values:** `'queued'` | `'running'` | `'completed'` | `'failed'` | `'waiting_for_input'` | `'cancelled'`

A database trigger (`handle_agent_job_updated_at`) automatically sets `started_at` when status transitions to `'running'` and `completed_at` when status transitions to a terminal state.

### 1.2 Student Mode Entities

### `learning_roadmaps`

Stores the generated curriculum for a specific project.

```sql
create table public.learning_roadmaps (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  modules jsonb not null,          -- Array of { title, steps, is_locked }
  current_step_index int default 0 not null,
  created_at timestamptz default now() not null
);
```

### `daily_sessions`

Tracks the "Socratic" chat history for learning.

```sql
create table public.daily_sessions (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  transcript jsonb,                -- Array of { role: 'user'|'mentor', content: string }
  concepts_covered text[],
  duration_minutes int default 0 not null,  -- Added in migration 0005
  created_at timestamptz default now() not null
);
```

### 1.3 RAG Entities

### `pattern_embeddings`

Vector store for architectural pattern matching (RAG).

```sql
create table public.pattern_embeddings (
  id uuid default uuid_generate_v4() primary key,
  project_type text not null,       -- 'saas', 'ecommerce', 'social', etc.
  embedding vector(1536),           -- OpenAI embedding dimension
  metadata jsonb,                   -- Pattern details
  success_score float,              -- 0-1, how well this pattern worked
  created_at timestamptz default now() not null
);
```

**Index:** IVFFlat with 100 lists for cosine similarity search.

**RPC Function:** `match_patterns(query_embedding, match_count, filter_type)` performs vector similarity search using the `<=>` cosine distance operator.

## 2. Row Level Security (RLS) Policies

**All tables have RLS enabled.** Policies enforce user-scoped access.

| Table                | Policy                      | Rule                                       |
| -------------------- | --------------------------- | ------------------------------------------ |
| `profiles`           | SELECT                      | Public (all authenticated users can view)  |
| `profiles`           | INSERT                      | `auth.uid() = id`                          |
| `profiles`           | UPDATE                      | `auth.uid() = id`                          |
| `projects`           | SELECT/INSERT/UPDATE/DELETE | `auth.uid() = user_id`                     |
| `project_files`      | ALL                         | Project owned by `auth.uid()` (join check) |
| `learning_roadmaps`  | ALL                         | Project owned by `auth.uid()` (join check) |
| `daily_sessions`     | ALL                         | Project owned by `auth.uid()` (join check) |
| `agent_jobs`         | SELECT                      | `auth.uid() = user_id`                     |
| `pattern_embeddings` | SELECT                      | `auth.role() = 'authenticated'`            |

**Note:** `agent_jobs` has no INSERT/UPDATE/DELETE policies for authenticated users — all writes are done by the backend using the service role key.

## 3. Supabase Realtime

Both `projects` and `agent_jobs` tables are added to the `supabase_realtime` publication:

```sql
alter publication supabase_realtime add table public.projects;
alter publication supabase_realtime add table public.agent_jobs;
```

Frontend subscribes to `postgres_changes` events for live status updates:

```typescript
supabase
  .channel(`project:${id}`)
  .on(
    "postgres_changes",
    {
      event: "UPDATE",
      schema: "public",
      table: "agent_jobs",
      filter: `project_id=eq.${id}`,
    },
    (payload) => handleJobUpdate(payload.new),
  )
  .subscribe();
```

## 4. Agent Interface Schemas (Pydantic)

All schemas are defined in `backend/app/schemas/protocol.py` (717 lines). They use Pydantic v2 with `ConfigDict(extra="forbid")` to reject unexpected fields.

### 4.1 Core Enums

```python
class AgentType(str, Enum):
    RESEARCH = "research"
    WIREFRAME = "wireframe"
    CODE = "code"
    QA = "qa"
    PEDAGOGY = "pedagogy"
    ROADMAP = "roadmap"

class JobStatusType(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_INPUT = "waiting_for_input"
    CANCELLED = "cancelled"

class PriorityLevel(str, Enum):
    MUST_HAVE = "must-have"
    SHOULD_HAVE = "should-have"
    NICE_TO_HAVE = "nice-to-have"
```

### 4.2 Research Agent Output

Target Field: `projects.requirements_spec`

```python
class UserPersona(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(..., min_length=1, max_length=100)
    goal: str = Field(..., min_length=1, max_length=200)
    pain_point: str = Field(..., min_length=1, max_length=200)

class Feature(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    priority: PriorityLevel  # 'must-have', 'should-have', 'nice-to-have'

class RequirementsDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_name: str = Field(..., min_length=1, max_length=100)
    elevator_pitch: str = Field(..., min_length=20, max_length=500)
    target_audience: List[UserPersona]
    core_features: List[Feature]
    recommended_stack: List[str]
    technical_constraints: Optional[str] = None
```

### 4.3 Wireframe Agent Output

Target Field: `projects.architecture_spec`

```python
class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=100)
    props: List[str]
    children: List[str]

class PageRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(..., min_length=1, max_length=200)
    description: str
    components: List[Component]

class WireframeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    site_map: List[PageRoute]
    global_state_needs: List[str]
    theme_colors: List[str]
```

### 4.4 Code Agent Output

```python
class CodeGenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str = Field(default="src/app/page.tsx", min_length=1, max_length=500)
    code: str = Field(..., min_length=1)
    language: str = Field(default="typescript", min_length=1, max_length=50)
    explanation: str
```

### 4.5 QA Agent Output

```python
class QAIssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class QAIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: QAIssueSeverity
    description: str
    suggestion: str

class QAResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    issues: List[QAIssue]
    summary: str
```

### 4.6 Pedagogy Agent — Choice Framework

```python
class ImplementationOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    pros: List[str]
    cons: List[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    educational_value: str

class ChoiceFramework(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context: str
    options: List[ImplementationOption]
    recommendation: str
```

### 4.7 Roadmap Agent Output

```python
class RoadmapModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    steps: List[str]
    estimated_hours: float = Field(..., gt=0, le=100)
    prerequisites: List[str] = Field(default_factory=list)

class LearningRoadmap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    skill_level: Literal["beginner", "intermediate", "advanced"]
    modules: List[RoadmapModule] = Field(..., min_length=1)
    total_estimated_hours: float = Field(..., gt=0, le=500)
```

### 4.8 Clarification Flow (Research Agent)

```python
class ClarificationQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    question: str
    options: Optional[List[str]] = None

class ClarificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    answer: str
```

## 5. API Contracts

### 5.1 Run Agent

**Endpoint:** `POST /v1/run-agent`

```json
// Request
{
  "project_id": "uuid-string-36-chars",
  "agent_type": "research",
  "input_context": { "user_idea": "A CRM for dog walkers" }
}

// Response (immediate — async execution)
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_time": "30s"
}
```

### 5.2 Run Pipeline

**Endpoint:** `POST /v1/run-pipeline`

```json
// Request
{
  "project_id": "uuid-string-36-chars",
  "input_context": { "user_idea": "A CRM for dog walkers" }
}

// Response
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_time": "5m"
}
```

### 5.3 Job Status

**Endpoint:** `GET /v1/jobs/{job_id}`

```json
{
  "job_id": "uuid",
  "status": "running",
  "agent_type": "research",
  "project_id": "uuid",
  "progress": 45.0,
  "result": null,
  "error": null,
  "created_at": "2026-01-15T10:30:00Z",
  "completed_at": null
}
```

### 5.4 SSE Stream

**Endpoint:** `GET /v1/jobs/{job_id}/stream`

Server-Sent Events format:

```
event: progress
data: {"progress": 45.0, "status": "running"}

event: complete
data: {"result": {...}, "status": "completed"}

event: error
data: {"error": "Agent timeout", "status": "failed"}

event: waiting
data: {"questions": [...], "status": "waiting_for_input"}

event: cancelled
data: {"status": "cancelled"}
```

### 5.5 Clarification Response

**Endpoint:** `POST /v1/jobs/{job_id}/respond`

```json
// Request
{
  "responses": [
    { "question_id": "q1", "answer": "Just scheduling for MVP" }
  ]
}

// Response
{ "status": "running", "message": "Agent resumed with clarifications" }
```

### 5.6 Job Listing (Paginated)

**Endpoint:** `GET /v1/jobs/{project_id}/list?limit=20&offset=0`

```json
{
  "items": [{ "job_id": "...", "status": "completed", ... }],
  "total": 42,
  "has_more": true
}
```

### 5.7 Cancel Job

**Endpoint:** `POST /v1/jobs/{job_id}/cancel`

```json
{ "status": "cancelled" }
```

### 5.8 GitHub Export

**Endpoint:** `POST /v1/projects/{project_id}/export/github`

```json
// Request
{
  "repo_name": "my-project",
  "github_token": "ghp_xxx"
}

// Response
{
  "repo_url": "https://github.com/user/my-project",
  "files_pushed": 12,
  "commit_sha": "abc123"
}
```
