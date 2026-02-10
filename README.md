# CodeForge AI

**Your AI Engineering Team** — Transform ideas into production-ready applications.

## Architecture

CodeForge AI is a hybrid monorepo with two distinct layers:

- **Frontend (Next.js 14)**: Handles UI, auth, CRUD operations via Supabase
- **Agent Engine (Python FastAPI)**: Executes long-running AI tasks with LLM orchestration

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 (TypeScript)                        │
│  • Server Components (RSC first)                │
│  • Tailwind + Shadcn/UI                         │
│  • Monaco Editor for code viewing               │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Supabase (PostgreSQL)                          │
│  • Auth (GitHub OAuth)                          │
│  • RLS policies (user isolation)                │
│  • Realtime subscriptions                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Python FastAPI (Agent Engine)                  │
│  • 6 AI Agents (Research/Wireframe/Code/QA/     │
│    Pedagogy/Roadmap)                            │
│  • LangChain/LangGraph orchestration            │
│  • Celery + Redis persistent task queue         │
│  • Pydantic v2 strict validation                │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
CodeForge AI/
├── web/                    # Next.js 14 Frontend
├── backend/                # Python FastAPI Agent Engine
├── database/               # Supabase SQL Migrations (7 migrations)
├── docs/                   # Documentation
├── docker-compose.yml      # Redis + Flower + Worker services
└── .github/                # CI/CD Workflows & Copilot Instructions
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Redis (local or Docker)
- Supabase CLI
- pnpm

### Option A: Docker Compose (Recommended)

```bash
# Clone and configure
git clone https://github.com/cainebenoy/CodeForge-AI.git
cd CodeForge-AI

# Copy env files
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services (Redis, FastAPI, Celery Worker, Flower)
docker-compose up --build
```

- Backend API: `http://localhost:8000`
- Flower Dashboard: `http://localhost:5555`

### Option B: Manual Setup

1. **Frontend Setup**
   ```bash
   cd web
   pnpm install
   cp .env.example .env.local
   # Edit .env.local with your Supabase credentials
   pnpm dev
   ```
   Frontend runs on `http://localhost:3000`

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   uvicorn app.main:app --reload
   ```
   Backend runs on `http://localhost:8000`

3. **Celery Worker** (separate terminal)
   ```bash
   cd backend
   celery -A app.workers.celery_app worker --loglevel=info
   ```

4. **Database Setup**
   ```bash
   cd database
   supabase init
   supabase db push
   ```

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Backend (.env)
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_JWT_SECRET=your_jwt_secret

# LLM Providers
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
CSRF_SECRET=generate-a-random-secret
ALLOWED_ORIGINS=http://localhost:3000

# Optional
GITHUB_APP_PRIVATE_KEY=your_github_private_key
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Development Workflow

```bash
# Frontend (Next.js)
cd web
pnpm dev                    # Starts on localhost:3000
pnpm build                  # Production build
pnpm lint                   # ESLint + Prettier

# Backend (Python Agent Engine)
cd backend
pip install -r requirements.txt  # Install dependencies
uvicorn app.main:app --reload    # Starts on localhost:8000
pytest                           # Run tests (297 tests)

# Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Flower Monitoring
celery -A app.workers.celery_app flower --port=5555
```

## AI Agents

| Agent | Model | Purpose |
|---|---|---|
| Research | GPT-4o | Requirements spec from one-liner ideas |
| Wireframe | GPT-4o | Architecture spec (sitemap, components, state) |
| Code | Gemini 1.5 Pro | Production code generation (1M token context) |
| QA | GPT-4o | Code review with severity scoring |
| Pedagogy | Claude 3.5 Sonnet | Socratic mentoring with choice frameworks |
| Roadmap | Claude 3.5 Sonnet | Personalized learning curriculum |

## Deployment

- **Frontend**: Vercel (auto-deploy on push to `main`)
- **Backend**: Railway/Render (containerized FastAPI + Celery)
- **Database**: Supabase (managed PostgreSQL)
- **Redis**: Railway Redis or Upstash

## Documentation

- [Product Requirements](docs/PRD.md)
- [Tech Stack](docs/Tech_Stack.md)
- [Backend Schema & API](docs/Backend_Schema.md)
- [Frontend Guidelines](docs/Frontend_Guidelines.md)
- [Implementation Details](docs/Implementation_Details.md)
- [App Flow](docs/App_Flow.md)
- [Backend Guide](backend/README_BACKEND.md)

## Contributing

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for development guidelines.

## License

MIT
