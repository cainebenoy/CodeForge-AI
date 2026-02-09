-- Row Level Security (RLS) Policies
-- CRITICAL: Ensures users can only access their own data

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.project_files enable row level security;
alter table public.learning_roadmaps enable row level security;
alter table public.daily_sessions enable row level security;

-- Profiles policies
create policy "Public profiles are viewable by everyone"
  on public.profiles for select
  using ( true );

create policy "Users can insert their own profile"
  on public.profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile"
  on public.profiles for update
  using ( auth.uid() = id );

-- Projects policies
create policy "Users can view own projects"
  on public.projects for select
  using ( auth.uid() = user_id );

create policy "Users can insert own projects"
  on public.projects for insert
  with check ( auth.uid() = user_id );

create policy "Users can update own projects"
  on public.projects for update
  using ( auth.uid() = user_id );

create policy "Users can delete own projects"  
  on public.projects for delete
  using ( auth.uid() = user_id );

-- Project files policies
create policy "Users can view files from own projects"
  on public.project_files for select
  using (
    exists (
      select 1 from public.projects
      where id = project_files.project_id
      and user_id = auth.uid()
    )
  );

create policy "Users can insert files to own projects"
  on public.project_files for insert
  with check (
    exists (
      select 1 from public.projects
      where id = project_files.project_id
      and user_id = auth.uid()
    )
  );

create policy "Users can update files in own projects"
  on public.project_files for update
  using (
    exists (
      select 1 from public.projects
      where id = project_files.project_id
      and user_id = auth.uid()
    )
  );

create policy "Users can delete files from own projects"
  on public.project_files for delete
  using (
    exists (
      select 1 from public.projects
      where id = project_files.project_id
      and user_id = auth.uid()
    )
  );

-- Learning roadmaps policies
create policy "Users can view own roadmaps"
  on public.learning_roadmaps for select
  using (
    exists (
      select 1 from public.projects
      where id = learning_roadmaps.project_id
      and user_id = auth.uid()
    )
  );

create policy "Users can manage own roadmaps"
  on public.learning_roadmaps for all
  using (
    exists (
      select 1 from public.projects
      where id = learning_roadmaps.project_id
      and user_id = auth.uid()
    )
  );

-- Daily sessions policies  
create policy "Users can view own sessions"
  on public.daily_sessions for select
  using (
    exists (
      select 1 from public.projects
      where id = daily_sessions.project_id
      and user_id = auth.uid()
    )
  );

create policy "Users can manage own sessions"
  on public.daily_sessions for all
  using (
    exists (
      select 1 from public.projects
      where id = daily_sessions.project_id
      and user_id = auth.uid()
    )
  );
