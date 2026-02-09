-- Enable pgvector for RAG (Retrieval Augmented Generation)
create extension if not exists vector;

-- Embeddings table for long-term memory
create table public.pattern_embeddings (
  id uuid default uuid_generate_v4() primary key,
  project_type text not null,  -- 'saas', 'ecommerce', 'social', etc.
  embedding vector(1536),       -- OpenAI embedding dimension
  metadata jsonb,                -- Pattern details
  success_score float,           -- 0-1, how well this pattern worked
  created_at timestamptz default now() not null
);

-- Vector similarity search index
create index on public.pattern_embeddings 
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Enable RLS
alter table public.pattern_embeddings enable row level security;

-- Public read access for pattern search
create policy "Patterns readable by all authenticated users"
  on public.pattern_embeddings for select
  using ( auth.role() = 'authenticated' );
