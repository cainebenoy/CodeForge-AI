-- Automatic Profile Creation Trigger
-- Run this in your Supabase SQL Editor

-- Function to create profile when user signs up
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, username, full_name, avatar_url, skill_level)
  values (
    new.id,
    new.raw_user_meta_data->>'username',
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url',
    'beginner'
  );
  return new;
end;
$$;

-- Trigger to run function on new user signup
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- For existing users without profiles, create them now
insert into public.profiles (id, skill_level)
select id, 'beginner'
from auth.users
where id not in (select id from public.profiles)
on conflict (id) do nothing;
