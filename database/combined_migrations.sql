-- ============================================================================
-- CodeForge AI - Complete Database Setup
-- Run this entire script in your Supabase SQL Editor
-- ============================================================================

-- Migration 0001: Initial Schema
-- ============================================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Profiles table (extends auth.users)
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  username text unique,
  full_name text,
  avatar_url text,
  skill_level text check (skill_level in ('beginner', 'intermediate', 'advanced')),
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Projects table
create table if not exists public.projects (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  description text,
  mode text check (mode in ('builder', 'student')) not null,
  status text default 'planning' not null,
  
  -- Agent outputs (JSONB for flexibility)
  requirements_spec jsonb,
  architecture_spec jsonb,
  
  -- Metadata
  tech_stack text[],
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Project files (virtual file system)
create table if not exists public.project_files (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  path text not null,
  content text,
  language text,
  version int default 1 not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  
  -- Prevent duplicate paths per project
  unique(project_id, path)
);

-- Learning roadmaps (Student Mode)
create table if not exists public.learning_roadmaps (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  modules jsonb not null,
  current_step_index int default 0 not null,
  created_at timestamptz default now() not null
);

-- Daily sessions (Student Mode)
create table if not exists public.daily_sessions (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  transcript jsonb,
  concepts_covered text[],
  created_at timestamptz default now() not null
);

-- Agent jobs table
create table if not exists public.agent_jobs (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  agent_type text not null check (agent_type in ('research', 'wireframe', 'code', 'qa', 'pedagogy', 'roadmap')),
  status text default 'queued' not null check (status in ('queued', 'running', 'completed', 'failed', 'cancelled')),
  progress int default 0 not null check (progress >= 0 and progress <= 100),
  result jsonb,
  error jsonb,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  completed_at timestamptz
);

-- Create indexes for performance
create index if not exists idx_projects_user_id on public.projects(user_id);
create index if not exists idx_projects_mode on public.projects(mode);
create index if not exists idx_project_files_project_id on public.project_files(project_id);
create index if not exists idx_project_files_path on public.project_files(path);
create index if not exists idx_learning_roadmaps_project_id on public.learning_roadmaps(project_id);
create index if not exists idx_agent_jobs_project_id on public.agent_jobs(project_id);
create index if not exists idx_agent_jobs_status on public.agent_jobs(status);

-- Updated at trigger function
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Apply updated_at triggers
drop trigger if exists update_profiles_updated_at on public.profiles;
create trigger update_profiles_updated_at before update on public.profiles
  for each row execute procedure update_updated_at_column();

drop trigger if exists update_projects_updated_at on public.projects;
create trigger update_projects_updated_at before update on public.projects
  for each row execute procedure update_updated_at_column();

drop trigger if exists update_project_files_updated_at on public.project_files;
create trigger update_project_files_updated_at before update on public.project_files
  for each row execute procedure update_updated_at_column();

drop trigger if exists update_agent_jobs_updated_at on public.agent_jobs;
create trigger update_agent_jobs_updated_at before update on public.agent_jobs
  for each row execute procedure update_updated_at_column();


-- Migration 0002: Row Level Security Policies
-- ============================================================================

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.project_files enable row level security;
alter table public.learning_roadmaps enable row level security;
alter table public.daily_sessions enable row level security;
alter table public.agent_jobs enable row level security;

-- Profiles policies
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

drop policy if exists "Users can insert own profile" on public.profiles;
create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

-- Projects policies
drop policy if exists "Users can view own projects" on public.projects;
create policy "Users can view own projects"
  on public.projects for select
  using (auth.uid() = user_id);

drop policy if exists "Users can create projects" on public.projects;
create policy "Users can create projects"
  on public.projects for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can update own projects" on public.projects;
create policy "Users can update own projects"
  on public.projects for update
  using (auth.uid() = user_id);

drop policy if exists "Users can delete own projects" on public.projects;
create policy "Users can delete own projects"
  on public.projects for delete
  using (auth.uid() = user_id);

-- Project files policies
drop policy if exists "Users can view files from own projects" on public.project_files;
create policy "Users can view files from own projects"
  on public.project_files for select
  using (
    exists (
      select 1 from public.projects
      where projects.id = project_files.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can create files in own projects" on public.project_files;
create policy "Users can create files in own projects"
  on public.project_files for insert
  with check (
    exists (
      select 1 from public.projects
      where projects.id = project_files.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can update files in own projects" on public.project_files;
create policy "Users can update files in own projects"
  on public.project_files for update
  using (
    exists (
      select 1 from public.projects
      where projects.id = project_files.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can delete files from own projects" on public.project_files;
create policy "Users can delete files from own projects"
  on public.project_files for delete
  using (
    exists (
      select 1 from public.projects
      where projects.id = project_files.project_id
        and projects.user_id = auth.uid()
    )
  );

-- Learning roadmaps policies
drop policy if exists "Users can view own roadmaps" on public.learning_roadmaps;
create policy "Users can view own roadmaps"
  on public.learning_roadmaps for select
  using (
    exists (
      select 1 from public.projects
      where projects.id = learning_roadmaps.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can create roadmaps in own projects" on public.learning_roadmaps;
create policy "Users can create roadmaps in own projects"
  on public.learning_roadmaps for insert
  with check (
    exists (
      select 1 from public.projects
      where projects.id = learning_roadmaps.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can update own roadmaps" on public.learning_roadmaps;
create policy "Users can update own roadmaps"
  on public.learning_roadmaps for update
  using (
    exists (
      select 1 from public.projects
      where projects.id = learning_roadmaps.project_id
        and projects.user_id = auth.uid()
    )
  );

-- Daily sessions policies
drop policy if exists "Users can view own sessions" on public.daily_sessions;
create policy "Users can view own sessions"
  on public.daily_sessions for select
  using (
    exists (
      select 1 from public.projects
      where projects.id = daily_sessions.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can create sessions in own projects" on public.daily_sessions;
create policy "Users can create sessions in own projects"
  on public.daily_sessions for insert
  with check (
    exists (
      select 1 from public.projects
      where projects.id = daily_sessions.project_id
        and projects.user_id = auth.uid()
    )
  );

-- Agent jobs policies
drop policy if exists "Users can view jobs from own projects" on public.agent_jobs;
create policy "Users can view jobs from own projects"
  on public.agent_jobs for select
  using (
    exists (
      select 1 from public.projects
      where projects.id = agent_jobs.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can create jobs in own projects" on public.agent_jobs;
create policy "Users can create jobs in own projects"
  on public.agent_jobs for insert
  with check (
    exists (
      select 1 from public.projects
      where projects.id = agent_jobs.project_id
        and projects.user_id = auth.uid()
    )
  );

drop policy if exists "Users can update jobs in own projects" on public.agent_jobs;
create policy "Users can update jobs in own projects"
  on public.agent_jobs for update
  using (
    exists (
      select 1 from public.projects
      where projects.id = agent_jobs.project_id
        and projects.user_id = auth.uid()
    )
  );


-- Migration 0003: Vector Embeddings (Optional - for pattern matching)
-- ============================================================================
-- NOTE: This section requires pgvector extension. If it fails, the app will
-- still work without pattern matching features.

do $$
begin
  -- Try to enable pgvector extension for similarity search
  create extension if not exists vector;
  
  -- Pattern embeddings table (only if vector extension is available)
  create table if not exists public.pattern_embeddings (
    id uuid default uuid_generate_v4() primary key,
    pattern_name text not null,
    description text,
    embedding vector(1536),
    metadata jsonb,
    created_at timestamptz default now() not null
  );

  -- Note: IVFFlat index creation deferred - requires data to build index
  -- Run this later after inserting pattern data:
  -- create index idx_pattern_embeddings_embedding on public.pattern_embeddings
  --   using ivfflat (embedding vector_cosine_ops) with (lists = 100);

  -- For now, use a simple index that works on empty tables
  create index if not exists idx_pattern_embeddings_pattern_name on public.pattern_embeddings(pattern_name);

exception
  when undefined_object then
    -- pgvector extension not available - skip vector features
    raise notice 'pgvector extension not available - skipping pattern embeddings';
  when others then
    -- Other errors - log but continue
    raise notice 'Pattern embeddings setup failed: %', sqlerrm;
end;
$$;


-- Migration 0004: Match Patterns RPC
-- ============================================================================
-- Only create if pattern_embeddings table exists

do $$
begin
  -- Check if pattern_embeddings table exists
  if exists (select from pg_tables where schemaname = 'public' and tablename = 'pattern_embeddings') then
    -- Create the match_patterns function
    execute $func$
      create or replace function match_patterns(
        query_embedding vector(1536),
        match_threshold float default 0.7,
        match_count int default 5
      )
      returns table (
        id uuid,
        pattern_name text,
        description text,
        similarity float
      )
      language plpgsql
      as $inner$
      begin
        return query
        select
          p.id,
          p.pattern_name,
          p.description,
          1 - (p.embedding <=> query_embedding) as similarity
        from public.pattern_embeddings p
        where 1 - (p.embedding <=> query_embedding) > match_threshold
        order by p.embedding <=> query_embedding
        limit match_count;
      end;
      $inner$;
    $func$;
  else
    raise notice 'pattern_embeddings table does not exist - skipping match_patterns function';
  end if;
exception
  when others then
    raise notice 'match_patterns function creation failed: %', sqlerrm;
end;
$$;


-- Migration 0005: Add duration_minutes column
-- ============================================================================

alter table public.daily_sessions 
  add column if not exists duration_minutes int;


-- Migration 0006: Project status constraint
-- ============================================================================

do $$
begin
  -- Drop existing constraint if it exists
  alter table public.projects 
    drop constraint if exists projects_status_check;
  
  -- Add new constraint
  alter table public.projects
    add constraint projects_status_check 
    check (status in ('planning', 'in-progress', 'building', 'completed', 'archived'));
exception
  when duplicate_object then
    -- Constraint already exists with correct values
    null;
end;
$$;


-- Migration 0007: Enable Realtime for agent_jobs
-- ============================================================================

-- Enable realtime for agent_jobs and projects tables
-- Note: Supabase manages a publication called 'supabase_realtime' automatically
-- We need to ensure our tables are included in it

do $$
begin
  -- Try to alter existing publication first
  begin
    alter publication supabase_realtime add table public.agent_jobs;
  exception
    when duplicate_object then
      -- Table already in publication
      null;
    when undefined_object then
      -- Publication doesn't exist, create it
      create publication supabase_realtime;
      alter publication supabase_realtime add table public.agent_jobs;
  end;
  
  -- Add projects table
  begin
    alter publication supabase_realtime add table public.projects;
  exception
    when duplicate_object then
      -- Table already in publication
      null;
  end;
end;
$$;


-- ============================================================================
-- Setup Complete!
-- ============================================================================

-- Verify tables were created
select 
  schemaname,
  tablename
from pg_tables
where schemaname = 'public'
order by tablename;
