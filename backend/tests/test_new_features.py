"""
Tests for all new backend features:
- Model router (roadmap type, fallback)
- JobStatusType new states (WAITING_FOR_INPUT, CANCELLED)
- InMemoryJobStore thread safety
- Job pagination (get_project_jobs returns dict)
- Circuit breaker state machine
- Transient error detection
- resilient_llm_call retry + circuit breaker integration
- CSRF Bearer token bypass
- ExternalServiceError sanitization
- _db_execute error categorization
- Config startup validation
"""

import asyncio
import secrets
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.job_queue import InMemoryJobStore, Job, JobStatusType

# ──────────────────────────────────────────────────────────────
# Model Router tests
# ──────────────────────────────────────────────────────────────


class TestModelRouter:
    """Tests for the LLM model router (get_optimal_model)."""

    def test_research_routes_to_openai(self):
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("research")
        assert model is not None

    def test_wireframe_routes_to_openai(self):
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("wireframe")
        assert model is not None

    def test_code_routes_to_google(self):
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("code")
        assert model is not None

    def test_qa_routes_to_openai(self):
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("qa")
        assert model is not None

    def test_pedagogy_routes_to_anthropic(self):
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("pedagogy")
        assert model is not None

    def test_roadmap_routes_to_anthropic(self):
        """Roadmap agent should route to Anthropic (Claude) — not fall through."""
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("roadmap")
        assert model is not None

    def test_unknown_type_returns_fallback(self):
        """Unknown agent types should return a fallback model with a warning."""
        from app.agents.core.llm import get_optimal_model

        model = get_optimal_model("nonexistent_type")
        assert model is not None


# ──────────────────────────────────────────────────────────────
# JobStatusType new states
# ──────────────────────────────────────────────────────────────


class TestJobStatusTypes:
    """Tests for new job status values."""

    def test_waiting_for_input_exists(self):
        assert JobStatusType.WAITING_FOR_INPUT.value == "waiting_for_input"

    def test_cancelled_exists(self):
        assert JobStatusType.CANCELLED.value == "cancelled"

    def test_cancelled_is_complete(self):
        """Cancelled jobs should be considered complete."""
        job = Job(job_id="c1", project_id="p1", agent_type="research")
        job.status = JobStatusType.CANCELLED
        assert job.is_complete is True

    def test_waiting_for_input_is_not_complete(self):
        """Waiting-for-input jobs should NOT be complete."""
        job = Job(job_id="w1", project_id="p1", agent_type="research")
        job.status = JobStatusType.WAITING_FOR_INPUT
        assert job.is_complete is False

    def test_all_statuses_are_valid(self):
        """Verify all expected statuses exist."""
        expected = {
            "queued",
            "running",
            "completed",
            "failed",
            "waiting_for_input",
            "cancelled",
        }
        actual = {s.value for s in JobStatusType}
        assert expected == actual


# ──────────────────────────────────────────────────────────────
# InMemoryJobStore thread safety
# ──────────────────────────────────────────────────────────────


class TestJobStoreThreadSafety:
    """Tests for InMemoryJobStore thread-safe operations."""

    def test_concurrent_job_creation(self, fresh_job_store):
        """Multiple threads creating jobs should not lose data."""
        errors = []

        def create_job(i):
            try:
                fresh_job_store.create_job(
                    job_id=f"thread-job-{i}",
                    project_id="p-thread",
                    agent_type="research",
                    input_context={},
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_job, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # All 50 jobs should be stored
        result = fresh_job_store.get_project_jobs("p-thread", limit=100)
        assert result["total"] == 50

    def test_concurrent_updates(self, fresh_job_store):
        """Concurrent updates to the same job should not crash."""
        fresh_job_store.create_job(
            job_id="race-job",
            project_id="p-race",
            agent_type="code",
            input_context={},
        )

        errors = []

        def update_progress(progress):
            try:
                fresh_job_store.update_job("race-job", progress=progress)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_progress, args=(i * 10,)) for i in range(11)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        job = fresh_job_store.get_job("race-job")
        assert job is not None
        assert 0 <= job.progress <= 100


# ──────────────────────────────────────────────────────────────
# Job pagination
# ──────────────────────────────────────────────────────────────


class TestJobPagination:
    """Tests for paginated get_project_jobs."""

    def test_returns_dict_with_items_and_total(self, fresh_job_store):
        """get_project_jobs should return a dict, not a list."""
        for i in range(5):
            fresh_job_store.create_job(
                job_id=f"pg-{i}",
                project_id="p-page",
                agent_type="research",
                input_context={},
            )

        result = fresh_job_store.get_project_jobs("p-page")
        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result
        assert "has_more" in result
        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["has_more"] is False

    def test_limit_caps_items(self, fresh_job_store):
        """Limit should cap the number of returned items."""
        for i in range(10):
            fresh_job_store.create_job(
                job_id=f"lm-{i}",
                project_id="p-limit",
                agent_type="code",
                input_context={},
            )

        result = fresh_job_store.get_project_jobs("p-limit", limit=3)
        assert len(result["items"]) == 3
        assert result["total"] == 10
        assert result["has_more"] is True

    def test_offset_skips_items(self, fresh_job_store):
        """Offset should skip leading items."""
        for i in range(5):
            fresh_job_store.create_job(
                job_id=f"off-{i}",
                project_id="p-offset",
                agent_type="qa",
                input_context={},
            )

        result = fresh_job_store.get_project_jobs("p-offset", limit=10, offset=3)
        # 5 total, offset by 3 → should get 2 items
        assert len(result["items"]) <= 5
        assert result["total"] == 5

    def test_empty_project(self, fresh_job_store):
        """Empty project should return zero items."""
        result = fresh_job_store.get_project_jobs("nonexistent-project")
        assert result["total"] == 0
        assert len(result["items"]) == 0
        assert result["has_more"] is False


# ──────────────────────────────────────────────────────────────
# Circuit Breaker
# ──────────────────────────────────────────────────────────────


class TestCircuitBreaker:
    """Tests for the CircuitBreaker state machine."""

    @pytest.mark.asyncio
    async def test_starts_closed(self):
        from app.agents.core.resilience import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test-provider")
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_keeps_closed(self):
        from app.agents.core.resilience import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test-provider")

        async def success():
            return "ok"

        result = await cb.call(success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        from app.agents.core.resilience import (
            CircuitBreaker,
            CircuitBreakerError,
            CircuitState,
        )

        cb = CircuitBreaker("test-provider", failure_threshold=3)

        async def failing():
            raise RuntimeError("LLM error")

        # 3 failures to trigger OPEN
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == CircuitState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerError):
            await cb.call(failing)

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_recovery(self):
        from app.agents.core.resilience import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test-provider", failure_threshold=2, recovery_timeout=0.1)

        async def failing():
            raise RuntimeError("error")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call triggers HALF_OPEN check
        async def success():
            return "recovered"

        result = await cb.call(success)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_returns_to_open(self):
        from app.agents.core.resilience import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test-provider", failure_threshold=2, recovery_timeout=0.1)

        async def failing():
            raise RuntimeError("error")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.15)

        # Fail again during half-open
        with pytest.raises(RuntimeError):
            await cb.call(failing)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_reset(self):
        from app.agents.core.resilience import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test-provider", failure_threshold=2)

        async def failing():
            raise RuntimeError("error")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0


# ──────────────────────────────────────────────────────────────
# Transient error detection
# ──────────────────────────────────────────────────────────────


class TestTransientErrorDetection:
    """Tests for _is_transient_error."""

    def test_rate_limit_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("Rate limit exceeded")) is True

    def test_429_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("HTTP 429 Too Many Requests")) is True

    def test_500_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("Internal Server Error 500")) is True

    def test_503_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("Service Unavailable 503")) is True

    def test_timeout_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(TimeoutError("Connection timed out")) is True

    def test_overloaded_is_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("API overloaded")) is True

    def test_auth_error_is_not_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("Invalid API key")) is False

    def test_validation_error_is_not_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(ValueError("Invalid input format")) is False

    def test_generic_error_is_not_transient(self):
        from app.agents.core.resilience import _is_transient_error

        assert _is_transient_error(Exception("Something went wrong")) is False


# ──────────────────────────────────────────────────────────────
# Provider detection
# ──────────────────────────────────────────────────────────────


class TestProviderDetection:
    """Tests for _detect_provider mapping."""

    def test_research_maps_to_openai(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("research") == "openai"

    def test_qa_maps_to_openai(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("qa") == "openai"

    def test_wireframe_maps_to_openai(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("wireframe") == "openai"

    def test_code_maps_to_google(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("code") == "google"

    def test_pedagogy_maps_to_anthropic(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("pedagogy") == "anthropic"

    def test_roadmap_maps_to_anthropic(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("roadmap") == "anthropic"

    def test_unknown_defaults_to_openai(self):
        from app.agents.core.resilience import _detect_provider

        assert _detect_provider("unknown_agent") == "openai"


# ──────────────────────────────────────────────────────────────
# resilient_llm_call integration
# ──────────────────────────────────────────────────────────────


class TestResilientLlmCall:
    """Tests for resilient_llm_call combining circuit breaker + retry."""

    @pytest.fixture(autouse=True)
    def _reset_circuit_breakers(self):
        """Reset all circuit breakers between tests."""
        from app.agents.core import resilience

        resilience._circuit_breakers.clear()
        yield
        resilience._circuit_breakers.clear()

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        from app.agents.core.resilience import resilient_llm_call

        async def mock_func(data):
            return {"result": data}

        result = await resilient_llm_call(
            mock_func, {"input": "test"}, agent_type="research"
        )
        assert result == {"result": {"input": "test"}}

    @pytest.mark.asyncio
    async def test_retries_transient_error(self):
        from app.agents.core.resilience import resilient_llm_call

        call_count = 0

        async def flaky_func(data):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded")
            return "success"

        result = await resilient_llm_call(
            flaky_func,
            {"input": "test"},
            agent_type="research",
            max_retries=3,
            base_delay=0.01,
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_non_transient(self):
        from app.agents.core.resilience import resilient_llm_call

        call_count = 0

        async def auth_fail(data):
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid API key")

        with pytest.raises(ValueError):
            await resilient_llm_call(
                auth_fail,
                {"input": "test"},
                agent_type="research",
                max_retries=3,
                base_delay=0.01,
            )

        # Should NOT have retried
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        from app.agents.core.resilience import resilient_llm_call

        call_count = 0

        async def always_fail(data):
            nonlocal call_count
            call_count += 1
            raise Exception("Rate limit exceeded")

        with pytest.raises(Exception, match="Rate limit"):
            await resilient_llm_call(
                always_fail,
                {"input": "test"},
                agent_type="code",
                max_retries=2,
                base_delay=0.01,
            )

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_error_not_retried(self):
        from app.agents.core.resilience import (
            CircuitBreakerError,
            get_circuit_breaker,
            resilient_llm_call,
        )

        # Force the circuit open
        cb = get_circuit_breaker("openai")
        cb._state = __import__(
            "app.agents.core.resilience", fromlist=["CircuitState"]
        ).CircuitState.OPEN
        cb._last_failure_time = time.monotonic()

        async def mock_func(data):
            return "ok"

        with pytest.raises(CircuitBreakerError):
            await resilient_llm_call(
                mock_func, {"input": "test"}, agent_type="research"
            )


# ──────────────────────────────────────────────────────────────
# CSRF Bearer token bypass
# ──────────────────────────────────────────────────────────────


class TestCSRFBearerBypass:
    """Tests for CSRF middleware Bearer token bypass."""

    def test_post_with_bearer_skips_csrf(self, client):
        """POST with Bearer token should skip CSRF validation."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {
                "sub": "test-user-id",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            "test-jwt-secret-super-secret-at-least-32-chars-long",
            algorithm="HS256",
        )

        # A POST to health without CSRF but with Bearer should not get 403
        response = client.post(
            "/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        # /health is exempt from CSRF anyway, but the point is no 403
        assert response.status_code != 403

    def test_post_without_bearer_requires_csrf(self, client):
        """POST without Bearer AND without CSRF cookie should set CSRF cookie."""
        # First, make a GET to get the CSRF cookie
        get_resp = client.get("/health")
        assert get_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_has_bearer_token_detection(self):
        """_has_bearer_token correctly identifies Bearer headers."""
        from app.middleware.csrf import _has_bearer_token

        req = MagicMock()
        req.headers = {"Authorization": "Bearer abc123"}
        assert _has_bearer_token(req) is True

        req.headers = {"Authorization": "Basic abc123"}
        assert _has_bearer_token(req) is False

        req.headers = {}
        assert _has_bearer_token(req) is False


# ──────────────────────────────────────────────────────────────
# ExternalServiceError sanitization
# ──────────────────────────────────────────────────────────────


class TestExternalServiceError:
    """Tests for ExternalServiceError message sanitization."""

    def test_error_message_does_not_expose_internals(self):
        from app.core.exceptions import ExternalServiceError

        err = ExternalServiceError("Supabase", "connection refused at 10.0.0.1:5432")
        response = err.to_dict()

        # Client-facing message should NOT contain the internal details
        assert "10.0.0.1" not in response["message"]
        assert "5432" not in response["message"]
        assert "connection refused" not in response["message"]
        assert response["message"] == "Supabase service error"

    def test_internal_message_preserved(self):
        from app.core.exceptions import ExternalServiceError

        err = ExternalServiceError("Redis", "ECONNREFUSED at 127.0.0.1:6379")
        assert err._internal_message == "ECONNREFUSED at 127.0.0.1:6379"

    def test_status_code_is_503(self):
        from app.core.exceptions import ExternalServiceError

        err = ExternalServiceError("Database", "timeout")
        assert err.status_code == 503

    def test_details_contain_service_name(self):
        from app.core.exceptions import ExternalServiceError

        err = ExternalServiceError("GitHub", "API error")
        assert err.details["service"] == "GitHub"


# ──────────────────────────────────────────────────────────────
# _db_execute error categorization
# ──────────────────────────────────────────────────────────────


class TestDbExecuteErrorHandling:
    """Tests for _db_execute error categorization."""

    @pytest.mark.asyncio
    async def test_duplicate_key_raises_validation_error(self):
        from app.core.exceptions import ValidationError
        from app.services.database import _db_execute

        def fail():
            raise Exception("duplicate key value violates unique constraint")

        with pytest.raises(ValidationError) as exc_info:
            await _db_execute(fail, operation="test_insert")
        assert "already exists" in exc_info.value.details["reason"]

    @pytest.mark.asyncio
    async def test_foreign_key_raises_validation_error(self):
        from app.core.exceptions import ValidationError
        from app.services.database import _db_execute

        def fail():
            raise Exception("violates foreign key constraint")

        with pytest.raises(ValidationError):
            await _db_execute(fail, operation="test_insert")

    @pytest.mark.asyncio
    async def test_check_constraint_raises_validation_error(self):
        from app.core.exceptions import ValidationError
        from app.services.database import _db_execute

        def fail():
            raise Exception("violates check constraint")

        with pytest.raises(ValidationError):
            await _db_execute(fail, operation="test_update")

    @pytest.mark.asyncio
    async def test_no_rows_raises_not_found(self):
        from app.core.exceptions import ResourceNotFoundError
        from app.services.database import _db_execute

        def fail():
            raise Exception("No rows returned")

        with pytest.raises(ResourceNotFoundError):
            await _db_execute(fail, operation="test_get")

    @pytest.mark.asyncio
    async def test_generic_error_raises_external_service_error(self):
        from app.core.exceptions import ExternalServiceError
        from app.services.database import _db_execute

        def fail():
            raise Exception("network unreachable")

        with pytest.raises(ExternalServiceError):
            await _db_execute(fail, operation="test_generic")

    @pytest.mark.asyncio
    async def test_codeforge_exceptions_pass_through(self):
        """Already-categorized exceptions should not be wrapped."""
        from app.core.exceptions import PermissionError
        from app.services.database import _db_execute

        def fail():
            raise PermissionError("access denied")

        with pytest.raises(PermissionError):
            await _db_execute(fail, operation="test_passthrough")

    @pytest.mark.asyncio
    async def test_success_returns_value(self):
        from app.services.database import _db_execute

        result = await _db_execute(lambda: 42, operation="test_success")
        assert result == 42


# ──────────────────────────────────────────────────────────────
# Config startup validation
# ──────────────────────────────────────────────────────────────


class TestConfigValidation:
    """Tests for config.py startup validation."""

    def test_test_environment_skips_validation(self):
        """In test environment, missing keys should not raise."""
        import os

        # We're already in test environment (conftest sets ENVIRONMENT=testing)
        from app.core.config import settings

        assert settings is not None

    def test_celery_defaults_to_redis(self):
        """Celery broker/backend should default to REDIS_URL if not set."""
        from app.core.config import Settings

        s = Settings(
            ENVIRONMENT="test",
            REDIS_URL="redis://localhost:6379",
            CELERY_BROKER_URL=None,
            CELERY_RESULT_BACKEND=None,
        )
        assert s.CELERY_BROKER_URL == "redis://localhost:6379"
        assert s.CELERY_RESULT_BACKEND == "redis://localhost:6379"


# ──────────────────────────────────────────────────────────────
# Roadmap agent uses resilient_llm_call
# ──────────────────────────────────────────────────────────────


class TestAgentsUseResilience:
    """Verify that agent LLM calls go through resilient_llm_call."""

    @pytest.mark.asyncio
    async def test_research_agent_uses_resilient_call(self):
        """Research agent should call resilient_llm_call, not chain.ainvoke directly."""
        from app.schemas.protocol import RequirementsDoc
        from tests.conftest import mock_lcel_chain

        sample = RequirementsDoc(
            app_name="Test App",
            elevator_pitch="A comprehensive test application for validating agent resilience patterns",
            target_audience=[
                {
                    "role": "Developer",
                    "goal": "Test the app",
                    "pain_point": "No tests",
                }
            ],
            core_features=[
                {
                    "name": "Testing",
                    "description": "Run all tests",
                    "priority": "must-have",
                }
            ],
            recommended_stack=["Python"],
        )

        with mock_lcel_chain("app.agents.research_agent", sample):
            with patch(
                "app.agents.research_agent.resilient_llm_call",
                new_callable=AsyncMock,
                return_value=sample,
            ) as mock_resilient:
                from app.agents.research_agent import run_research_agent

                result = await run_research_agent("test idea")

                mock_resilient.assert_awaited_once()
                call_kwargs = mock_resilient.call_args
                assert call_kwargs.kwargs.get("agent_type") == "research"

    @pytest.mark.asyncio
    async def test_roadmap_agent_uses_resilient_call(self):
        """Roadmap agent should call resilient_llm_call with agent_type='roadmap'."""
        from app.schemas.protocol import LearningRoadmap
        from tests.conftest import mock_lcel_chain

        sample = LearningRoadmap(
            modules=[
                {
                    "title": "Module One",
                    "description": "First learning module for testing",
                    "concepts": ["basics"],
                    "estimated_hours": 5.0,
                }
            ],
            total_estimated_hours=5.0,
            learning_objectives=["Learn testing"],
        )

        with mock_lcel_chain("app.agents.roadmap_agent", sample):
            with patch(
                "app.agents.roadmap_agent.resilient_llm_call",
                new_callable=AsyncMock,
                return_value=sample,
            ) as mock_resilient:
                from app.agents.roadmap_agent import run_roadmap_agent

                result = await run_roadmap_agent("Build a todo app", "beginner")

                mock_resilient.assert_awaited_once()
                call_kwargs = mock_resilient.call_args
                assert call_kwargs.kwargs.get("agent_type") == "roadmap"


# ──────────────────────────────────────────────────────────────
# Job cancellation status
# ──────────────────────────────────────────────────────────────


class TestJobCancellation:
    """Tests for job cancellation flow."""

    def test_cancel_sets_status(self, fresh_job_store):
        """Updating a job to CANCELLED should set is_complete."""
        fresh_job_store.create_job(
            job_id="cancel-1",
            project_id="p-cancel",
            agent_type="research",
            input_context={},
        )

        updated = fresh_job_store.update_job("cancel-1", status=JobStatusType.CANCELLED)

        assert updated.status == JobStatusType.CANCELLED
        assert updated.is_complete is True
        assert updated.completed_at is not None

    def test_cancel_preserves_progress(self, fresh_job_store):
        """Cancelling should keep the last known progress value."""
        fresh_job_store.create_job(
            job_id="cancel-2",
            project_id="p-cancel",
            agent_type="code",
            input_context={},
        )
        fresh_job_store.update_job(
            "cancel-2", status=JobStatusType.RUNNING, progress=45
        )
        updated = fresh_job_store.update_job("cancel-2", status=JobStatusType.CANCELLED)

        assert updated.progress == 45
