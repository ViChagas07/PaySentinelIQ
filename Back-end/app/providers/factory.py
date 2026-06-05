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
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    # Reserved for future providers
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    GROQ = "groq"
    GEMINI = "gemini"


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
            return OllamaProvider(
                config=config,
                base_url=kwargs.get("base_url"),
                num_gpu=kwargs.get("num_gpu"),
                num_thread=kwargs.get("num_thread"),
            )

        if provider_type == ProviderType.OPENAI:
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return OpenAIProvider(config=config, api_key=api_key)

        if provider_type == ProviderType.GEMINI:
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
            return GeminiProvider(config=config, api_key=api_key)

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
    """Build LLMConfig from application settings."""
    from app.shared.settings import get_settings

    settings = get_settings()
    provider = settings.LLM_PROVIDER

    # Determine which model to use based on the active provider
    if provider == ProviderType.OLLAMA.value:
        model = settings.OLLAMA_MODEL
    elif provider == ProviderType.GEMINI.value:
        model = settings.GEMINI_MODEL
    elif provider == ProviderType.OPENAI.value:
        model = settings.OPENAI_MODEL
    else:
        model = settings.OLLAMA_MODEL  # sensible fallback

    return LLMConfig(
        model=model,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
        timeout=settings.OLLAMA_TIMEOUT,
        max_retries=settings.OLLAMA_MAX_RETRIES,
    )


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    """
    Get or create the configured LLM provider (singleton, cached).

    Uses the LLM_PROVIDER setting to determine which provider to instantiate.
    Defaults to Ollama for zero-cost local inference.
    """
    from app.shared.settings import get_settings

    settings = get_settings()
    provider_type = ProviderType(settings.LLM_PROVIDER)

    config = _resolve_llm_config()

    extra_kwargs: dict[str, Any] = {}

    if provider_type == ProviderType.OLLAMA:
        extra_kwargs["base_url"] = settings.OLLAMA_BASE_URL
        if settings.OLLAMA_NUM_GPU is not None:
            extra_kwargs["num_gpu"] = settings.OLLAMA_NUM_GPU
        if settings.OLLAMA_NUM_THREAD is not None:
            extra_kwargs["num_thread"] = settings.OLLAMA_NUM_THREAD
    elif provider_type == ProviderType.OPENAI:
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'. "
                "Set LLM_PROVIDER=ollama for local inference."
            )
        extra_kwargs["api_key"] = api_key
    elif provider_type == ProviderType.GEMINI:
        api_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'. "
                "Set LLM_PROVIDER=ollama for local inference."
            )
        extra_kwargs["api_key"] = api_key

    provider = LLMProviderFactory.create(provider_type, config, **extra_kwargs)
    logger.info(
        "LLM provider initialized: type=%s, model=%s",
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


@lru_cache
def get_crewai_llm() -> Any:
    """
    Return a CrewAI-compatible LLM object from the configured provider.

    CrewAI 1.14+ does NOT accept raw LangChain ChatModels in the Agent llm field;
    it requires a string model name (LiteLLM format) or a crewai.llm.LLM instance.
    This function wraps the provider configuration into the correct format.

    Returns None if the provider cannot be resolved (graceful fallback).
    """
    try:
        from crewai.llm import LLM as CrewAILLM  # noqa: N811
    except ImportError:
        logger.warning("crewai not installed — cannot create CrewAI LLM")
        return None

    from app.shared.settings import get_settings

    settings = get_settings()
    provider_type = settings.LLM_PROVIDER

    if provider_type == ProviderType.OLLAMA.value:
        return CrewAILLM(
            model=f"ollama/{settings.OLLAMA_MODEL}",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
            timeout=settings.OLLAMA_TIMEOUT,
        )

    if provider_type == ProviderType.OPENAI.value:
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — cannot create CrewAI LLM for OpenAI")
            return None
        return CrewAILLM(
            model=settings.OPENAI_MODEL,
            api_key=api_key,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )

    if provider_type == ProviderType.GEMINI.value:
        api_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — cannot create CrewAI LLM for Gemini")
            return None
        # CrewAI LLM uses LiteLLM under the hood;
        # model format for Gemini is "gemini/<model_name>"
        return CrewAILLM(
            model=f"gemini/{settings.GEMINI_MODEL}",
            api_key=api_key,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )

    logger.warning("Unsupported provider for CrewAI LLM: %s", provider_type)
    return None
