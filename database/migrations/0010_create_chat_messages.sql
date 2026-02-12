-- Migration: Create chat_messages table for Realtime Chat
--
-- This table serves as the message bus for the Agent Chat.
-- 1. Frontend inserts User messages (or Backend does, depending on architecture - Guide says Backend logs it)
-- 2. Backend inserts 'System' (Thinking) and 'Assistant' (Response) messages
-- 3. Frontend subscribes to changes via Supabase Realtime

CREATE TABLE public.chat_messages (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id uuid REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content text NOT NULL,
  is_thinking boolean DEFAULT false,
  created_at timestamptz DEFAULT now() NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb
);

-- Indexes for fast retrieval by project
CREATE INDEX idx_chat_messages_project ON public.chat_messages(project_id);
CREATE INDEX idx_chat_messages_created_at ON public.chat_messages(created_at);

-- Enable RLS
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can see messages for projects they own
CREATE POLICY "Users can read chat messages for details own projects"
  ON public.chat_messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects 
      WHERE id = chat_messages.project_id 
      AND user_id = auth.uid()
    )
  );

-- Service role (Backend) can insert/update/delete
-- Authenticated users might need insert permission if they write directly, 
-- but the guide says the Backend endpoint logs the user message. 
-- We'll allow users to insert for optimistic UI if needed, but primarily backend handles it.
-- Actually, the guide says: "3.2 ... Log the 'User Message' to the DB" (Backend).
-- So valid users just need Read access.

-- Enable Supabase Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.chat_messages;
