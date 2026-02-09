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

1. `0001_init_schema.sql` - Core tables (profiles, projects, files)
2. `0002_rls_policies.sql` - Row Level Security policies
3. `0003_vector_embeddings.sql` - pgvector for RAG

## Security

- **RLS enabled on all tables** - Users can only access their own data
- **Service role key** - Used by backend only, never exposed to client
- **Parameterized queries** - No SQL injection vulnerabilities
- **Unique constraints** - Prevents duplicate file paths

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
project_files     → Virtual file system
learning_roadmaps → Student mode curriculum
daily_sessions    → Learning session transcripts
pattern_embeddings→ RAG vector store
```
