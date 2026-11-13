# ============================================================
# PaySentinelIQ — LLM Provider Factory
# Creates the appropriate provider based on settings/configuration.
# DI-compatible: can be overridden in tests.
# ============================================================

from __future__ import annotations

import logging
from enum import Enum
from functools import lru_cache
from typing import Any

from app.providers.base import BaseLLMProvider, LLMConfig
from app.providers.mock import MockLLMProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"
    LMSTUDIO = "lmstudio"
    # Reserved for future providers
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    GROQ = "groq"


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Usage:
        factory = LLMProviderFactory()
        provider = factory.create(ProviderType.OLLAMA, config)

    For FastAPI DI:
        from app.providers import get_llm_provider
        provider = get_llm_provider()
    """

    @staticmethod
    def create(
        provider_type: ProviderType,
        config: LLMConfig,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        """
        Create and return a provider instance.

        Args:
            provider_type: The provider to instantiate.
            config: Standardized LLMConfig for the model.
            **kwargs: Provider-specific arguments (api_key, base_url, etc.).
        """
        if provider_type == ProviderType.OLLAMA:
            from app.providers.ollama import OllamaProvider
            return OllamaProvider(
                config=config,
                base_url=kwargs.get("base_url"),
                num_gpu=kwargs.get("num_gpu"),
                num_thread=kwargs.get("num_thread"),
            )

        if provider_type == ProviderType.OPENAI:
            from app.providers.openai import OpenAIProvider
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return OpenAIProvider(config=config, api_key=api_key)

        if provider_type == ProviderType.GEMINI:
            from app.providers.gemini import GeminiProvider
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
            return GeminiProvider(config=config, api_key=api_key)

        if provider_type == ProviderType.MOCK:
            return MockLLMProvider(config=config, scenario=kwargs.get("scenario", "auto"))

        if provider_type in (
            ProviderType.OPENAI_COMPATIBLE,
            ProviderType.LMSTUDIO,
        ):
            from app.providers.openai_compatible import OpenAICompatibleProvider
            return OpenAICompatibleProvider(
                config=config,
                base_url=kwargs.get("base_url") or "http://localhost:1234/v1",
                api_key=kwargs.get("api_key"),
                reasoning_effort=kwargs.get("reasoning_effort", "none"),
                max_concurrency=kwargs.get("max_concurrency", 1),
            )

        # Reserved for future providers
        if provider_type in (
            ProviderType.ANTHROPIC,
            ProviderType.BEDROCK,
            ProviderType.GROQ,
        ):
            raise NotImplementedError(
                f"Provider '{provider_type.value}' is reserved but not yet implemented."
            )

        raise ValueError(f"Unknown provider type: {provider_type}")


# ── Convenience Functions ──


def _resolve_llm_config() -> LLMConfig:
    """Build LLMConfig from application settings (using effective_* computed fields)."""
    from app.shared.settings import get_settings

    settings = get_settings()

    # Use environment-aware computed fields
    provider = settings.effective_llm_provider
    if provider in ("openai_compatible", "lmstudio"):
        model = settings.LLM_MODEL or settings.effective_ollama_model
        timeout = settings.LLM_TIMEOUT or 120.0
        max_retries = settings.LLM_MAX_RETRIES
    else:
        model = settings.effective_ollama_model if provider == "ollama" else (
            settings.GEMINI_MODEL if provider == "gemini" else
            settings.OPENAI_MODEL if provider == "openai" else
            "mock"
        )
        timeout = settings.OLLAMA_TIMEOUT
        max_retries = settings.OLLAMA_MAX_RETRIES

    return LLMConfig(
        model=model,
        temperature=settings.effective_ai_temperature,
        max_tokens=settings.effective_ai_max_tokens,
        timeout=timeout,
        max_retries=max_retries,
    )


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    """
    Get or create the configured LLM provider (singleton, cached).

    Uses the ENVIRONMENT setting to determine which provider to instantiate:
    - demo → ollama with Qwen3 1.7B (local, zero-cost, fast)
    - development → ollama with Qwen3 4B (local, zero-cost)
    - production → gemini (or explicitly configured provider)
    """
    from app.shared.settings import get_settings

    settings = get_settings()
    provider_type = ProviderType(settings.effective_llm_provider)

    config = _resolve_llm_config()

    extra_kwargs: dict[str, Any] = {}

    if provider_type == ProviderType.OLLAMA:
        extra_kwargs["base_url"] = settings.OLLAMA_BASE_URL
        extra_kwargs["num_gpu"] = settings.effective_ollama_num_gpu
        extra_kwargs["num_thread"] = settings.effective_ollama_num_thread
    elif provider_type == ProviderType.OPENAI:
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'. "
                "Set ENVIRONMENT=demo for mock or ENVIRONMENT=development for ollama."
            )
        extra_kwargs["api_key"] = api_key
    elif provider_type == ProviderType.GEMINI:
        api_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'. "
                "Set ENVIRONMENT=demo for mock or ENVIRONMENT=development for ollama."
            )
        extra_kwargs["api_key"] = api_key
    elif provider_type == ProviderType.MOCK:
        extra_kwargs["scenario"] = "auto"
    elif provider_type in (
        ProviderType.OPENAI_COMPATIBLE,
        ProviderType.LMSTUDIO,
    ):
        extra_kwargs["base_url"] = settings.LLM_BASE_URL
        extra_kwargs["api_key"] = (
            settings.LLM_API_KEY.get_secret_value()
            if settings.LLM_API_KEY
            else None
        )
        extra_kwargs["reasoning_effort"] = settings.LLM_REASONING_EFFORT
        extra_kwargs["max_concurrency"] = settings.LLM_MAX_CONCURRENCY or 1

    provider = LLMProviderFactory.create(provider_type, config, **extra_kwargs)
    logger.info(
        "LLM provider initialized: environment=%s, type=%s, model=%s",
        settings.ENVIRONMENT,
        provider_type.value,
        config.model,
    )
    return provider


def get_llm() -> Any:
    """
    Convenience function: return a ready-to-use LangChain chat model
    from the configured provider. Use this in LangChain chains.
    """
    provider = get_llm_provider()
    return provider.get_chat_model()


def _create_crewai_llm(llm_cls: Any, **kwargs: Any) -> Any:
    """Construct a CrewAI LLM, falling back to None when LiteLLM is absent.

    ``crewai.llm.LLM`` imports LiteLLM lazily inside its constructor. When the
    optional LiteLLM dependency is not installed, construction raises
    ImportError instead of failing at module import time. CrewAI is an optional
    integration, so callers must degrade to the deterministic pipeline rather
    than crash the request.
    """
    try:
        return llm_cls(**kwargs)
    except ImportError:
        logger.warning(
            "CrewAI LLM backend unavailable (LiteLLM fallback not installed) "
            "— using deterministic pipeline"
        )
        return None


@lru_cache
def get_crewai_llm() -> Any:
    """
    Return a CrewAI-compatible LLM object from the configured provider.

    CrewAI 1.14+ does NOT accept raw LangChain ChatModels in the Agent llm field;
    it requires a string model name (LiteLLM format) or a crewai.llm.LLM instance.
    This function wraps the provider configuration into the correct format.

    Returns None if the provider cannot be resolved (graceful fallback),
    including when CrewAI is installed without its LiteLLM backend.
    """
    try:
        from crewai.llm import LLM as CrewAILLM  # noqa: N811
    except ImportError:
        logger.warning("crewai not installed — cannot create CrewAI LLM")
        return None

    from app.shared.settings import get_settings

    settings = get_settings()
    provider_type = settings.effective_llm_provider

    if provider_type == ProviderType.OLLAMA.value:
        return _create_crewai_llm(
            CrewAILLM,
            model=f"ollama/{settings.effective_ollama_model}",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.effective_ai_temperature,
            max_tokens=settings.effective_ai_max_tokens,
            timeout=settings.OLLAMA_TIMEOUT,
        )

    if provider_type == ProviderType.OPENAI.value:
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — cannot create CrewAI LLM for OpenAI")
            return None
        return _create_crewai_llm(
            CrewAILLM,
            model=settings.OPENAI_MODEL,
            api_key=api_key,
            temperature=settings.effective_ai_temperature,
            max_tokens=settings.effective_ai_max_tokens,
        )

    if provider_type == ProviderType.GEMINI.value:
        api_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — cannot create CrewAI LLM for Gemini")
            return None
        # CrewAI LLM uses LiteLLM under the hood;
        # model format for Gemini is "gemini/<model_name>"
        return _create_crewai_llm(
            CrewAILLM,
            model=f"gemini/{settings.GEMINI_MODEL}",
            api_key=api_key,
            temperature=settings.effective_ai_temperature,
            max_tokens=settings.effective_ai_max_tokens,
        )

    if provider_type == ProviderType.MOCK.value:
        return _create_crewai_llm(
            CrewAILLM,
            model="mock/demo",
            temperature=settings.effective_ai_temperature,
            max_tokens=settings.effective_ai_max_tokens,
        )

    if provider_type in (
        ProviderType.OPENAI_COMPATIBLE.value,
        ProviderType.LMSTUDIO.value,
    ):
        api_key = (
            settings.LLM_API_KEY.get_secret_value()
            if settings.LLM_API_KEY
            else "lm-studio"
        )
        model = settings.LLM_MODEL or settings.effective_ollama_model
        return _create_crewai_llm(
            CrewAILLM,
            model=f"openai/{model}",
            base_url=settings.LLM_BASE_URL or "http://localhost:1234/v1",
            api_key=api_key,
            temperature=settings.effective_ai_temperature,
            max_tokens=settings.effective_ai_max_tokens,
            timeout=settings.LLM_TIMEOUT or 120.0,
        )

    logger.warning("Unsupported provider for CrewAI LLM: %s", provider_type)
    return None