"""
Phase 7 — Production hardening tests.

Covers:
- Rate limiter backends (InMemory, Redis)
- Enhanced health check
- Async DB wrappers (_db_execute)
- RAG memory service (generate_embedding, search, store)
- Periodic job cleanup & lifespan
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Rate limiter backend tests
# ---------------------------------------------------------------------------


class TestInMemoryRateLimiter:
    """Unit tests for the InMemoryRateLimiter class."""

    def _make_limiter(self, rate: int = 5):
        from app.middleware.rate_limiter import InMemoryRateLimiter

        return InMemoryRateLimiter(rate_per_minute=rate)

    @pytest.mark.asyncio
    async def test_allows_up_to_limit(self):
        limiter = self._make_limiter(rate=3)
        # First call always allowed (bucket created at full)
        allowed, _ = await limiter.is_allowed("k1")
        assert allowed is True
        # Next 3 calls decrement from 3
        for _ in range(3):
            allowed, _ = await limiter.is_allowed("k1")
            assert allowed is True
        # 5th call denied (1 create + 3 decrements = 4 OK, 5th denied)
        allowed, remaining = await limiter.is_allowed("k1")
        assert allowed is False
        assert remaining == 0.0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self):
        limiter = self._make_limiter(rate=1)
        ok1, _ = await limiter.is_allowed("a")
        ok2, _ = await limiter.is_allowed("b")
        assert ok1 is True
        assert ok2 is True

    @pytest.mark.asyncio
    async def test_reset_clears_state(self):
        limiter = self._make_limiter(rate=1)
        await limiter.is_allowed("x")
        await limiter.is_allowed("x")  # exhaust
        limiter.reset()
        ok, _ = await limiter.is_allowed("x")
        assert ok is True


class TestRedisRateLimiter:
    """Unit tests for RedisRateLimiter with a mocked Redis client."""

    def _make_limiter(self, rate: int = 5):
        from app.middleware.rate_limiter import RedisRateLimiter

        limiter = object.__new__(RedisRateLimiter)
        limiter._rate = rate
        limiter._redis = MagicMock()
        return limiter

    @pytest.mark.asyncio
    async def test_allows_when_under_limit(self):
        limiter = self._make_limiter(rate=10)
        limiter._redis.incr.return_value = 1
        allowed, remaining = await limiter.is_allowed("k1")
        assert allowed is True
        assert remaining == 9.0
        limiter._redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_denies_when_over_limit(self):
        limiter = self._make_limiter(rate=5)
        limiter._redis.incr.return_value = 6
        allowed, remaining = await limiter.is_allowed("k1")
        assert allowed is False
        assert remaining == 0.0

    @pytest.mark.asyncio
    async def test_remaining_calculation(self):
        limiter = self._make_limiter(rate=10)
        limiter._redis.incr.return_value = 4
        _, remaining = await limiter.is_allowed("k")
        assert remaining == 6.0


class TestRateLimiterFactory:
    """Tests for the factory function and backend selection."""

    def test_falls_back_to_inmemory(self):
        from app.middleware.rate_limiter import (
            InMemoryRateLimiter,
            _create_rate_limiter,
        )

        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.REDIS_URL = ""
            mock_settings.RATE_LIMIT_PER_MINUTE = 60
            limiter = _create_rate_limiter()
            assert isinstance(limiter, InMemoryRateLimiter)

    def test_falls_back_on_redis_error(self):
        from app.middleware.rate_limiter import (
            InMemoryRateLimiter,
            _create_rate_limiter,
        )

        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.REDIS_URL = "redis://nonexistent:6379"
            mock_settings.RATE_LIMIT_PER_MINUTE = 60
            limiter = _create_rate_limiter()
            assert isinstance(limiter, InMemoryRateLimiter)


# ---------------------------------------------------------------------------
# Enhanced health check tests
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_dependencies(self):
        """Health check should include dependency status."""
        from app.main import health_check

        with (
            patch("app.services.supabase.supabase_client") as mock_sb,
            patch("app.services.job_queue.get_job_store") as mock_store_fn,
        ):
            # Supabase OK
            mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "x"}]
            )
            # In-memory store (not Redis)
            from app.services.job_queue import InMemoryJobStore

            mock_store_fn.return_value = InMemoryJobStore()

            result = await health_check()
            assert result["status"] == "healthy"
            assert "supabase" in result["dependencies"]
            assert "redis" in result["dependencies"]
            assert result["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_health_degraded_on_supabase_failure(self):
        from app.main import health_check

        with (
            patch("app.services.supabase.supabase_client") as mock_sb,
            patch("app.services.job_queue.get_job_store") as mock_store_fn,
        ):
            mock_sb.table.side_effect = ConnectionError("db down")
            from app.services.job_queue import InMemoryJobStore

            mock_store_fn.return_value = InMemoryJobStore()

            result = await health_check()
            assert result["status"] == "degraded"
            assert "degraded" in result["dependencies"]["supabase"]


# ---------------------------------------------------------------------------
# Async DB wrappers
# ---------------------------------------------------------------------------


class TestDbExecute:
    """Tests for the _db_execute async wrapper."""

    @pytest.mark.asyncio
    async def test_runs_sync_function_in_thread(self):
        from app.services.database import _db_execute

        def sync_fn():
            return 42

        result = await _db_execute(sync_fn)
        assert result == 42

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self):
        from app.core.exceptions import ExternalServiceError
        from app.services.database import _db_execute

        def bad_fn():
            raise ValueError("oops")

        # _db_execute now categorizes generic errors as ExternalServiceError
        with pytest.raises(ExternalServiceError):
            await _db_execute(bad_fn)

    @pytest.mark.asyncio
    async def test_does_not_block_event_loop(self):
        """Verify the event loop remains responsive during _db_execute."""
        import time

        from app.services.database import _db_execute

        def slow_fn():
            time.sleep(0.05)
            return "done"

        # Run the slow function and a concurrent coroutine simultaneously
        async def fast_coro():
            return "fast"

        results = await asyncio.gather(
            _db_execute(slow_fn),
            fast_coro(),
        )
        assert results == ["done", "fast"]


# ---------------------------------------------------------------------------
# RAG Memory service
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    """Tests for generate_embedding()."""

    @pytest.mark.asyncio
    async def test_returns_embedding_vector(self):
        from app.agents.core.memory import generate_embedding

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        with patch("openai.OpenAI", return_value=mock_client):
            result = await generate_embedding("test text")
            assert len(result) == 1536
            assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_raises_on_api_failure(self):
        from app.agents.core.memory import generate_embedding

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("API error")

        with patch("openai.OpenAI", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to generate embedding"):
                await generate_embedding("test")


class TestSearchSimilarPatterns:
    """Tests for search_similar_patterns()."""

    @pytest.mark.asyncio
    async def test_text_match_fallback(self):
        """Without query_text, uses simple text-match ordering."""
        from app.agents.core.memory import search_similar_patterns

        mock_response = MagicMock()
        mock_response.data = [
            {"id": "1", "project_type": "saas", "metadata": {}, "success_score": 0.9}
        ]

        with patch("app.agents.core.memory.supabase_client") as mock_sb:
            (
                mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value
            ) = mock_response

            results = await search_similar_patterns("saas", query_text=None)
            assert len(results) == 1
            assert results[0]["project_type"] == "saas"

    @pytest.mark.asyncio
    async def test_vector_search_with_query_text(self):
        """With query_text, generates embedding and calls RPC."""
        from app.agents.core.memory import search_similar_patterns

        mock_rpc_response = MagicMock()
        mock_rpc_response.data = [
            {"id": "2", "project_type": "ecommerce", "success_score": 0.8}
        ]

        with (
            patch(
                "app.agents.core.memory.generate_embedding", new_callable=AsyncMock
            ) as mock_embed,
            patch("app.agents.core.memory.supabase_client") as mock_sb,
        ):
            mock_embed.return_value = [0.1] * 1536
            mock_sb.rpc.return_value.execute.return_value = mock_rpc_response

            results = await search_similar_patterns(
                "ecommerce", query_text="online store"
            )
            assert len(results) == 1
            mock_embed.assert_awaited_once_with("online store")

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        """Search should not crash on failure — returns empty list."""
        from app.agents.core.memory import search_similar_patterns

        with patch("app.agents.core.memory.supabase_client") as mock_sb:
            mock_sb.table.side_effect = Exception("db error")
            results = await search_similar_patterns("saas")
            assert results == []


class TestStorePattern:
    """Tests for store_pattern()."""

    @pytest.mark.asyncio
    async def test_stores_pattern_with_embedding(self):
        from app.agents.core.memory import store_pattern

        mock_response = MagicMock()
        mock_response.data = [{"id": "new-id", "project_type": "saas"}]

        with (
            patch(
                "app.agents.core.memory.generate_embedding", new_callable=AsyncMock
            ) as mock_embed,
            patch("app.agents.core.memory.supabase_client") as mock_sb,
        ):
            mock_embed.return_value = [0.5] * 1536
            mock_sb.table.return_value.insert.return_value.execute.return_value = (
                mock_response
            )

            result = await store_pattern(
                project_type="saas",
                metadata={"stack": ["next.js"]},
                description="SaaS boilerplate",
                success_score=0.85,
            )
            assert result is not None
            assert result["id"] == "new-id"
            mock_embed.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clamps_success_score(self):
        from app.agents.core.memory import store_pattern

        mock_response = MagicMock()
        mock_response.data = [{"id": "x"}]

        with (
            patch(
                "app.agents.core.memory.generate_embedding", new_callable=AsyncMock
            ) as mock_embed,
            patch("app.agents.core.memory.supabase_client") as mock_sb,
        ):
            mock_embed.return_value = [0.0] * 1536
            mock_sb.table.return_value.insert.return_value.execute.return_value = (
                mock_response
            )

            # Score > 1.0 should be clamped
            await store_pattern("x", {}, "test", success_score=5.0)
            insert_call = mock_sb.table.return_value.insert.call_args[0][0]
            assert insert_call["success_score"] == 1.0

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self):
        from app.agents.core.memory import store_pattern

        with patch(
            "app.agents.core.memory.generate_embedding", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.side_effect = RuntimeError("embedding failed")
            result = await store_pattern("saas", {}, "test")
            assert result is None


# ---------------------------------------------------------------------------
# Periodic job cleanup & lifespan
# ---------------------------------------------------------------------------


class TestPeriodicJobCleanup:
    """Tests for the background cleanup coroutine."""

    @pytest.mark.asyncio
    async def test_cleanup_runs_and_can_be_cancelled(self):
        from app.main import _periodic_job_cleanup

        mock_store = MagicMock()
        mock_store.cleanup_old_jobs.return_value = 3

        with patch("app.services.job_queue.get_job_store", return_value=mock_store):
            # Override the sleep interval so the test doesn't wait an hour
            with patch("app.main.JOB_CLEANUP_INTERVAL_SECONDS", 0.01):
                task = asyncio.create_task(_periodic_job_cleanup())
                await asyncio.sleep(0.05)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Should have called cleanup at least once
            assert mock_store.cleanup_old_jobs.call_count >= 1


class TestLifespan:
    """Tests for the FastAPI lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_starts_and_stops_cleanup(self):
        import app.main as main_mod
        from app.main import lifespan

        mock_app = MagicMock()

        async with lifespan(mock_app):
            # Cleanup task should have been created
            assert main_mod._cleanup_task is not None
            assert not main_mod._cleanup_task.done()

        # After exiting, the task should be cancelled
        # (it might take a moment to fully cancel)
        await asyncio.sleep(0.05)
        assert main_mod._cleanup_task.done()
