-- Migration: Add CHECK constraint for project status values
-- This ensures invalid status values are rejected at the DB level
-- rather than producing a 500 error.

-- Add check constraint to projects.status
-- Supports: planning, in-progress, building, completed, archived
alter table public.projects
  add constraint projects_status_check
  check (status in ('planning', 'in-progress', 'building', 'completed', 'archived'));
