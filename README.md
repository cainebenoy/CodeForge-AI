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
│  • 4 AI Agents (Research/Wireframe/Code/Pedagogy)│
│  • LangChain/LangGraph orchestration            │
│  • Pydantic strict validation                   │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
codeforge-ai/
├── web/                    # Next.js 14 Frontend
├── backend/                # Python FastAPI Agent Engine
├── database/               # Supabase SQL Migrations
├── docs/                   # Documentation
└── .github/                # CI/CD Workflows
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Poetry (Python package manager)
- Supabase CLI
- pnpm (or npm/yarn)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/cainebenoy/CodeForge-AI.git
   cd codeforge-ai
   ```

2. **Frontend Setup**
   ```bash
   cd web
   pnpm install
   cp .env.example .env.local
   # Edit .env.local with your Supabase credentials
   pnpm dev
   ```
   Frontend runs on `http://localhost:3000`

3. **Backend Setup**
   ```bash
   cd backend
   poetry install
   cp .env.example .env
   # Edit .env with your API keys (OpenAI, Gemini, Supabase)
   poetry run uvicorn app.main:app --reload
   ```
   Backend runs on `http://localhost:8000`

4. **Database Setup**
   ```bash
   cd database
   # Initialize Supabase project
   supabase init
   # Run migrations
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
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
DATABASE_URL=your_postgres_url
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
poetry install              # Install dependencies
poetry run uvicorn app.main:app --reload  # Starts on localhost:8000
poetry run pytest           # Run tests
```

## Deployment

- **Frontend**: Vercel (auto-deploy on push to `main`)
- **Backend**: Railway/Render (containerized FastAPI)
- **Database**: Supabase (managed PostgreSQL)

## Documentation

- [Tech Stack](docs/Tech_Stack.md)
- [Backend Schema](docs/Backend_Schema.md)
- [Frontend Guidelines](docs/Frontend_Guidelines.md)
- [Implementation Details](docs/Implementation_Details.md)
- [App Flow](docs/App_Flow.md)

## Contributing

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for development guidelines.

## License

MIT
