"""
RAG Memory Service - Vector search for pattern matching
Uses pgvector to find similar successful architectural patterns
"""
from typing import List, Dict, Any
from app.services.supabase import supabase_client


async def search_similar_patterns(
    project_type: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for similar successful architectural patterns
    
    Uses vector similarity search on embeddings
    Returns top K similar patterns
    """
    # This would use actual embeddings in production
    # For now, simple text match
    result = await supabase_client.table("pattern_embeddings") \
        .select("*") \
        .eq("project_type", project_type) \
        .order("success_score", desc=True) \
        .limit(limit) \
        .execute()
    
    return result.data or []
