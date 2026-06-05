# ============================================================
# PaySentinelIQ — Gemini Provider (Google AI — Cloud LLM)
# Integrates Gemini 2.5 Flash via google-generativeai SDK and
# LangChain's ChatGoogleGenerativeAI for CrewAI compatibility.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

import google.generativeai as genai

from app.providers.base import BaseLLMProvider, LLMConfig, ProviderInfo

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Gemini provider for cloud-based LLM inference via Google AI.

    Uses google.generativeai as the underlying SDK and
    langchain_google_genai.ChatGoogleGenerativeAI as the LangChain integration,
    making it fully compatible with CrewAI and LangChain chains.

    Key features:
    - Cloud-based — no local hardware required
    - Gemini 2.5 Flash for fast, cost-effective inference (default)
    - Google's built-in safety filters
    - Up to 1M token context window (Gemini 2.5 Flash)
    - Automatic retry and rate-limit handling via LangChain wrapper
    """

    def __init__(self, config: LLMConfig, api_key: str) -> None:
        super().__init__(config)
        self.api_key = api_key

        # Configure the google-generativeai SDK globally
        genai.configure(api_key=self.api_key)

    def get_chat_model(self) -> Any:
        """
        Return a LangChain-compatible ChatGoogleGenerativeAI instance.

        This is the primary integration point with CrewAI and LangChain chains.
        The returned model can be used directly in LangChain chains or passed
        to CrewAI agents via CrewAI's LangChain adapter.
        """
        if self._chat_model is not None:
            return self._chat_model

        from langchain_google_genai import ChatGoogleGenerativeAI

        self._chat_model = ChatGoogleGenerativeAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            google_api_key=self.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        logger.info(
            "Gemini chat model initialized: model=%s, max_tokens=%d",
            self.config.model,
            self.config.max_tokens,
        )
        return self._chat_model

    def health_check(self) -> bool:
        """
        Verify the Gemini API key is valid and the target model is accessible.

        Uses the google-generativeai SDK to list available models.
        This is a lightweight call that does not consume tokens.
        """
        try:
            # List available models via the SDK — validates API key + network
            models = genai.list_models()
            available_models = [m.name for m in models]

            # Normalise model name for matching
            # API returns names like "models/gemini-2.5-flash"
            # User may provide "gemini-2.5-flash" or "models/gemini-2.5-flash"
            search_name = (
                self.config.model
                if self.config.model.startswith("models/")
                else f"models/{self.config.model}"
            )

            is_available = any(search_name in m for m in available_models)

            if not is_available:
                logger.warning(
                    "Gemini model '%s' not found. Available models: %s",
                    self.config.model,
                    [m.replace("models/", "") for m in available_models],
                )
                return False

            logger.info(
                "Gemini health check passed: model=%s",
                self.config.model,
            )
            return True

        except Exception as e:
            logger.error("Gemini health check failed: %s", e)
            return False

    def get_info(self) -> ProviderInfo:
        """Return metadata about this Gemini provider instance."""
        return ProviderInfo(
            provider_name="gemini",
            model_name=self.config.model,
            is_local=False,
            base_url="https://generativelanguage.googleapis.com",
        )
