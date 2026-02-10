# CodeForge Backend

Python FastAPI backend for CodeForge AI — The AI Agent Engine.

> **Full documentation:** See [README_BACKEND.md](README_BACKEND.md) for the comprehensive guide.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn app.main:app --reload

# Run Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Run tests (297 tests)
pytest

# Or use Docker Compose (from project root)
docker-compose up --build
```

## Architecture

```
app/
├── main.py                # FastAPI app factory + middleware stack
├── core/                  # Auth, config, exceptions, logging
├── middleware/             # CSRF, rate limiter, request tracking
├── api/
│   ├── router.py          # API route aggregator
│   └── endpoints/         # agents, projects, profiles, student
├── agents/
│   ├── research_agent.py  # GPT-4o — Requirements generation
│   ├── wireframe_agent.py # GPT-4o — Architecture design
│   ├── code_agent.py      # Gemini 1.5 Pro — Code generation
│   ├── qa_agent.py        # GPT-4o — Code review
│   ├── pedagogy_agent.py  # Claude 3.5 Sonnet — Socratic mentor
│   ├── roadmap_agent.py   # Claude 3.5 Sonnet — Learning curriculum
│   ├── orchestrator.py    # Agent routing + execution
│   ├── prompts.py         # Centralized system prompts
│   ├── core/              # LLM router, memory (RAG), resilience (circuit breaker)
│   └── graph/             # LangGraph workflows (state, nodes, workflows)
├── schemas/
│   └── protocol.py        # 717 lines of Pydantic v2 schemas
├── services/              # Database, validation, job queue, GitHub, Supabase
└── workers/               # Celery task queue (celery_app, tasks)
```

## Key Stats

- **6 AI Agents** across 3 LLM providers
- **~25 API endpoints** with full validation
- **297 tests** across 16 test files
- **7 database migrations** with RLS
- **Celery + Redis** persistent task queue
- **SSE + Supabase Realtime** for live updates

## Security

- Pydantic v2 strict validation on all inputs
- CSRF double-submit cookie protection
- Token bucket rate limiting (60 req/min)
- Error sanitization (no internals exposed)
- RLS enforcement (database-level user isolation)
- All secrets from environment variables

## Deployment

Docker image included for Railway/Render deployment. See [docker-compose.yml](../docker-compose.yml) for the full stack.
