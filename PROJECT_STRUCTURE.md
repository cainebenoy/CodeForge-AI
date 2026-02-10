# CodeForge AI - Complete Project Structure

```
CodeForge AI/
├── .github/
│   └── copilot-instructions.md     # AI coding guidelines & dev patterns
│
├── web/                            # Next.js 14 Frontend
│   ├── public/                     # Static assets
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── (auth)/            # Auth route group
│   │   │   ├── (dashboard)/       # Dashboard route group
│   │   │   │   ├── builder/       # Builder Mode routes
│   │   │   │   └── student/       # Student Mode routes
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── providers.tsx      # React Query + Theme providers
│   │   │   ├── page.tsx           # Landing page
│   │   │   └── globals.css        # Tailwind styles
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn primitives (Button, Card, etc.)
│   │   │   ├── shared/            # Reusable compounds (ThemeToggle, etc.)
│   │   │   └── features/          # Feature-specific components
│   │   │       ├── builder/       # SpecViewer, FileTree, etc.
│   │   │       ├── student/       # ChoiceCard, etc.
│   │   │       ├── editor/        # Monaco Editor wrappers
│   │   │       └── chat/          # Agent Chat Interface
│   │   │
│   │   ├── lib/
│   │   │   ├── supabase/          # Supabase clients (browser + server)
│   │   │   ├── hooks/             # Custom React hooks
│   │   │   ├── api.ts             # Backend API client
│   │   │   └── utils.ts           # Helper functions (cn, formatters)
│   │   │
│   │   ├── store/                 # Zustand stores
│   │   │   ├── useBuilderStore.ts # Builder Mode UI state
│   │   │   └── useStudentStore.ts # Student Mode UI state
│   │   │
│   │   └── types/
│   │       └── database.types.ts  # Supabase generated types
│   │
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                        # Python FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app factory + middleware stack
│   │   │
│   │   ├── core/                  # Core infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # JWT verification (Supabase)
│   │   │   ├── config.py          # Settings (Pydantic BaseSettings)
│   │   │   ├── exceptions.py      # 10 custom exception classes
│   │   │   └── logging.py         # Structured JSON logging
│   │   │
│   │   ├── middleware/            # ASGI middleware chain
│   │   │   ├── __init__.py
│   │   │   ├── csrf.py            # Double-submit cookie CSRF
│   │   │   ├── rate_limiter.py    # Token bucket rate limiter
│   │   │   └── request_tracking.py # Request ID tracing
│   │   │
│   │   ├── api/                   # HTTP layer
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Route aggregator
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── agents.py      # Agent execution + SSE streaming
│   │   │       ├── projects.py    # Project CRUD + file management
│   │   │       ├── profiles.py    # User profile endpoints
│   │   │       └── student.py     # Student mode endpoints
│   │   │
│   │   ├── agents/                # AI Agent system
│   │   │   ├── __init__.py
│   │   │   ├── research_agent.py  # Requirements generation (GPT-4o)
│   │   │   ├── wireframe_agent.py # Architecture design (GPT-4o)
│   │   │   ├── code_agent.py      # Code generation (Gemini 1.5 Pro)
│   │   │   ├── qa_agent.py        # Code review (GPT-4o)
│   │   │   ├── pedagogy_agent.py  # Socratic mentor (Claude 3.5 Sonnet)
│   │   │   ├── roadmap_agent.py   # Learning curriculum (Claude 3.5 Sonnet)
│   │   │   ├── prompts.py         # Centralized system prompts
│   │   │   ├── orchestrator.py    # Agent routing + execution
│   │   │   │
│   │   │   ├── core/              # Agent infrastructure
│   │   │   │   ├── __init__.py
│   │   │   │   ├── llm.py         # LLM model router (3 providers)
│   │   │   │   ├── memory.py      # RAG vector search (pgvector)
│   │   │   │   └── resilience.py  # Circuit breaker + retry logic
│   │   │   │
│   │   │   └── graph/             # LangGraph workflows
│   │   │       ├── __init__.py
│   │   │       ├── state.py       # TypedDict pipeline state
│   │   │       ├── nodes.py       # Graph node functions
│   │   │       └── workflows.py   # StateGraph definitions
│   │   │
│   │   ├── schemas/               # Data contracts
│   │   │   ├── __init__.py
│   │   │   └── protocol.py        # 717 lines of Pydantic v2 schemas
│   │   │
│   │   ├── services/              # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── supabase.py        # Supabase client wrapper
│   │   │   ├── database.py        # DatabaseOperations (CRUD + RLS)
│   │   │   ├── github.py          # GitHub API integration
│   │   │   ├── job_queue.py       # In-memory job store
│   │   │   └── validation.py      # InputValidator (sanitization)
│   │   │
│   │   └── workers/               # Celery task queue
│   │       ├── __init__.py
│   │       ├── celery_app.py      # Celery configuration
│   │       └── tasks.py           # Async task definitions
│   │
│   ├── tests/                     # Test suite (297 tests)
│   │   ├── __init__.py
│   │   ├── conftest.py            # Fixtures + test configuration
│   │   ├── test_agents.py         # Agent unit tests
│   │   ├── test_auth.py           # JWT auth tests
│   │   ├── test_endpoints.py      # API endpoint tests
│   │   ├── test_exceptions.py     # Custom exception tests
│   │   ├── test_github.py         # GitHub integration tests
│   │   ├── test_graph_workflows.py # LangGraph workflow tests
│   │   ├── test_hardening.py      # Security hardening tests
│   │   ├── test_job_queue.py      # Job queue lifecycle tests
│   │   ├── test_middleware.py     # Middleware tests
│   │   ├── test_new_features.py   # Celery/SSE/Realtime tests
│   │   ├── test_orchestrator.py   # Orchestrator tests
│   │   ├── test_profiles.py       # Profile endpoint tests
│   │   ├── test_projects.py       # Project CRUD tests
│   │   ├── test_student.py        # Student mode tests
│   │   └── test_validation.py     # Input validation tests
│   │
│   ├── Dockerfile                 # Production container
│   ├── pyproject.toml             # Python dependencies
│   ├── pytest.ini                 # Pytest configuration
│   ├── requirements.txt           # Pip dependencies
│   ├── README.md                  # Quick reference
│   └── README_BACKEND.md          # Comprehensive backend guide
│
├── database/                       # Supabase SQL Migrations
│   ├── migrations/
│   │   ├── 0001_init_schema.sql        # Core tables (profiles, projects, files)
│   │   ├── 0002_rls_policies.sql       # Row Level Security policies
│   │   ├── 0003_vector_embeddings.sql  # pgvector + pattern_embeddings
│   │   ├── 0004_match_patterns_rpc.sql # Similarity search RPC function
│   │   ├── 0005_add_duration_minutes.sql # Session duration tracking
│   │   ├── 0006_project_status_constraint.sql # Status enum constraint
│   │   └── 0007_agent_jobs_realtime.sql # agent_jobs table + Realtime
│   │
│   ├── seeds/
│   │   └── seed.sql               # Initial data
│   │
│   ├── config.toml                # Supabase config
│   └── README.md                  # Database documentation
│
├── docs/                           # Documentation
│   ├── PRD.md                     # Product Requirements Document
│   ├── Tech_Stack.md              # Technology stack & architecture
│   ├── Backend_Schema.md          # Database schema & API contracts
│   ├── Frontend_Guidelines.md     # Component patterns & design system
│   ├── Implementation_Details.md  # Implementation progress & roadmap
│   └── App_Flow.md                # User journeys & agent flows
│
├── docker-compose.yml             # Redis + FastAPI + Celery + Flower
├── BACKEND_IMPLEMENTATION.md      # Backend implementation summary
├── PROJECT_STRUCTURE.md           # This file
├── README.md                      # Project overview
└── .gitignore
```

## Key Architectural Decisions

### Monorepo Structure
- `/web` — Next.js frontend (TypeScript)
- `/backend` — FastAPI backend (Python)
- `/database` — Supabase migrations (SQL)

### Security by Design
- RLS on all database tables
- Pydantic v2 strict validation on all inputs
- CSRF double-submit cookie protection
- Token bucket rate limiting (60 req/min)
- Error sanitization (no stack traces to clients)
- Secrets validated at startup from environment variables

### Task Execution
- **Celery + Redis** for persistent background task queue
- **`task_acks_late`** ensures no task loss on worker crashes
- **BackgroundTasks** fallback if Celery unavailable
- **Flower** dashboard for monitoring at `:5555`

### LLM Architecture
- **Model Router**: 3 providers (OpenAI, Google, Anthropic) × 6 agents
- **Circuit Breaker**: Prevents cascade failures on LLM outages
- **LangChain LCEL**: `prompt | llm | PydanticOutputParser` chains
- **LangGraph**: StateGraph with conditional edges for multi-agent pipelines
- **RAG with pgvector**: Pattern matching from previous projects

### State Management (Frontend)
- **Server State**: React Query (TanStack Query)
- **Local UI State**: Zustand
- **Shareable State**: URL parameters

### Data Flow
```
User → Next.js → Supabase (CRUD)
User → Next.js → FastAPI → Celery → LLM → Supabase (Agent tasks)
Supabase Realtime → Next.js (Status updates)
FastAPI SSE → Next.js (Streaming progress)
```

## Quick Start

```bash
# Option A: Docker Compose
cp backend/.env.example backend/.env
docker-compose up --build

# Option B: Manual
cd web && pnpm install && pnpm dev          # Terminal 1
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload  # Terminal 2
cd backend && celery -A app.workers.celery_app worker --loglevel=info          # Terminal 3
```

## Technology Stack

**Frontend**
- Next.js 14 (App Router), TypeScript (Strict mode)
- Tailwind CSS + Shadcn/UI
- React Query + Zustand
- Monaco Editor

**Backend**
- Python 3.11+, FastAPI
- LangChain + LangGraph
- Pydantic v2 (strict validation, 717 lines of schemas)
- Celery + Redis (persistent task queue)

**Database**
- Supabase (PostgreSQL) with 7 migrations
- pgvector (RAG embeddings)
- Row Level Security (RLS)
- Supabase Realtime (agent_jobs + projects)

**AI Models**
- OpenAI GPT-4o (Research, Wireframe, QA)
- Google Gemini 1.5 Pro (Code generation)
- Anthropic Claude 3.5 Sonnet (Pedagogy, Roadmap)

**Infrastructure**
- Docker Compose (Redis, FastAPI, Celery, Flower)
- Vercel (Frontend), Railway/Render (Backend)
- 297 tests across 16 test files
