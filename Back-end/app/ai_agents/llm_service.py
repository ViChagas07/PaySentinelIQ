# ============================================================
# PaySentinelIQ — LLM Service (Production-Grade)
# Wraps provider abstraction with retry, timeout, fallback,
# health checks, and async support for FastAPI.
# ============================================================

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import tenacity

from app.providers.base import BaseLLMProvider
from app.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)


# ── Custom Exceptions ──


class LLMServiceError(Exception):
    """Base exception for LLM service failures."""


class ProviderUnavailableError(LLMServiceError):
    """Raised when the LLM provider is unreachable."""


class ModelNotAvailableError(LLMServiceError):
    """Raised when the requested model is not available."""


class LLMTimeoutError(LLMServiceError):
    """Raised when an LLM call exceeds the configured timeout."""


class LLMMaxRetriesExceededError(LLMServiceError):
    """Raised when all retry attempts have been exhausted."""


# ── Retry Configuration ──


def _default_before_sleep(retry_state: tenacity.RetryCallState) -> None:
    """Log retry attempts with backoff information."""
    attempt = retry_state.attempt_number
    wait = retry_state.next_action.sleep if retry_state.next_action else 0
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "LLM call retry %d/%d after %.1fs — error: %s",
        attempt,
        attempt + 1 if attempt < 5 else attempt,  # approximate
        wait,
        exc,
    )


DEFAULT_RETRY_CONFIG = tenacity.Retrying(
    wait=tenacity.wait_exponential(
        multiplier=1.0,
        min=1.0,
        max=30.0,
    ),
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(
        (ConnectionError, TimeoutError, OSError, LLMTimeoutError)
    ),
    before_sleep=_default_before_sleep,
    reraise=True,
)


# ── LLM Service ──


@dataclass
class LLMService:
    """
    Production-grade LLM service with full resilience patterns.

    Features:
    - Provider abstraction via BaseLLMProvider
    - Automatic retry with exponential backoff
    - Health checks before first use
    - Timeout enforcement
    - Graceful degradation (optional fallback chain)
    - Async-compatible for FastAPI
    - Structured logging at all levels
    - Metrics-friendly (timing, error rates)

    Usage (FastAPI DI):
        from app.ai_agents.llm_service import LLMService
        llm_service = LLMService()
        await llm_service.initialize()
    """

    provider: BaseLLMProvider = field(default_factory=get_llm_provider)
    fallback_provider: BaseLLMProvider | None = None
    _initialized: bool = field(default=False, init=False)
    _health_status: bool = field(default=False, init=False)
    _last_health_check: float = field(default=0.0, init=False)
    _health_check_interval: float = field(default=60.0, init=False)

    async def initialize(self) -> None:
        """
        Initialize the service: validate provider connectivity and model availability.
        Should be called once at application startup.
        """
        if self._initialized:
            return

        logger.info("Initializing LLM service: provider=%s", self.provider.get_info().provider_name)

        is_healthy = await self._run_health_check()
        if not is_healthy:
            if self.fallback_provider:
                logger.warning(
                    "Primary provider unhealthy, switching to fallback: %s",
                    self.fallback_provider.get_info().provider_name,
                )
                self.provider = self.fallback_provider
                is_healthy = await self._run_health_check()

            if not is_healthy:
                raise ProviderUnavailableError(
                    f"LLM provider '{self.provider.get_info().provider_name}' is not available. "
                    f"Ensure Ollama is running ('ollama serve') and model '{self.provider.config.model}' "
                    f"is pulled ('ollama pull {self.provider.config.model}')."
                )

        self._initialized = True
        self._health_status = True
        self._last_health_check = time.monotonic()
        provider_info = self.provider.get_info()
        logger.info(
            "LLM service ready: provider=%s, model=%s, local=%s",
            provider_info.provider_name,
            provider_info.model_name,
            provider_info.is_local,
        )

    async def _run_health_check(self) -> bool:
        """Execute health check in a thread to avoid blocking the event loop."""
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self.provider.health_check),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.error("Health check timed out for %s", self.provider.get_info().provider_name)
            return False
        except Exception as e:
            logger.error("Health check error: %s", e)
            return False

    async def ensure_healthy(self) -> None:
        """Verify the provider is still healthy (with caching to avoid excessive checks)."""
        now = time.monotonic()
        if (now - self._last_health_check) > self._health_check_interval:
            self._health_status = await self._run_health_check()
            self._last_health_check = now
        if not self._health_status:
            raise ProviderUnavailableError(
                f"LLM provider '{self.provider.get_info().provider_name}' is unhealthy."
            )

    def get_chat_model(self) -> Any:
        """
        Return the LangChain-compatible chat model for CrewAI/LangChain usage.
        Call initialize() first, or this will lazily health-check.
        """
        if not self._initialized:
            logger.warning("LLMService.get_chat_model() called before initialize() — checking health lazily")
            if not self.provider.health_check():
                raise ProviderUnavailableError(
                    f"LLM provider '{self.provider.get_info().provider_name}' is not available."
                )
            self._initialized = True
            self._health_status = True

        return self.provider.get_chat_model()

    async def invoke_with_retry(
        self,
        invoke_fn: Callable[[], Any],
        max_retries: int | None = None,
        timeout: float | None = None,
    ) -> Any:
        """
        Execute an LLM invocation with retry and timeout.

        Args:
            invoke_fn: A callable that invokes the LLM (e.g., crew.kickoff).
            max_retries: Override the default retry count.
            timeout: Override the default timeout.

        Returns:
            The result from invoke_fn().

        Raises:
            LLMTimeoutError: If the call exceeds the timeout.
            LLMMaxRetriesExceededError: If all retries are exhausted.
        """
        await self.ensure_healthy()

        effective_timeout = timeout or self.provider.config.timeout
        effective_retries = max_retries or self.provider.config.max_retries

        retryer = DEFAULT_RETRY_CONFIG.copy(
            stop=tenacity.stop_after_attempt(effective_retries + 1),
        )

        loop = asyncio.get_running_loop()

        @retryer.wraps
        def _wrapped() -> Any:
            return invoke_fn()

        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _wrapped),
                timeout=effective_timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                "LLM invocation timed out after %.1fs (provider=%s, model=%s)",
                effective_timeout,
                self.provider.get_info().provider_name,
                self.provider.config.model,
            )
            raise LLMTimeoutError(
                f"LLM call timed out after {effective_timeout:.0f}s with "
                f"provider '{self.provider.get_info().provider_name}'"
            )
        except tenacity.RetryError as e:
            logger.error("LLM invocation failed after %d retries: %s", effective_retries, e)
            raise LLMMaxRetriesExceededError(
                f"LLM call failed after {effective_retries} retries: {e}"
            )
        except Exception as e:
            logger.error("LLM invocation unexpected error: %s", e)
            raise LLMServiceError(f"LLM invocation failed: {e}") from e

    def get_info(self) -> dict[str, Any]:
        """Return service diagnostics for monitoring."""
        pinfo = self.provider.get_info()
        return {
            "provider": pinfo.provider_name,
            "model": pinfo.model_name,
            "is_local": pinfo.is_local,
            "base_url": pinfo.base_url,
            "initialized": self._initialized,
            "healthy": self._health_status,
            "temperature": self.provider.config.temperature,
            "max_tokens": self.provider.config.max_tokens,
            "timeout": self.provider.config.timeout,
            "max_retries": self.provider.config.max_retries,
        }

    def invalidate(self) -> None:
        """Reset the service state (useful after config changes)."""
        self._initialized = False
        self._health_status = False
        self._last_health_check = 0.0
        self.provider.invalidate_cache()


# ── Singleton / DI Helpers ──

_llm_service_instance: LLMService | None = None


async def get_llm_service() -> LLMService:
    """
    FastAPI dependency: get or create the LLM service singleton.

    Usage:
        from fastapi import Depends
        from app.ai_agents.llm_service import get_llm_service

        @router.post("/analyze")
        async def analyze(service: LLMService = Depends(get_llm_service)):
            model = service.get_chat_model()
            ...
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
        await _llm_service_instance.initialize()
    return _llm_service_instance


def reset_llm_service() -> None:
    """Reset the singleton (useful for testing or config changes)."""
    global _llm_service_instance
    if _llm_service_instance:
        _llm_service_instance.invalidate()
    _llm_service_instance = None
