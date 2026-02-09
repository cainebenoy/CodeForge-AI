-- CodeForge AI Database Schema
-- Initial schema with core tables

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Profiles table (extends auth.users)
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  username text unique,
  full_name text,
  avatar_url text,
  skill_level text check (skill_level in ('beginner', 'intermediate', 'advanced')),
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Projects table
create table public.projects (
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
create table public.project_files (
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
create table public.learning_roadmaps (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  modules jsonb not null,
  current_step_index int default 0 not null,
  created_at timestamptz default now() not null
);

-- Daily sessions (Student Mode)
create table public.daily_sessions (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  transcript jsonb,
  concepts_covered text[],
  created_at timestamptz default now() not null
);

-- Create indexes for performance
create index idx_projects_user_id on public.projects(user_id);
create index idx_projects_mode on public.projects(mode);
create index idx_project_files_project_id on public.project_files(project_id);
create index idx_project_files_path on public.project_files(path);
create index idx_learning_roadmaps_project_id on public.learning_roadmaps(project_id);

-- Updated at trigger function
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Apply updated_at triggers
create trigger update_profiles_updated_at before update on public.profiles
  for each row execute procedure update_updated_at_column();

create trigger update_projects_updated_at before update on public.projects
  for each row execute procedure update_updated_at_column();

create trigger update_project_files_updated_at before update on public.project_files
  for each row execute procedure update_updated_at_column();
