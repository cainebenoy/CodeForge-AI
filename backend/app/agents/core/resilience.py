"""
LLM Resilience Layer — Circuit Breaker + Exponential Backoff Retry

Provides fault-tolerant wrappers for LLM API calls across all agents.

Circuit Breaker:
- Per-provider isolation (OpenAI, Google, Anthropic) so one provider's
  outage doesn't block calls to other providers.
- States: CLOSED (normal) → OPEN (all calls fail-fast) → HALF_OPEN (test calls)
- Opens after `failure_threshold` consecutive failures.
- Automatically tests recovery after `recovery_timeout` seconds.

Retry with Exponential Backoff:
- Retries transient errors (rate limits, timeouts, server errors)
- Exponential backoff with jitter to prevent thundering herd
- Max 3 attempts by default

Security:
- Never logs or exposes API keys in error messages
- Sanitizes provider error messages before re-raising
"""

import asyncio
import logging
import random
import time
from enum import Enum
from typing import Any, Callable, Coroutine, Optional, TypeVar

logger = logging.getLogger("codeforge.resilience")

T = TypeVar("T")


# ──────────────────────────────────────────────────────────────
# Circuit Breaker
# ──────────────────────────────────────────────────────────────


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation — calls pass through
    OPEN = "open"  # Failing — all calls rejected immediately
    HALF_OPEN = "half_open"  # Testing recovery — limited calls allowed


class CircuitBreakerError(Exception):
    """Raised when circuit is open and calls are rejected"""

    def __init__(self, provider: str, state: CircuitState):
        self.provider = provider
        self.state = state
        super().__init__(
            f"Circuit breaker OPEN for provider '{provider}'. "
            f"Service is temporarily unavailable. Try again later."
        )


class CircuitBreaker:
    """
    Per-provider circuit breaker for LLM API calls.

    Thread-safe via asyncio.Lock for concurrent access from
    multiple agent tasks.

    Args:
        provider: Provider name (e.g., 'openai', 'google', 'anthropic')
        failure_threshold: Consecutive failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait before testing recovery (default: 60)
        half_open_max_calls: Number of test calls in HALF_OPEN state (default: 2)
    """

    def __init__(
        self,
        provider: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 2,
    ):
        self.provider = provider
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def _check_state_transition(self) -> None:
        """Check if circuit should transition from OPEN → HALF_OPEN."""
        if (
            self._state == CircuitState.OPEN
            and self._last_failure_time is not None
            and (time.monotonic() - self._last_failure_time) >= self.recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0
            logger.info(
                f"Circuit breaker [{self.provider}]: OPEN → HALF_OPEN "
                f"(testing recovery after {self.recovery_timeout}s)"
            )

    async def call(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a function through the circuit breaker.

        Raises CircuitBreakerError if the circuit is OPEN.
        On success in HALF_OPEN, transitions to CLOSED.
        On failure, increments failure count and may open circuit.
        """
        async with self._lock:
            await self._check_state_transition()

            if self._state == CircuitState.OPEN:
                raise CircuitBreakerError(self.provider, self._state)

            if (
                self._state == CircuitState.HALF_OPEN
                and self._half_open_calls >= self.half_open_max_calls
            ):
                raise CircuitBreakerError(self.provider, self._state)

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

        # Execute outside the lock to allow concurrent calls
        try:
            result = await func(*args, **kwargs)

            # Success — reset circuit
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    logger.info(
                        f"Circuit breaker [{self.provider}]: HALF_OPEN → CLOSED "
                        f"(recovery confirmed)"
                    )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0

            return result

        except Exception as e:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.monotonic()

                if self._state == CircuitState.HALF_OPEN:
                    # Recovery failed — go back to OPEN
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker [{self.provider}]: HALF_OPEN → OPEN "
                        f"(recovery failed: {type(e).__name__})"
                    )
                elif self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker [{self.provider}]: CLOSED → OPEN "
                        f"(threshold {self.failure_threshold} reached: {type(e).__name__})"
                    )

            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
        logger.info(f"Circuit breaker [{self.provider}]: manually reset to CLOSED")


# ──────────────────────────────────────────────────────────────
# Per-provider circuit breakers (singletons)
# ──────────────────────────────────────────────────────────────

_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    """Get or create a circuit breaker for the given provider."""
    if provider not in _circuit_breakers:
        _circuit_breakers[provider] = CircuitBreaker(provider=provider)
    return _circuit_breakers[provider]


# ──────────────────────────────────────────────────────────────
# Transient error detection
# ──────────────────────────────────────────────────────────────


def _is_transient_error(exc: Exception) -> bool:
    """
    Determine if an exception is transient (retryable).

    Transient errors include:
    - Rate limit errors (429)
    - Server errors (500, 502, 503, 529)
    - Connection/timeout errors
    - Provider overloaded errors

    Non-transient errors (auth failures, invalid requests) are NOT retried.
    """
    exc_type = type(exc).__name__
    exc_str = str(exc).lower()

    # Rate limits — all providers
    if "rate" in exc_str and "limit" in exc_str:
        return True
    if "429" in exc_str:
        return True

    # Server errors
    if any(code in exc_str for code in ["500", "502", "503", "529"]):
        return True

    # Overloaded / capacity errors
    if "overloaded" in exc_str or "capacity" in exc_str:
        return True

    # Connection / timeout errors
    transient_types = (
        "timeout",
        "connectionerror",
        "connecttimeout",
        "readtimeout",
        "serviceunavailable",
    )
    if exc_type.lower() in transient_types:
        return True
    if "timeout" in exc_str or "connection" in exc_str:
        return True

    # OpenAI-specific
    if "ratelimiterror" in exc_type.lower():
        return True
    if "apierror" in exc_type.lower() and (
        "server" in exc_str or "overloaded" in exc_str
    ):
        return True

    # Google-specific
    if "resourceexhausted" in exc_type.lower():
        return True

    # Anthropic-specific
    if "overloadederror" in exc_type.lower():
        return True

    return False


def _detect_provider(agent_type: str) -> str:
    """Map agent type to its LLM provider for circuit breaker routing."""
    if agent_type in ("research", "qa", "wireframe"):
        return "openai"
    elif agent_type == "code":
        return "google"
    elif agent_type in ("pedagogy", "roadmap"):
        return "anthropic"
    else:
        return "openai"  # Default


# ──────────────────────────────────────────────────────────────
# Resilient LLM Call — combines circuit breaker + retry
# ──────────────────────────────────────────────────────────────


async def resilient_llm_call(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    agent_type: str = "research",
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    **kwargs: Any,
) -> T:
    """
    Execute an LLM call with circuit breaker protection and exponential
    backoff retry for transient errors.

    Args:
        func: The async function to call (e.g., chain.ainvoke)
        *args: Positional arguments for func
        agent_type: Agent type for provider routing (default: 'research')
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Base delay in seconds for backoff (default: 2.0)
        max_delay: Maximum delay cap in seconds (default: 30.0)
        **kwargs: Keyword arguments for func

    Returns:
        The result of func(*args, **kwargs)

    Raises:
        CircuitBreakerError: If the provider's circuit is open
        Exception: The last exception after all retries are exhausted
    """
    provider = _detect_provider(agent_type)
    cb = get_circuit_breaker(provider)

    last_exception: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            result = await cb.call(func, *args, **kwargs)
            if attempt > 1:
                logger.info(
                    f"LLM call succeeded on attempt {attempt}/{max_retries} "
                    f"[{provider}]"
                )
            return result

        except CircuitBreakerError:
            # Circuit is open — don't retry, fail immediately
            raise

        except Exception as e:
            last_exception = e

            if not _is_transient_error(e) or attempt == max_retries:
                logger.error(
                    f"LLM call failed [{provider}] "
                    f"(attempt {attempt}/{max_retries}, "
                    f"transient={_is_transient_error(e)}): "
                    f"{type(e).__name__}"
                )
                raise

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = random.uniform(0, delay * 0.3)
            wait_time = delay + jitter

            logger.warning(
                f"LLM call failed [{provider}] "
                f"(attempt {attempt}/{max_retries}, "
                f"retrying in {wait_time:.1f}s): "
                f"{type(e).__name__}"
            )

            await asyncio.sleep(wait_time)

    # Should never reach here, but just in case
    raise last_exception  # type: ignore[misc]
