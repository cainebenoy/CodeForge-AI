# CodeForge AI Backend

Production-quality FastAPI backend for the AI code generation platform.

## Architecture Overview

```
FastAPI Application
├── Middleware (logging, CORS, rate limiting)
├── API Routes (v1/agents, v1/projects)
├── Services (database, LLM orchestration, validation)
├── Agents (research, wireframe, code, QA, pedagogy)
└── Core (config, logging, exceptions)
```

## Key Features

### 1. **Async-First Design**
- FastAPI with async/await patterns
- Non-blocking background task execution
- Timeout enforcement (5 min max per agent)

### 2. **Structured Logging**
- JSON format for easy parsing
- Request ID tracing
- Contextual information in logs

### 3. **Comprehensive Error Handling**
- Custom exception classes with HTTP status codes
- Validation error details
- Sanitized error messages (no stack traces to client)

### 4. **Input Validation & Sanitization**
- Pydantic v2 strict validation on all endpoints
- Custom validators for UUIDs, file paths, emails
- Defense against directory traversal attacks
- Dict nesting depth limits

### 5. **Rate Limiting**
- Token bucket algorithm
- Per-IP and per-user rate limits
- 60 requests/minute default (configurable)
- Graceful 429 responses with retry-after

### 6. **LLM Orchestration**
- Model Router selects optimal LLM per task:
  - **Research/QA**: GPT-4o (high reasoning)
  - **Code**: Gemini 1.5 Pro (1M context window)
  - **Wireframe**: GPT-4o (architecture)
  - **Pedagogy**: Claude 3.5 Sonnet (Socratic)
- Async LLM calls with error handling
- Timeout protection

### 7. **Job Queue System**
- In-memory job store (replace with Redis/Celery in production)
- Job status tracking: queued → running → completed/failed
- Progress monitoring with completion percentage
- Project-scoped job queries

### 8. **Database Operations**
- Supabase client with RLS enforcement
- Async database calls
- Whitelist validation for update fields
- Virtual file system (unique project_id + path constraint)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory
│   ├── core/
│   │   ├── config.py            # Settings from env variables
│   │   ├── logging.py           # Structured logging setup
│   │   └── exceptions.py        # Custom exception classes
│   ├── middleware/
│   │   ├── request_tracking.py  # Request ID + logging
│   │   └── rate_limiter.py      # Rate limiting middleware
│   ├── api/
│   │   ├── router.py            # Route aggregator
│   │   └── endpoints/
│   │       ├── agents.py        # Agent job endpoints
│   │       └── projects.py      # Project CRUD endpoints
│   ├── services/
│   │   ├── database.py          # Supabase operations
│   │   ├── supabase.py          # Supabase client init
│   │   ├── llm_orchestrator.py  # LLM routing & calls
│   │   ├── validation.py        # Input validation
│   │   └── job_queue.py         # Job storage & management
│   ├── agents/
│   │   ├── orchestrator.py      # Agent router with timeouts
│   │   ├── prompts.py           # System prompts for each agent
│   │   └── [individual agents]  # Placeholder files
│   └── schemas/
│       └── protocol.py          # Pydantic models
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── test_endpoints.py        # API endpoint tests
│   ├── test_validation.py       # Input validation tests
│   ├── test_job_queue.py        # Job queue tests
│   └── test_exceptions.py       # Exception tests
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Test configuration
└── .env.example                 # Environment variables
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

# Or use the app entry point
python -m app.main

# Docs available at: http://localhost:8000/docs
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_endpoints.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

### Production

```bash
# Build Docker image
docker build -t codeforge-backend .

# Run with production settings
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Agent Management

**POST** `/v1/run-agent`
- Trigger an AI agent job
- Request: `{project_id, agent_type, input_context}`
- Response: `{job_id, status, estimated_time}`

**GET** `/v1/jobs/{job_id}`
- Get job status and progress
- Response: `{job_id, status, progress, result, error, ...}`

**GET** `/v1/jobs/{project_id}/list`
- List all jobs for a project
- Query: `?limit=50` (max 100)
- Response: `{project_id, count, jobs[]}`

### Project Management

**POST** `/v1/projects/`
- Create a new project
- Request: `{title, description, mode, tech_stack}`
- Response: `{id, user_id, status, ...}`

**GET** `/v1/projects/{project_id}`
- Get project details
- Response: `{id, title, status, requirements_spec, ...}`

**PUT** `/v1/projects/{project_id}`
- Update project
- Request: `{title?, description?, status?, ...}`
- Response: Updated project

**GET** `/v1/projects/{project_id}/files`
- List project files (virtual file system)
- Response: `{project_id, count, files[]}`

**POST** `/v1/projects/{project_id}/files`
- Create/update file in project
- Query: `?path=src/...&content=...&language=...`
- Response: `{path, content, language, ...}`

### Health

**GET** `/health`
- Health check (development only)
- Response: `{status, service, version}`

## Environment Variables

```env
# App
ENVIRONMENT=development|production|staging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx  # Service role key (server-only!)

# LLM APIs
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=AIzaXxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
AGENT_TIMEOUT=300  # seconds

# Redis (optional, for production job queue)
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://codeforge.ai
```

## Security Practices

1. **Input Validation**: All inputs validated with Pydantic + custom validators
2. **Rate Limiting**: 60 req/min per IP/user
3. **Error Sanitization**: No stack traces in production
4. **Secret Management**: All secrets from environment variables
5. **HTTPS-Only**: Enforced in production
6. **RLS**: Database Row Level Security enforced
7. **Field Whitelisting**: Only specified fields allowed for updates
8. **Path Traversal Protection**: File paths validated, no `..` allowed
9. **Size Limits**: Request body, context, file sizes limited
10. **Timeout Protection**: All agent jobs timeout at 5 minutes

## Performance Considerations

### Response Times (Target)
- Health check: <10ms
- Agent trigger: <100ms (returns job ID immediately)
- Project CRUD: <200ms (Supabase latency)
- Agent execution: 2-10 minutes (depends on agent type)

### Scalability
- Job queue: Currently in-memory, upgrade to Redis for multi-instance
- Database: Supabase handles auto-scaling
- Rate limiting: Per-IP, scales with IP distribution
- Async/await: Handles 1000s of concurrent connections

## Future Improvements

1. **Job Queue**: Replace in-memory store with Celery + Redis
2. **Caching**: Add Redis caching for frequent queries
3. **WebSockets**: Real-time job status updates instead of polling
4. **Circuit Breaker**: Fail gracefully on LLM API issues
5. **Metrics**: Add Prometheus for monitoring
6. **Tracing**: Distributed tracing with OpenTelemetry
7. **Multi-region**: Supabase replication for availability

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Import Errors
```bash
# Verify PYTHONPATH includes app directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Supabase Connection Issues
```bash
# Verify credentials in .env
# Check SUPABASE_URL format (should be https://xxx.supabase.co)
# Check SERVICE_KEY (not the anon key)
```

### Tests Not Running
```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run with correct Python path
PYTHONPATH=. pytest
```

## Contributing

1. Keep code async-first
2. Use type hints on all functions
3. Add docstrings with security notes
4. Write tests for new features
5. Follow the exception handling pattern
6. Log important operations

## License

MIT
