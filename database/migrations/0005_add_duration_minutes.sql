-- Add duration_minutes column to daily_sessions
-- Fixes schema-code mismatch: SessionCreate schema and create_session()
-- accept duration_minutes but the column was missing from the table.

alter table public.daily_sessions
  add column duration_minutes int default 0 not null;
