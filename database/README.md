# CodeForge Database

Supabase PostgreSQL database schema and migrations.

## Setup

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Initialize Supabase project
supabase init

# Link to remote project
supabase link --project-ref <your-project-ref>

# Run migrations
supabase db push

# Generate TypeScript types
supabase gen types typescript --local > ../web/src/types/database.types.ts
```

## Migrations

Migrations are applied in order:

| # | File | Description |
|---|---|---|
| 1 | `0001_init_schema.sql` | Core tables (profiles, projects, project_files, learning_roadmaps, daily_sessions) |
| 2 | `0002_rls_policies.sql` | Row Level Security policies on all tables |
| 3 | `0003_vector_embeddings.sql` | pgvector extension + pattern_embeddings table |
| 4 | `0004_match_patterns_rpc.sql` | `match_patterns()` RPC function for similarity search |
| 5 | `0005_add_duration_minutes.sql` | `duration_minutes` column on daily_sessions |
| 6 | `0006_project_status_constraint.sql` | CHECK constraint on project status values |
| 7 | `0007_agent_jobs_realtime.sql` | agent_jobs table + Supabase Realtime publication |

## Security

- **RLS enabled on all tables** — Users can only access their own data
- **Service role key** — Used by backend only, never exposed to client
- **Parameterized queries** — No SQL injection vulnerabilities
- **Unique constraints** — Prevents duplicate file paths per project
- **Status constraint** — Only valid project statuses allowed (`planning`, `in-progress`, `building`, `completed`, `archived`)

## Local Development

```bash
# Start local Supabase
supabase start

# Access Studio
open http://localhost:54323

# Reset database
supabase db reset

# Seed data
psql postgresql://postgres:postgres@localhost:54322/postgres < seeds/seed.sql
```

## Schema Overview

```
profiles          → User accounts (extends auth.users)
projects          → User projects (builder/student mode)
project_files     → Virtual file system (unique per project+path)
agent_jobs        → Background task tracking (Celery jobs)
learning_roadmaps → Student mode curriculum
daily_sessions    → Learning session transcripts (with duration_minutes)
pattern_embeddings→ RAG vector store (pgvector, 1536 dimensions)
```

## Tables Detail

### profiles
Extends `auth.users`. Created automatically on signup via trigger.
- `id` (UUID, FK to auth.users)
- `display_name`, `avatar_url`, `skill_level`

### projects
User's builder or student projects.
- `id` (UUID), `user_id` (FK to profiles)
- `mode` ('builder' | 'student')
- `status` ('planning' | 'in-progress' | 'building' | 'completed' | 'archived')
- `requirements_spec` (JSONB — Research Agent output)
- `architecture_spec` (JSONB — Wireframe Agent output)

### project_files
Virtual file system. Unique constraint on `(project_id, path)`.
- `project_id` (FK), `path`, `content`, `language`

### agent_jobs
Background task tracking with Realtime publication.
- `id` (UUID), `project_id` (FK), `user_id` (FK)
- `agent_type`, `status`, `progress` (0-100)
- `result` (JSONB), `error_message`
- Realtime-enabled for live UI updates

### learning_roadmaps
Student mode learning curriculum.
- `project_id` (FK), `modules` (JSONB array)

### daily_sessions
Learning session transcripts.
- `project_id` (FK), `transcript` (JSONB), `concepts_covered` (text[])
- `duration_minutes` (integer)

### pattern_embeddings
RAG vector store for architectural patterns.
- `embedding` (vector(1536)), `metadata` (JSONB)
- Uses `match_patterns()` RPC for similarity search
