# CodeForge AI - Complete Project Structure

```
CodeForge AI/
├── .github/
│   ├── workflows/
│   │   ├── web-deploy.yml          # Next.js CI/CD
│   │   └── backend-deploy.yml      # FastAPI CI/CD
│   └── copilot-instructions.md     # AI coding guidelines
│
├── .vscode/
│   ├── settings.json               # VS Code workspace settings
│   └── extensions.json             # Recommended extensions
│
├── web/                            # Next.js 14 Frontend
│   ├── public/                     # Static assets
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── (auth)/            # Auth route group
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── (dashboard)/       # Dashboard route group
│   │   │   │   ├── builder/
│   │   │   │   │   └── [projectId]/page.tsx
│   │   │   │   ├── student/
│   │   │   │   │   └── [projectId]/page.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── providers.tsx      # React Query + Theme providers
│   │   │   ├── page.tsx           # Landing page
│   │   │   └── globals.css        # Tailwind styles
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn primitives
│   │   │   │   └── button.tsx
│   │   │   ├── shared/            # Shared components
│   │   │   │   └── ThemeToggle.tsx
│   │   │   └── features/          # Feature-specific
│   │   │       ├── builder/
│   │   │       │   ├── SpecViewer.tsx
│   │   │       │   └── FileTree.tsx
│   │   │       ├── student/
│   │   │       │   └── ChoiceCard.tsx
│   │   │       ├── editor/
│   │   │       │   └── CodeEditor.tsx
│   │   │       └── chat/
│   │   │           └── ChatBubble.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── supabase/
│   │   │   │   ├── client.ts      # Browser client
│   │   │   │   └── server.ts      # Server client
│   │   │   ├── hooks/
│   │   │   │   └── use-project.ts
│   │   │   ├── api.ts             # API client (axios)
│   │   │   └── utils.ts           # Helper functions
│   │   │
│   │   ├── store/                 # Zustand stores
│   │   │   ├── useBuilderStore.ts
│   │   │   └── useStudentStore.ts
│   │   │
│   │   └── types/
│   │       └── database.types.ts  # Supabase generated types
│   │
│   ├── .env.example
│   ├── .eslintrc.js
│   ├── .prettierrc
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                        # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   │
│   │   ├── core/
│   │   │   └── config.py          # Settings (Pydantic)
│   │   │
│   │   ├── api/
│   │   │   ├── router.py          # Route aggregator
│   │   │   └── endpoints/
│   │   │       ├── agents.py      # POST /run-agent
│   │   │       └── projects.py    # Project CRUD
│   │   │
│   │   ├── agents/
│   │   │   ├── core/
│   │   │   │   ├── llm.py         # Model router
│   │   │   │   └── memory.py      # RAG vector search
│   │   │   ├── research_agent.py  # Requirements generation
│   │   │   ├── wireframe_agent.py # Architecture design
│   │   │   ├── code_agent.py      # Code generation
│   │   │   ├── qa_agent.py        # Code validation
│   │   │   ├── pedagogy_agent.py  # Socratic mentor
│   │   │   └── orchestrator.py    # Agent workflow
│   │   │
│   │   ├── schemas/
│   │   │   └── protocol.py        # Pydantic models
│   │   │
│   │   └── services/
│   │       ├── supabase.py        # Database client
│   │       └── github.py          # GitHub API integration
│   │
│   ├── tests/
│   │   └── test_agents.py
│   │
│   ├── .env.example
│   ├── Dockerfile
│   ├── pyproject.toml             # Poetry dependencies
│   └── README.md
│
├── database/                       # Supabase SQL Migrations
│   ├── migrations/
│   │   ├── 0001_init_schema.sql   # Core tables
│   │   ├── 0002_rls_policies.sql  # Row Level Security
│   │   └── 0003_vector_embeddings.sql  # pgvector
│   │
│   ├── seeds/
│   │   └── seed.sql               # Initial data
│   │
│   ├── config.toml                # Supabase config
│   └── README.md
│
├── docs/                           # Documentation
│   ├── Tech_Stack.md
│   ├── Backend_Schema.md
│   ├── Frontend_Guidelines.md
│   ├── Implementation_Details.md
│   ├── App_Flow.md
│   └── PRD.md
│
├── .gitignore
└── README.md
```

## Key Architectural Decisions

### Monorepo Structure
- `/web` - Next.js frontend (TypeScript)
- `/backend` - FastAPI backend (Python)
- `/database` - Supabase migrations (SQL)

### Security by Design
- RLS on all database tables
- Pydantic validation on all inputs
- Secrets in environment variables only
- HTTPS enforced in production
- Rate limiting on all endpoints

### State Management
- **Server State**: React Query (TanStack Query)
- **Local UI State**: Zustand
- **Shareable State**: URL parameters

### LLM Architecture
- **Model Router**: Optimizes cost vs intelligence
- **Pydantic Enforcement**: Strict schemas prevent hallucination
- **LangGraph**: Manages cyclic agent workflows
- **RAG with pgvector**: Pattern matching from previous projects

### Data Flow
```
User → Next.js → Supabase (CRUD)
User → Next.js → FastAPI → LLM → Supabase (Agent tasks)
Supabase Realtime → Next.js (Status updates)
```

## Next Steps

1. **Install Dependencies**
   ```bash
   # Frontend
   cd web && pnpm install

   # Backend
   cd backend && poetry install
   ```

2. **Setup Environment Variables**
   ```bash
   # Copy example files
   cp web/.env.example web/.env.local
   cp backend/.env.example backend/.env
   ```

3. **Initialize Supabase**
   ```bash
   cd database && supabase start
   ```

4. **Run Development Servers**
   ```bash
   # Terminal 1: Frontend
   cd web && pnpm dev

   # Terminal 2: Backend
   cd backend && poetry run uvicorn app.main:app --reload
   ```

## Technology Stack

**Frontend**
- Next.js 14 (App Router)
- TypeScript (Strict mode)
- Tailwind CSS + Shadcn/UI
- React Query + Zustand
- Monaco Editor

**Backend**
- Python 3.11+
- FastAPI
- LangChain + LangGraph
- Pydantic (validation)
- Instructor (structured LLM outputs)

**Database**
- Supabase (PostgreSQL)
- pgvector (RAG embeddings)
- Row Level Security (RLS)

**AI Models**
- GPT-4o (Research, QA)
- Gemini 1.5 Pro (Code generation)
- Claude 3.5 Sonnet (Pedagogy)
- Gemini Flash (Routing)

**Infrastructure**
- Vercel (Frontend)
- Railway/Render (Backend)
- Supabase (Database)
- GitHub Actions (CI/CD)
