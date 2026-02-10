-- Migration: Create agent_jobs table for persistent job tracking + Supabase Realtime
--
-- This table serves two purposes:
-- 1. Persistent job history (survives server restarts)
-- 2. Supabase Realtime trigger source — frontend subscribes to
--    postgres_changes on this table for live status updates.
--
-- The in-memory/Redis job store remains for fast sub-second polling
-- during active execution. This table is the durable source of truth.

-- Enable Supabase Realtime on the projects table (status changes)
alter publication supabase_realtime add table public.projects;

-- Agent jobs table
create table public.agent_jobs (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  agent_type text not null,
  status text default 'queued' not null
    check (status in ('queued', 'running', 'completed', 'failed', 'waiting_for_input', 'cancelled')),
  progress float default 0.0 not null,
  result jsonb,
  error text,
  celery_task_id text,
  created_at timestamptz default now() not null,
  started_at timestamptz,
  completed_at timestamptz
);

-- Indexes for common queries
create index idx_agent_jobs_project on public.agent_jobs (project_id);
create index idx_agent_jobs_user on public.agent_jobs (user_id);
create index idx_agent_jobs_status on public.agent_jobs (status) where status not in ('completed', 'failed', 'cancelled');

-- Enable RLS
alter table public.agent_jobs enable row level security;

-- RLS policies: users can only see their own jobs
create policy "Users can read own agent jobs"
  on public.agent_jobs for select
  using (auth.uid() = user_id);

-- Service role can do everything (backend uses service key)
-- No INSERT/UPDATE/DELETE policies needed for authenticated users
-- since all writes come from the backend service role.

-- Enable Realtime on agent_jobs — frontend subscribes to status/progress changes
alter publication supabase_realtime add table public.agent_jobs;

-- Trigger to auto-update a timestamp when agent_jobs rows change
-- (useful for cache invalidation and ordering)
create or replace function public.handle_agent_job_updated_at()
returns trigger as $$
begin
  new.started_at = case
    when new.status = 'running' and old.status != 'running' then now()
    else new.started_at
  end;
  new.completed_at = case
    when new.status in ('completed', 'failed', 'cancelled') and old.status not in ('completed', 'failed', 'cancelled') then now()
    else new.completed_at
  end;
  return new;
end;
$$ language plpgsql;

create trigger on_agent_job_updated
  before update on public.agent_jobs
  for each row execute function public.handle_agent_job_updated_at();
