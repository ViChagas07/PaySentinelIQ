# ============================================================
# PaySentinelIQ — Ollama Provider (Local LLM)
# Integrates Ollama running locally with LangChain + CrewAI.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.providers.base import BaseLLMProvider, LLMConfig, ProviderInfo

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference via http://localhost:11434.

    Uses langchain_community.chat_models.ChatOllama as the LangChain integration,
    falling back to langchain_ollama.ChatOllama if available (newer official package).

    Key features:
    - Zero API costs — fully local
    - No internet required
    - Full data privacy
    - GPU-accelerated when available
    - Model caching via Ollama daemon
    """

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        config: LLMConfig,
        base_url: str | None = None,
        num_gpu: int | None = None,
        num_thread: int | None = None,
    ) -> None:
        super().__init__(config)
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.num_gpu = num_gpu
        self.num_thread = num_thread

    def get_chat_model(self) -> Any:
        """Return a LangChain-compatible ChatOllama instance."""
        if self._chat_model is not None:
            return self._chat_model

        # Prefer the newer official langchain_ollama package if available
        chat_ollama_cls: Any
        try:
            from langchain_ollama import ChatOllama as _OfficialChatOllama

            chat_ollama_cls = _OfficialChatOllama
            logger.info("Using langchain_ollama.ChatOllama (official package)")
        except ImportError:
            from langchain_community.chat_models import ChatOllama as _FallbackChatOllama

            chat_ollama_cls = _FallbackChatOllama
            logger.info("Using langchain_community.chat_models.ChatOllama (fallback)")

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "base_url": self.base_url,
        }

        # Optional performance tuning parameters
        if self.config.max_tokens > 0:
            kwargs["num_predict"] = self.config.max_tokens

        if self.num_gpu is not None:
            kwargs["num_gpu"] = self.num_gpu

        if self.num_thread is not None:
            kwargs["num_thread"] = self.num_thread

        # Timeout for streaming (non-streaming handled by httpx adapter)
        kwargs["timeout"] = self.config.timeout

        self._chat_model = chat_ollama_cls(**kwargs)
        logger.info(
            "Ollama chat model initialized: model=%s, base_url=%s",
            self.config.model,
            self.base_url,
        )
        return self._chat_model

    def health_check(self) -> bool:
        """
        Verify Ollama is reachable and the target model is available.

        Uses Ollama's /api/tags endpoint to check model availability.
        Falls back to a simple GET on /api/version for daemon liveness.
        """
        try:
            client = httpx.Client(timeout=10.0)
            # First, check if Ollama daemon is running
            resp = client.get(f"{self.base_url}/api/version")
            if resp.status_code != 200:
                logger.warning("Ollama daemon not reachable at %s", self.base_url)
                return False

            version_info = resp.json()
            logger.debug("Ollama version: %s", version_info.get("version", "unknown"))

            # Then check if the specific model is available
            tags_resp = client.get(f"{self.base_url}/api/tags")
            if tags_resp.status_code != 200:
                logger.warning("Could not query Ollama model list")
                return False

            models_data = tags_resp.json()
            available_models = [m.get("name", "") for m in models_data.get("models", [])]

            # Match model name (handles tags like "llama3:latest", "llama3:8b", etc.)
            model_base = self.config.model.split(":")[0]
            is_available = any(
                m == self.config.model or m.startswith(f"{model_base}:") for m in available_models
            )

            if not is_available:
                logger.warning(
                    "Model '%s' not found in Ollama. Available: %s",
                    self.config.model,
                    available_models,
                )
                return False

            logger.info("Ollama health check passed: model=%s", self.config.model)
            return True

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s — daemon not running?", self.base_url)
            return False
        except Exception as e:
            logger.error("Ollama health check failed: %s", e)
            return False

    def get_info(self) -> ProviderInfo:
        """Return metadata about this Ollama provider."""
        return ProviderInfo(
            provider_name="ollama",
            model_name=self.config.model,
            is_local=True,
            base_url=self.base_url,
        )
