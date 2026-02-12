-- Fix: Add missing updated_at column to agent_jobs table (Safe Version)
-- This resolves the error: record "new" has no field "updated_at"
-- And handles: trigger "update_agent_jobs_updated_at" ... already exists

-- 1. Drop existing trigger if it exists (to avoid conflict)
DROP TRIGGER IF EXISTS update_agent_jobs_updated_at ON public.agent_jobs;

-- 2. Add the column safely (only if it doesn't exist)
ALTER TABLE public.agent_jobs 
ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now() NOT NULL;

-- 3. Re-create the trigger
CREATE TRIGGER update_agent_jobs_updated_at
  BEFORE UPDATE ON public.agent_jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
