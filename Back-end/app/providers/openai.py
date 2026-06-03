# ============================================================
# PaySentinelIQ — OpenAI Provider (Cloud LLM)
# Kept for backward compatibility and future multi-provider support.
# Now optional — Ollama is the default for zero-cost inference.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.providers.base import BaseLLMProvider, LLMConfig, ProviderInfo

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider for cloud-based LLM inference.

    Uses langchain_openai.ChatOpenAI as the LangChain integration.
    Requires OPENAI_API_KEY to be set.

    Now secondary to Ollama for the default deployment. Use only when
    cloud inference is explicitly required (e.g., fallback, specific models).
    """

    def __init__(self, config: LLMConfig, api_key: str) -> None:
        super().__init__(config)
        self.api_key = api_key

    def get_chat_model(self) -> Any:
        """Return a LangChain-compatible ChatOpenAI instance."""
        if self._chat_model is not None:
            return self._chat_model

        from langchain_openai import ChatOpenAI  # type: ignore[import-untyped]

        self._chat_model = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        logger.info("OpenAI chat model initialized: model=%s", self.config.model)
        return self._chat_model

    def health_check(self) -> bool:
        """
        Verify OpenAI API key is valid by calling the models endpoint.
        Uses a lightweight API call to avoid unnecessary token costs.
        """
        try:
            client = httpx.Client(timeout=15.0)
            resp = client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                models_data = resp.json()
                model_ids = [m.get("id", "") for m in models_data.get("data", [])]
                is_available = self.config.model in model_ids
                if not is_available:
                    logger.warning("OpenAI model '%s' not in available models", self.config.model)
                logger.info("OpenAI health check: status=%s, model_available=%s", resp.status_code, is_available)
                return is_available
            else:
                logger.warning("OpenAI health check failed: HTTP %s", resp.status_code)
                return False
        except Exception as e:
            logger.error("OpenAI health check error: %s", e)
            return False

    def get_info(self) -> ProviderInfo:
        """Return metadata about this OpenAI provider."""
        return ProviderInfo(
            provider_name="openai",
            model_name=self.config.model,
            is_local=False,
            base_url="https://api.openai.com/v1",
        )
