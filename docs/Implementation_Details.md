# CodeForge AI — Master Implementation Plan

**Document Purpose:** A step-by-step execution roadmap for CodeForge from zero to Public Beta. Prioritizes "Builder Mode" core first, then layers "Student Mode" on top. Reflects current implementation status.

**Team Assumption:** 1 Full Stack Engineer + AI Agents

## Phase 1: The Foundation (Weeks 1-2) ✅ COMPLETE

**Goal:** A working "Skeleton" where a user can log in, create a project, and see a dashboard. The Python Engine is connected to the Next.js App.

### Week 1: Infrastructure & Auth ✅

- **Repo Setup:** Next.js 14 App Router + Tailwind CSS + Shadcn/UI + ESLint/Prettier
- **Supabase Init:** SQL migrations for tables, RLS policies, pgvector extension
- **Frontend Shell:** Auth pages, dashboard layout, project list
- **Python Engine Skeleton:** FastAPI project with modular structure, `/health` endpoint, Dockerfile for containerized deployment

### Week 2: Agent Orchestration Core ✅

- **LangChain + LangGraph Setup:** Installed `langchain`, `langchain-openai`, `langchain-google-genai`, `langchain-anthropic`, `langgraph`, `pydantic`
- **Database Connection:** `supabase-py` with service role key, async wrapper via `asyncio.to_thread`
- **Job Queue:** InMemoryJobStore with thread-safe locking + Redis store option + Celery persistent task queue
- **Realtime Feedback Loop:** Supabase Realtime on `projects` and `agent_jobs` tables + SSE streaming endpoint

## Phase 2: The "Builder Mode" Logic (Weeks 3-6) ✅ COMPLETE

**Goal:** A user can input an idea and get a full Spec + File Structure.

### Week 3: The Research Agent ✅

- **Prompt Engineering:** System Prompt for "Product Manager Persona" (in `prompts.py`)
- **Pydantic Schema:** `RequirementsDoc` with strict validation (`extra="forbid"`, min/max lengths)
- **Clarification Loop:** Research Agent asks clarifying questions → user responds → spec refined with `WAITING_FOR_INPUT` status
- **RAG Integration:** `search_similar_patterns()` enriches agent context with previous architectural patterns
- **LLM Resilience:** `resilient_llm_call()` with circuit breaker + exponential backoff on all `chain.ainvoke()` calls

### Week 4: The Wireframe Agent ✅

- **Architecture Logic:** System Prompt for "System Architect"
- **Pydantic Schema:** `WireframeSpec` with `PageRoute` and `Component` models
- **Resilient Execution:** Wrapped with `resilient_llm_call()` for retry on transient failures

### Week 5: Code Generation ✅

- **Code Agent:** Uses **Gemini 1.5 Pro** (1M token context) via Model Router
- **Pydantic Schema:** `CodeGenerationResult` with file path, code, language, explanation
- **Virtual File System:** Writes rows to `project_files` with unique `(project_id, path)` constraint
- **Refactoring:** Separate refactor prompt for modifying existing code

### Week 6: QA & Pipeline ✅

- **QA Agent:** Code review with severity scoring (`critical`, `warning`, `info`)
- **Builder Pipeline (LangGraph):** `Research → Wireframe → Code → QA` with conditional edge code→QA retry loop (max `MAX_AGENT_ITERATIONS` iterations)
- **Progress Callbacks:** Pipeline emits progress updates through the job system

## Phase 3: Student Mode & Pedagogy (Weeks 7-9) ✅ COMPLETE

**Goal:** Implement the "Learning Layer" and "Choice Framework."

### Week 7: Curriculum Generation ✅

- **Roadmap Agent:** Uses Claude 3.5 Sonnet for Socratic curriculum design
- **Pydantic Schema:** `LearningRoadmap` with `RoadmapModule` (title, steps, estimated_hours, prerequisites)
- **Endpoints:** `POST /v1/student/roadmap`, `GET /v1/student/roadmap/{project_id}`, `PUT /v1/student/roadmap/{project_id}/progress`

### Week 8: The "Choice Framework" ✅

- **Pedagogy Agent:** Generates 3 implementation options per decision node (beginner/intermediate/advanced difficulty)
- **Pydantic Schema:** `ChoiceFramework` with `ImplementationOption` models
- **Endpoints:** `POST /v1/student/choice-framework`, `POST /v1/student/choice-framework/select`

### Week 9: Mentor Chat & Sessions ✅

- **Pedagogy Agent:** Socratic mentoring mode (hints, not answers)
- **Session Tracking:** `daily_sessions` table with transcript, concepts covered, duration
- **Progress Tracking:** `GET /v1/student/progress/{project_id}` with module completion percentage

## Phase 4: Production Hardening (Week 10) ✅ COMPLETE

**Goal:** Production Readiness.

### Security & Observability ✅

- **Structured JSON Logging:** Rotating file handler, request ID tracing
- **Custom Exception Hierarchy:** 10 exception classes with HTTP status codes
- **Error Sanitization:** Internal details logged server-side, generic messages to clients
- **Middleware Stack:** CORS, CSRF (double-submit cookie + Bearer bypass), rate limiting (token bucket), request tracking
- **Input Validation:** Pydantic v2 strict mode, custom validators, path traversal prevention, file size limits

### GitHub Export ✅

- **Git Data API:** Create repos, batch commit (blobs → tree → commit → ref)
- **Validation:** Repo name validation, file path sanitization, per-request token handling

### Infrastructure ✅

- **Celery + Redis:** Persistent task queue with crash recovery (`task_acks_late=True`)
- **Circuit Breaker:** Per-provider LLM resilience (CLOSED → OPEN → HALF_OPEN)
- **Docker Compose:** Full stack: backend + redis + celery_worker + flower monitoring
- **Dual Realtime:** SSE streaming + Supabase Realtime on `agent_jobs` table

### Testing ✅

- **297 tests** across 15 test files
- Coverage: agents, auth, endpoints, exceptions, GitHub, LangGraph workflows, security hardening, job queue, middleware, orchestrator, profiles, projects, student mode, validation, new features (circuit breaker, resilience, CSRF bypass, error handling)

## Current Implementation Statistics

| Metric              | Count                                                     |
| ------------------- | --------------------------------------------------------- |
| AI Agents           | 6 (Research, Wireframe, Code, QA, Pedagogy, Roadmap)      |
| LLM Providers       | 3 (OpenAI, Google, Anthropic)                             |
| API Endpoints       | ~25 (agents, projects, profiles, student, GitHub, health) |
| Pydantic Schemas    | 717 lines in `protocol.py`                                |
| Database Migrations | 7                                                         |
| Test Suite          | 297 tests, 15 test files                                  |
| Test Status         | All passing                                               |

## Frontend Implementation ✅ COMPLETE

All frontend features have been implemented:

1. **Builder Mode UI:** ✅ SpecViewer (functional with tabs/collapsible sections), BuilderFileTree, Monaco Editor integration, GitHub Export Modal
2. **Student Mode UI:** ✅ Roadmap Kanban (SkillTreeCanvas), Choice Framework cards, Mentor Chat, Sandpack code sandbox
3. **Real-Time Integration:** ✅ Subscribe to `agent_jobs` Realtime + SSE streaming via hooks
4. **GitHub Export UI:** ✅ GitHubExportModal with PAT input, repo name, visibility toggle
5. **Sandpack Integration:** ✅ SandpackWrapper for in-browser code execution
6. **Landing Page:** ✅ DemoVideo section (with placeholder for video), WaitlistForm/WaitlistBanner for email capture

## Checklist for Success

1. **Don't Over-Engineer the Editor:** Monaco is complex. Stick to basic syntax highlighting initially.
2. **Cache the Agents:** Use `pgvector` to find similar previous projects and reuse their specs.
3. **Strict JSON:** All agents use `PydanticOutputParser` — schemas enforced, no free-form JSON.
4. **Use Celery for Long Tasks:** Agent jobs run in Celery workers; FastAPI `BackgroundTasks` is only a fallback.
5. **Circuit Breaker Protects LLMs:** Don't overload failing providers — the breaker opens after repeated failures and auto-recovers.
