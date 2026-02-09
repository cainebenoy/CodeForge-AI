-- Seed data for initial project templates

-- Example successful architectural patterns
insert into public.pattern_embeddings (project_type, metadata, success_score)
values
  (
    'saas',
    '{
      "name": "SaaS Starter",
      "stack": ["Next.js", "Supabase", "Stripe"],
      "architecture": {
        "auth": "Supabase Auth",
        "database": "PostgreSQL with RLS",
        "payments": "Stripe Checkout"
      }
    }'::jsonb,
    0.95
  ),
  (
    'ecommerce',
    '{
      "name": "E-commerce MVP",
      "stack": ["Next.js", "Supabase", "Stripe"],
      "architecture": {
        "cart": "Zustand state",
        "checkout": "Stripe",
        "inventory": "Supabase realtime"
      }
    }'::jsonb,
    0.92
  ),
  (
    'social',
    '{
      "name": "Social App",
      "stack": ["Next.js", "Supabase"],
      "architecture": {
        "feed": "Realtime subscriptions",
        "likes": "Optimistic updates",
        "notifications": "Supabase Functions"
      }
    }'::jsonb,
    0.88
  );

-- Note: Actual embeddings would be generated via OpenAI API
-- This is just structural placeholder
