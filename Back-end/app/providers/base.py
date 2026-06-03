# ============================================================
# PaySentinelIQ — Base LLM Provider (Abstract)
# All providers MUST implement this interface.
# ============================================================

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for any LLM provider."""

    model: str = "llama3"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: float = 120.0
    max_retries: int = 3
    streaming: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    """Metadata about the provider for diagnostics and monitoring."""

    provider_name: str
    model_name: str
    is_local: bool
    base_url: str | None = None


class BaseLLMProvider(ABC):
    """
    Abstract base for all LLM providers.

    Every provider must:
    1. Accept a standard LLMConfig
    2. Return a LangChain-compatible chat model via get_chat_model()
    3. Expose health_check() for connectivity validation
    4. Expose provider info via get_info()
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._chat_model: Any = None

    @abstractmethod
    def get_chat_model(self) -> Any:
        """
        Return a LangChain-compatible BaseChatModel instance.

        This is the primary integration point with CrewAI and LangChain chains.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify the provider is reachable and the model is available.

        Returns True if healthy, False otherwise.
        """
        ...

    @abstractmethod
    def get_info(self) -> ProviderInfo:
        """Return metadata about this provider instance."""
        ...

    def invalidate_cache(self) -> None:
        """Reset cached chat model instance (e.g., after config changes)."""
        self._chat_model = None
        logger.debug("Provider cache invalidated for %s", self.get_info().provider_name)
