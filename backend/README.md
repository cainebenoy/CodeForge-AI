# CodeForge Backend

Python FastAPI backend for CodeForge AI - The AI Agent Engine.

## Setup

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run development server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Lint
poetry run ruff check .

# Format
poetry run black .
```

## Architecture

```
app/
├── main.py              # FastAPI app entry point
├── core/
│   └── config.py        # Settings (env vars)
├── api/
│   ├── router.py        # API route aggregator
│   └── endpoints/       # API endpoints
├── agents/
│   ├── core/            # LLM router 
│   ├── research_agent.py
│   ├── wireframe_agent.py
│   ├── code_agent.py
│   └── orchestrator.py  # Agent workflow
├── schemas/
│   └── protocol.py      # Pydantic models
└── services/
    ├── supabase.py      # Database client
    └── github.py        # GitHub API
```

## Security

- All secrets in environment variables
- Input validation via Pydantic
- Rate limiting applied
- HTTPS only in production
- Parameterized queries only
- Service role key never exposed to client

## Deployment

Docker image included for Railway/Render deployment.
