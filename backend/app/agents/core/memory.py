"""
RAG Memory Service - Vector search for pattern matching.

Uses OpenAI embeddings + pgvector to find similar successful
architectural patterns from past projects.

Schema (see database/migrations/0003_vector_embeddings.sql):
    pattern_embeddings (
        id           uuid PK,
        project_type text,
        embedding    vector(1536),  -- OpenAI text-embedding-3-small
        metadata     jsonb,
        success_score float,
        created_at   timestamptz
    )
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.supabase import supabase_client

# OpenAI embedding model config
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


async def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for ``text`` using OpenAI.

    Returns:
        List of floats with length == EMBEDDING_DIMENSIONS.

    Raises:
        RuntimeError on API or network failure.
    """
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        def _call():
            return client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS,
            )

        response = await asyncio.to_thread(_call)
        embedding = response.data[0].embedding
        logger.debug(
            f"Generated embedding ({len(embedding)} dims) for text length {len(text)}"
        )
        return embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise RuntimeError(f"Failed to generate embedding: {e}") from e


async def search_similar_patterns(
    project_type: str,
    query_text: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search for similar successful architectural patterns.

    If ``query_text`` is provided, performs a **vector similarity** search
    using cosine distance (pgvector ``<=>`` operator) via the Supabase
    RPC ``match_patterns``.

    If ``query_text`` is None, falls back to a simple text-match +
    success-score ordering (no embedding needed).

    Returns:
        Top-K pattern records (id, project_type, metadata, success_score).
    """
    try:
        if query_text:
            # Vector similarity search
            embedding = await generate_embedding(query_text)

            def _rpc():
                return supabase_client.rpc(
                    "match_patterns",
                    {
                        "query_embedding": embedding,
                        "match_count": limit,
                        "filter_type": project_type,
                    },
                ).execute()

            response = await asyncio.to_thread(_rpc)
        else:
            # Fallback: simple text match + score ordering
            def _query():
                return (
                    supabase_client.table("pattern_embeddings")
                    .select("id, project_type, metadata, success_score")
                    .eq("project_type", project_type)
                    .order("success_score", desc=True)
                    .limit(limit)
                    .execute()
                )

            response = await asyncio.to_thread(_query)

        results = response.data or []
        logger.info(
            f"Pattern search for '{project_type}' returned {len(results)} results"
        )
        return results

    except Exception as e:
        logger.error(f"Pattern search failed: {e}")
        # Non-critical — return empty rather than crashing the agent
        return []


async def store_pattern(
    project_type: str,
    metadata: Dict[str, Any],
    description: str,
    success_score: float = 0.5,
) -> Optional[Dict[str, Any]]:
    """
    Store a new architectural pattern with its embedding.

    Args:
        project_type:  Category (e.g. 'saas', 'ecommerce').
        metadata:      JSONB blob describing the pattern.
        description:   Human-readable text to embed.
        success_score: Quality score 0.0 – 1.0.

    Returns:
        The created record, or None on failure.
    """
    try:
        embedding = await generate_embedding(description)

        def _insert():
            return (
                supabase_client.table("pattern_embeddings")
                .insert(
                    {
                        "project_type": project_type,
                        "embedding": embedding,
                        "metadata": metadata,
                        "success_score": max(0.0, min(1.0, success_score)),
                    }
                )
                .execute()
            )

        response = await asyncio.to_thread(_insert)

        if response.data:
            logger.info(f"Stored pattern for '{project_type}' (score={success_score})")
            return response.data[0]

        return None

    except Exception as e:
        logger.error(f"Failed to store pattern: {e}")
        return None
