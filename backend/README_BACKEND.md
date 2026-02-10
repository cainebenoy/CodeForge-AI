# CodeForge AI Backend

Production-quality FastAPI backend for the AI code generation and learning platform.

## Architecture Overview

```
FastAPI Application
├── Middleware (CORS, CSRF, rate limiting, request tracking)
├── API Routes (v1/agents, v1/projects, v1/profiles, v1/student)
├── Services (database, GitHub, validation, job queue)
├── Agents (research, wireframe, code, QA, pedagogy, roadmap)
│   ├── Core (LLM router, circuit breaker, memory/RAG)
│   └── Graph (LangGraph state machine, multi-agent pipelines)
├── Workers (Celery tasks with Redis broker)
└── Core (config, logging, exceptions, auth)
```

### Request Flow

```
Client → FastAPI Middleware → JWT Auth → Endpoint
  → Agent Job created (in-memory + Supabase agent_jobs table)
  → Celery task dispatched (or BackgroundTasks fallback)
  → Agent chain executes with resilient_llm_call (circuit breaker + retry)
  → Result stored in Supabase → Realtime notification to client
  → SSE stream emits progress/completion events
```

## Key Features

### 1. **Six AI Agents with Pydantic-Enforced Output**

All agents use LangChain LCEL chains (`prompt | llm | PydanticOutputParser`) with strict schema enforcement:

- **Research Agent** — Requirements spec from user idea (+ clarification flow)
- **Wireframe Agent** — Architecture & component tree design
- **Code Agent** — Production-ready code generation (+ refactoring)
- **QA Agent** — Code review with severity scoring
- **Pedagogy Agent** — Socratic learning guidance (+ choice framework)
- **Roadmap Agent** — Personalized learning curriculum

### 2. **LLM Model Router**

Selects optimal LLM per agent type for cost vs. capability:
| Agent Type | Model | Provider | Rationale |
|---|---|---|---|
| Research, QA, Wireframe | GPT-4o | OpenAI | High reasoning |
| Code, Refactor | Gemini 1.5 Pro | Google | 1M token context |
| Pedagogy, Roadmap | Claude 3.5 Sonnet | Anthropic | Socratic style |

### 3. **LLM Resilience Layer**

- **Circuit Breaker**: Per-provider (CLOSED → OPEN → HALF_OPEN states)
- **Exponential Backoff**: With jitter, configurable retries
- **Transient Error Detection**: Rate limits (429), server errors (500/502/503), timeouts
- All agent invocations wrapped with `resilient_llm_call()`

### 4. **Multi-Agent Pipelines (LangGraph)**

- **Single Agent**: Execute one agent with timeout + cancellation
- **Builder Pipeline**: Research → Wireframe → Code → QA (with code→QA retry loop)
- State machine with conditional edges and progress callbacks
- Cooperative cancellation via `job_store` status checks

### 5. **Persistent Task Queue (Celery + Redis)**

- Celery worker pool with configurable concurrency
- `task_acks_late=True` for crash recovery (tasks re-queued if worker dies)
- Soft/hard time limits from `AGENT_TIMEOUT` setting
- Falls back to FastAPI `BackgroundTasks` when Celery is unavailable
- **Flower** monitoring dashboard on port 5555

### 6. **Dual Realtime Updates**

- **SSE (Server-Sent Events)**: `/v1/jobs/{job_id}/stream` with progress events
- **Supabase Realtime**: `agent_jobs` and `projects` tables enabled for Postgres changes
- Frontend can subscribe to either or both for live updates

### 7. **Job Lifecycle Management**

- Status flow: `queued → running → completed | failed | cancelled | waiting_for_input`
- Pagination support for job listing
- Job cancellation endpoint (revokes Celery task)
- In-memory store (InMemoryJobStore with thread-safe locking) + Redis store
- Best-effort sync to `agent_jobs` Supabase table for persistence

### 8. **RAG Pattern Matching**

- pgvector embeddings (1536 dims, IVFFlat index)
- `match_patterns` RPC for semantic similarity search
- Enriches Research and Code agents with successful architectural patterns

### 9. **Security**

- JWT Bearer auth with Supabase token verification
- CSRF double-submit cookie with Bearer token bypass for API clients
- Rate limiting (token bucket, per-IP + per-user)
- Input validation (Pydantic v2 strict mode, custom validators)
- Error sanitization (no internal details in client responses)
- RLS enforcement on all database tables
- Field whitelisting for update operations
- File path traversal protection
- Request size limits

### 10. **GitHub Integration**

- Create repos and push generated code via Git Data API
- Batch commit (blobs → tree → commit → ref) for initial push
- Per-request token handling (never stored server-side)
- Repo name and file path validation

## Project Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI app factory + exception handlers
│   ├── core/
│   │   ├── config.py                # Pydantic Settings with startup validation
│   │   ├── auth.py                  # JWT verification (Supabase tokens)
│   │   ├── logging.py              # Structured JSON logging
│   │   └── exceptions.py           # Custom exception hierarchy
│   ├── middleware/
│   │   ├── csrf.py                  # CSRF protection + Bearer bypass
│   │   ├── rate_limiter.py          # Token bucket rate limiting
│   │   └── request_tracking.py      # Request ID + timing
│   ├── api/
│   │   ├── router.py               # Route aggregator
│   │   └── endpoints/
│   │       ├── agents.py           # Agent jobs, SSE, cancellation
│   │       ├── projects.py         # Project CRUD + files
│   │       ├── profiles.py         # User profile management
│   │       └── student.py          # Student mode endpoints
│   ├── services/
│   │   ├── database.py             # Supabase operations (async wrapper)
│   │   ├── supabase.py             # Supabase client init
│   │   ├── github.py               # GitHub API integration
│   │   ├── validation.py           # Input validation helpers
│   │   └── job_queue.py            # InMemory + Redis job stores
│   ├── agents/
│   │   ├── orchestrator.py         # Agent dispatch with timeout
│   │   ├── prompts.py              # System prompts for each agent
│   │   ├── research_agent.py       # Requirements spec generation
│   │   ├── wireframe_agent.py      # Architecture design
│   │   ├── code_agent.py           # Code generation + refactoring
│   │   ├── qa_agent.py             # Code review
│   │   ├── pedagogy_agent.py       # Learning guidance + choice framework
│   │   ├── roadmap_agent.py        # Learning roadmap generation
│   │   ├── core/
│   │   │   ├── llm.py              # Model router (3-provider)
│   │   │   ├── resilience.py       # Circuit breaker + retry
│   │   │   └── memory.py           # RAG vector search
│   │   └── graph/
│   │       ├── state.py            # LangGraph state definitions
│   │       ├── nodes.py            # Graph node functions
│   │       └── workflows.py        # Pipeline graph definitions
│   ├── workers/
│   │   ├── celery_app.py           # Celery application factory
│   │   └── tasks.py               # Celery task definitions
│   └── schemas/
│       └── protocol.py             # All Pydantic models (700+ lines)
├── tests/
│   ├── conftest.py                 # Test fixtures
│   ├── test_agents.py              # Agent unit tests
│   ├── test_auth.py                # Auth tests
│   ├── test_endpoints.py           # API endpoint tests
│   ├── test_exceptions.py          # Exception tests
│   ├── test_github.py              # GitHub integration tests
│   ├── test_graph_workflows.py     # LangGraph workflow tests
│   ├── test_hardening.py           # Security hardening tests
│   ├── test_job_queue.py           # Job queue tests
│   ├── test_middleware.py          # Middleware tests
│   ├── test_orchestrator.py        # Orchestrator tests
│   ├── test_profiles.py            # Profile tests
│   ├── test_projects.py            # Project tests
│   ├── test_student.py             # Student mode tests
│   └── test_validation.py          # Input validation tests
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── pytest.ini
└── .env.example
```

## Running the Backend

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run dev server (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs: http://localhost:8000/docs
```

### With Celery Workers

```bash
# Start Redis (required for Celery)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start Celery worker (in separate terminal)
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

# (Optional) Start Flower monitoring
celery -A app.workers.celery_app flower --port=5555
# Dashboard: http://localhost:5555
```

### Docker Compose (Full Stack)

```bash
# Start all services: backend + redis + celery worker + flower
docker compose up -d

# Or with monitoring profile (includes Flower)
docker compose --profile monitoring up -d
```

### Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run specific test
pytest tests/test_agents.py::test_model_router_routing -v
```

### Production

```bash
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Agent Execution

| Method | Path                         | Description                       |
| ------ | ---------------------------- | --------------------------------- |
| POST   | `/v1/run-agent`              | Trigger a single agent job        |
| POST   | `/v1/run-pipeline`           | Run multi-agent builder pipeline  |
| GET    | `/v1/jobs/{job_id}`          | Get job status and result         |
| GET    | `/v1/jobs/{job_id}/stream`   | SSE stream for real-time progress |
| GET    | `/v1/jobs/{project_id}/list` | List jobs for project (paginated) |
| POST   | `/v1/jobs/{job_id}/cancel`   | Cancel a running job              |
| POST   | `/v1/clarify`                | Submit clarification answers      |

### Project Management

| Method | Path                      | Description        |
| ------ | ------------------------- | ------------------ |
| POST   | `/v1/projects/`           | Create project     |
| GET    | `/v1/projects/{id}`       | Get project        |
| PUT    | `/v1/projects/{id}`       | Update project     |
| DELETE | `/v1/projects/{id}`       | Archive project    |
| GET    | `/v1/projects/`           | List user projects |
| GET    | `/v1/projects/{id}/files` | List project files |
| POST   | `/v1/projects/{id}/files` | Create/update file |

### Profiles & Student Mode

| Method       | Path                           | Description             |
| ------------ | ------------------------------ | ----------------------- |
| GET/POST/PUT | `/v1/profiles/`                | User profile CRUD       |
| POST         | `/v1/student/ask`              | Pedagogy agent guidance |
| POST         | `/v1/student/choice-framework` | Decision options        |
| POST         | `/v1/student/roadmap`          | Learning roadmap        |

### GitHub Export

| Method | Path                              | Description           |
| ------ | --------------------------------- | --------------------- |
| POST   | `/v1/projects/{id}/export/github` | Export to GitHub repo |

### Health

| Method | Path      | Description  |
| ------ | --------- | ------------ |
| GET    | `/health` | Health check |

## CSRF for API Clients

The backend enforces CSRF double-submit cookies for browser requests.
API clients using **Bearer token authentication** are automatically exempt.

```bash
# API clients — just include the Authorization header
curl -X POST http://localhost:8000/v1/run-agent \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "...", "agent_type": "research", "input_context": "..."}'
```

Browser-based clients must:

1. Read the `csrf_token` cookie set by the server
2. Send it as `X-CSRF-Token` header on POST/PUT/DELETE requests

## Environment Variables

See [`.env.example`](.env.example) for all variables with descriptions.

## Security Practices

1. **Input Validation**: Pydantic v2 strict mode + custom validators on all endpoints
2. **Rate Limiting**: Token bucket algorithm, 60 req/min per IP/user
3. **Error Sanitization**: Internal details logged server-side, never exposed to clients
4. **Secret Management**: All secrets from environment variables, validated on startup
5. **CSRF Protection**: Double-submit cookie with Bearer token bypass
6. **RLS**: Row Level Security on all Supabase tables
7. **Field Whitelisting**: Only specified fields accepted for updates
8. **Path Traversal Protection**: File paths validated, no `..` allowed
9. **JWT Verification**: Supabase JWT tokens verified on every authenticated request
10. **Circuit Breaker**: Prevents cascade failures on LLM provider outages

## Troubleshooting

### Port Already in Use

```bash
lsof -ti:8000 | xargs kill -9   # macOS/Linux
netstat -ano | findstr :8000     # Windows
```

### Celery Worker Not Processing Tasks

```bash
# Check Redis is running
redis-cli ping  # should return PONG

# Check worker is connected
celery -A app.workers.celery_app inspect active

# Check for queued tasks
celery -A app.workers.celery_app inspect reserved
```

### LLM Provider Errors

```bash
# Check circuit breaker status (in application logs)
# Look for: "Circuit breaker OPEN for provider: xxx"
# The circuit auto-resets after 60s recovery period
```

### Supabase Connection Issues

```bash
# Verify SUPABASE_URL format: https://xxx.supabase.co
# Verify using SERVICE_KEY (not anon key)
# Check RLS policies if getting empty results
```
