# CodeForge AI — Backend Schema & Data Models

**Document Purpose:** To define the database structure (PostgreSQL/Supabase), Row Level Security (RLS) policies, and the strict Pydantic schemas used for Agent inter-communication.

## 1. Database Schema (Supabase PostgreSQL)

We use a relational model for core entities (Users, Projects) and a document model (JSONB) for flexible Agent outputs.

### 1.1 Core Entities

### `profiles`

Extends the default `auth.users` table.

```
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  username text,
  full_name text,
  avatar_url text,
  skill_level text check (skill_level in ('beginner', 'intermediate', 'advanced')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

### `projects`

The central hub for both Builder and Student modes.

```
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  description text, -- The initial one-liner
  mode text check (mode in ('builder', 'student')) not null,
  status text default 'planning', -- 'planning', 'building', 'completed'

  -- The "Brain" of the project (Agent Outputs)
  requirements_spec jsonb, -- Output from Research Agent
  architecture_spec jsonb, -- Output from Wireframe Agent

  -- Metadata
  tech_stack text[], -- ['Next.js', 'Supabase', 'Tailwind']
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

### `project_files`

The virtual file system. Storing files individually allows specific file fetching for the IDE.

```
create table public.project_files (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  path text not null, -- e.g., "src/app/page.tsx"
  content text, -- The actual code
  language text, -- 'typescript', 'python', 'css', etc.
  version int default 1,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(project_id, path) -- Prevent duplicate paths in one project
);
```

### 1.2 Student Mode Entities

### `learning_roadmaps`

Stores the generated curriculum for a specific project.

```
create table public.learning_roadmaps (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  modules jsonb not null, -- Array of { title, steps, is_locked }
  current_step_index int default 0,

  created_at timestamptz default now()
);
```

### `daily_sessions`

Tracks the "Socratic" chat history for learning.

```
create table public.daily_sessions (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  transcript jsonb, -- Array of { role: 'user'|'mentor', content: string }
  concepts_covered text[],

  created_at timestamptz default now()
);
```

## 2. Row Level Security (RLS) Policies

**Crucial for security:** Ensure users can only access their own projects.

```
-- Enable RLS on all tables
alter table profiles enable row level security;
alter table projects enable row level security;
alter table project_files enable row level security;

-- Profiles: Users can see everyone's username (for collaboration later) but edit only their own
create policy "Public profiles are viewable by everyone."
  on profiles for select using ( true );

create policy "Users can insert their own profile."
  on profiles for insert with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update using ( auth.uid() = id );

-- Projects: Users can CRUD only their own projects
create policy "Users can crud own projects."
  on projects for all using ( auth.uid() = user_id );

-- Files: Users can CRUD files belonging to their projects
create policy "Users can crud own project files."
  on project_files for all using (
    exists ( select 1 from projects where id = project_files.project_id and user_id = auth.uid() )
  );
```

## 3. Agent Interface Schemas (Pydantic)

These Python classes define the **Strict JSON Protocol** exchanged between the Python Agent Engine and the Next.js backend.

### 3.1 Research Agent Output

Target Field: `projects.requirements_spec`

```
from pydantic import BaseModel, Field
from typing import List, Optional

class UserPersona(BaseModel):
    role: str
    goal: str
    pain_point: str

class Feature(BaseModel):
    name: str
    description: str
    priority: str # 'Must Have', 'Should Have', 'Nice to Have'

class RequirementsDoc(BaseModel):
    app_name: str
    elevator_pitch: str
    target_audience: List[UserPersona]
    core_features: List[Feature]
    recommended_stack: List[str]
    technical_constraints: Optional[str] = None
```

### 3.2 Wireframe Agent Output

Target Field: `projects.architecture_spec`

```
class Component(BaseModel):
    name: str # e.g., "ClientCard"
    props: List[str] # e.g., ["clientName", "lastWalkDate"]
    children: List[str] # Names of child components

class PageRoute(BaseModel):
    path: str # e.g., "/dashboard/clients"
    description: str
    components: List[Component]

class WireframeSpec(BaseModel):
    site_map: List[PageRoute]
    global_state_needs: List[str] # e.g., ["AuthUser", "Theme"]
    theme_colors: List[str]
```

### 3.3 Pedagogy Agent (The "Choice Framework")

This structure drives the UI cards in Student Mode.

```
class ImplementationOption(BaseModel):
    id: str # 'option_a'
    title: str # "Use Firebase"
    pros: List[str]
    cons: List[str]
    difficulty: str # 'Easy', 'Medium', 'Hard'
    educational_value: str # "Good for getting to market fast"

class ChoiceFramework(BaseModel):
    context: str # "We need to choose a database."
    options: List[ImplementationOption]
    recommendation: str # Optional hint
```

## 4. API Contracts (Next.js <-> Python)

### 4.1 Triggering an Agent

**Endpoint:** `POST https://api.codeforge.ai/v1/run-agent`

**Request Body:**

```
{
  "project_id": "uuid",
  "agent_type": "research",
  "input_context": {
    "user_idea": "A CRM for dog walkers"
  }
}
```

**Response (Async):**

```
{
  "job_id": "job_12345",
  "status": "queued",
  "estimated_time": "30s"
}
```

*Note: Since Agent runs can take 30s+, the frontend should poll for status or listen to Supabase Realtime updates on the `projects` table.*