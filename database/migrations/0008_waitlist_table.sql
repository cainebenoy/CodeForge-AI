-- Waitlist table
create table public.waitlist (
  email text primary key,
  created_at timestamptz default now() not null
);

-- RLS: Allow public insert (for signups) but restrict read/update/delete
alter table public.waitlist enable row level security;

create policy "Allow public insert"
  on public.waitlist
  for insert
  with check (true);

create policy "Allow service role full access"
  on public.waitlist
  using (auth.role() = 'service_role');
