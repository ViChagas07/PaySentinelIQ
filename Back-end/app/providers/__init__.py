# ============================================================
# PaySentinelIQ — LLM Provider Abstraction Layer
# Supports: Ollama (local), OpenAI, Anthropic, AWS Bedrock, Groq, Gemini, Mock
# ============================================================

# Base and factory are always available
from app.providers.base import BaseLLMProvider
from app.providers.factory import LLMProviderFactory, get_crewai_llm, get_llm, get_llm_provider

# Concrete providers are imported lazily in factory to avoid mandatory dependencies
# Import here only for type hints / isinstance checks if needed
# from app.providers.gemini import GeminiProvider
# from app.providers.ollama import OllamaProvider
# from app.providers.openai import OpenAIProvider
# from app.providers.mock import MockLLMProvider

__all__ = [
    "BaseLLMProvider",
    "LLMProviderFactory",
    "get_llm_provider",
    "get_llm",
    "get_crewai_llm",
]
