from __future__ import annotations

import asyncio
import logging
import re
import threading
from dataclasses import dataclass
from typing import Any

import httpx
import tenacity

from app.ai_agents.llm_service import (
    DEFAULT_RETRY_CONFIG,
    LLMServiceError,
    LLMTimeoutError,
    ProviderUnavailableError,
)
from app.providers.base import BaseLLMProvider, LLMConfig, ProviderInfo

logger = logging.getLogger(__name__)

_THINK_PATTERN = re.compile(
    r"<think\b[^>]*>.*?(?:</think\s*>|$)",
    re.IGNORECASE | re.DOTALL,
)


def _strip_reasoning(content: str) -> str:
    return _THINK_PATTERN.sub("", content).strip()


def _normalize_messages(messages: Any) -> list[dict[str, str]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if isinstance(messages, dict):
        messages = [messages]

    normalized: list[dict[str, str]] = []
    for message in messages or []:
        if isinstance(message, dict):
            role = str(message.get("role", "user"))
            content = message.get("content", "")
        else:
            role = str(
                getattr(message, "type", None)
                or getattr(message, "role", "user")
            )
            content = getattr(message, "content", message)

        normalized_role = {"human": "user", "ai": "assistant"}.get(
            role.lower(), role
        )
        normalized.append(
            {
                "role": normalized_role,
                "content": content if isinstance(content, str) else str(content),
            }
        )
    return normalized


@dataclass
class _ChatResult:
    content: str


class _OpenAICompatibleChatModel:
    def __init__(self, provider: OpenAICompatibleProvider) -> None:
        self._provider = provider

    def invoke(self, messages: Any, **kwargs: Any) -> _ChatResult:
        result = asyncio.run(self._ainvoke(messages, **kwargs))
        return result

    async def ainvoke(self, messages: Any, **kwargs: Any) -> _ChatResult:
        return await self._ainvoke(messages, **kwargs)

    async def _ainvoke(self, messages: Any, **kwargs: Any) -> _ChatResult:
        result = await self._provider.chat(
            _normalize_messages(messages),
            temperature=kwargs.get("temperature"),
            max_tokens=kwargs.get("max_tokens", kwargs.get("max_output_tokens")),
            timeout=kwargs.get("timeout"),
        )
        return _ChatResult(content=str(result["content"]))


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        config: LLMConfig,
        base_url: str = "http://localhost:1234/v1",
        api_key: str | None = None,
        reasoning_effort: str = "none",
        max_concurrency: int = 1,
        is_local: bool | None = None,
        transport: Any = None,
        retry_wait: float | None = None,
    ) -> None:
        super().__init__(config)
        self.base_url = (base_url or "http://localhost:1234/v1").rstrip("/")
        self.api_key = api_key
        self.reasoning_effort = reasoning_effort
        self.max_concurrency = max(1, max_concurrency)
        self.is_local = (
            is_local if is_local is not None else self._looks_local(self.base_url)
        )
        self._transport = transport
        self._retry_wait = retry_wait
        self._concurrency_guard = threading.BoundedSemaphore(
            self.max_concurrency
        )

    @staticmethod
    def _looks_local(url: str) -> bool:
        return any(
            host in url
            for host in ("localhost", "127.0.0.1", "host.docker.internal")
        )

    def get_chat_model(self) -> Any:
        if self._chat_model is None:
            self._chat_model = _OpenAICompatibleChatModel(self)
        return self._chat_model

    def get_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_name="openai_compatible",
            model_name=self.config.model,
            is_local=self.is_local,
            base_url=self.base_url,
        )

    def health_check(self) -> bool:
        timeout = min(self.config.timeout, 10.0)
        try:
            with httpx.Client(
                transport=self._transport,
                timeout=httpx.Timeout(timeout, connect=min(5.0, timeout)),
            ) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
            return response.status_code == 200
        except Exception:
            logger.debug(
                "OpenAI-compatible health check failed for %s",
                self.base_url,
                exc_info=True,
            )
            return False

    async def chat(
        self,
        messages: list[dict[str, str]] | str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            _normalize_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )

        await asyncio.to_thread(self._concurrency_guard.acquire)
        try:
            retrying = self._build_retryer()
            async for attempt in retrying:
                with attempt:
                    return await self._chat_once(payload, timeout=timeout)
        finally:
            self._concurrency_guard.release()

        raise LLMServiceError("LLM request failed without a response")

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": (
                self.config.temperature if temperature is None else temperature
            ),
            "max_tokens": (
                self.config.max_tokens if max_tokens is None else max_tokens
            ),
        }
        effort = self.reasoning_effort.strip()
        if effort:
            payload["reasoning_effort"] = effort
        return payload

    def _build_retryer(self) -> tenacity.AsyncRetrying:
        wait = (
            tenacity.wait_fixed(self._retry_wait)
            if self._retry_wait is not None
            else DEFAULT_RETRY_CONFIG.wait
        )
        return tenacity.AsyncRetrying(
            wait=wait,
            stop=tenacity.stop_after_attempt(
                max(1, self.config.max_retries + 1)
            ),
            retry=tenacity.retry_if_exception_type(
                (LLMTimeoutError, ProviderUnavailableError)
            ),
            before_sleep=DEFAULT_RETRY_CONFIG.before_sleep,
            reraise=True,
        )

    async def _chat_once(
        self,
        payload: dict[str, Any],
        *,
        timeout: float | None,
    ) -> dict[str, Any]:
        request_timeout = timeout or self.config.timeout
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(
                    request_timeout,
                    connect=min(10.0, request_timeout),
                ),
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"LLM request timed out after {request_timeout:.0f}s"
            ) from exc
        except httpx.TransportError as exc:
            raise ProviderUnavailableError(
                f"LLM server unreachable: {exc}"
            ) from exc

        if response.status_code >= 500:
            raise ProviderUnavailableError(
                f"LLM server returned HTTP {response.status_code}"
            )
        if response.status_code != 200:
            raise LLMServiceError(
                "LLM server returned HTTP "
                f"{response.status_code}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMServiceError("LLM server returned invalid JSON") from exc

        choices = data.get("choices") if isinstance(data, dict) else None
        message = (
            choices[0].get("message")
            if isinstance(choices, list)
            and choices
            and isinstance(choices[0], dict)
            else None
        )
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise LLMServiceError("LLM server returned empty content")

        return {
            "content": _strip_reasoning(content),
            "model": data.get("model", self.config.model),
            "provider": "openai_compatible",
            "usage": data.get("usage", {}),
        }
