-- match_patterns RPC function for RAG vector similarity search
-- Called by app/agents/core/memory.py via supabase_client.rpc("match_patterns", ...)
-- Uses pgvector's cosine distance operator (<=>) consistent with the
-- vector_cosine_ops index defined in 0003_vector_embeddings.sql.

create or replace function match_patterns(
  query_embedding vector(1536),
  match_count int default 3,
  filter_type text default ''
)
returns table (
  id uuid,
  project_type text,
  metadata jsonb,
  success_score float,
  similarity float
)
language plpgsql
as $$
begin
  return query
    select
      pe.id,
      pe.project_type,
      pe.metadata,
      pe.success_score,
      1 - (pe.embedding <=> query_embedding) as similarity
    from public.pattern_embeddings pe
    where (filter_type = '' or pe.project_type = filter_type)
    order by pe.embedding <=> query_embedding
    limit match_count;
end;
$$;
