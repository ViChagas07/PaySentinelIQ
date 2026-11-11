import asyncio
import json

import httpx
import pytest

from app.providers.base import LLMConfig
from app.providers.factory import LLMProviderFactory, ProviderType
from app.providers.openai_compatible import OpenAICompatibleProvider


def _make_provider(
    handler,
    *,
    api_key=None,
    reasoning_effort="none",
    max_concurrency=1,
    max_retries=0,
    retry_wait=0.0,
):
    config = LLMConfig(
        model="qwen3.5-4b@q4_k_m",
        temperature=0.2,
        max_tokens=128,
        timeout=5.0,
        max_retries=max_retries,
    )
    return OpenAICompatibleProvider(
        config=config,
        base_url="http://lmstudio.test/v1",
        api_key=api_key,
        reasoning_effort=reasoning_effort,
        max_concurrency=max_concurrency,
        transport=httpx.MockTransport(handler),
        retry_wait=retry_wait,
    )


def _completion(content, status_code=200):
    return httpx.Response(
        status_code,
        json={
            "model": "qwen3.5-4b@q4_k_m",
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
    )


@pytest.mark.asyncio
async def test_payload_and_authorization_header():
    requests = []

    def handler(request):
        requests.append(request)
        return _completion("answer")

    provider = _make_provider(handler, api_key="secret-key")

    result = await provider.chat(
        [{"role": "user", "content": "hello"}],
        temperature=0.0,
        max_tokens=64,
    )

    payload = json.loads(requests[0].content)
    assert requests[0].method == "POST"
    assert str(requests[0].url) == "http://lmstudio.test/v1/chat/completions"
    assert payload["model"] == "qwen3.5-4b@q4_k_m"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 64
    assert payload["reasoning_effort"] == "none"
    assert requests[0].headers["authorization"] == "Bearer secret-key"
    assert result["content"] == "answer"
    assert result["provider"] == "openai_compatible"


@pytest.mark.asyncio
async def test_no_authorization_header_without_api_key():
    requests = []

    def handler(request):
        requests.append(request)
        return _completion("answer")

    provider = _make_provider(handler, api_key=None)

    await provider.chat([{"role": "user", "content": "hello"}])

    assert "authorization" not in requests[0].headers


@pytest.mark.asyncio
async def test_reasoning_effort_is_configurable():
    requests = []

    def handler(request):
        requests.append(request)
        return _completion("answer")

    provider = _make_provider(handler, reasoning_effort="high")

    await provider.chat([{"role": "user", "content": "hello"}])

    payload = json.loads(requests[0].content)
    assert payload["reasoning_effort"] == "high"


@pytest.mark.asyncio
async def test_strips_closed_think_block():
    provider = _make_provider(
        lambda request: _completion("before<think>hidden</think>after")
    )

    result = await provider.chat([{"role": "user", "content": "hello"}])

    assert result["content"] == "beforeafter"


@pytest.mark.asyncio
async def test_strips_unclosed_think_block():
    provider = _make_provider(
        lambda request: _completion("before<think>hidden forever")
    )

    result = await provider.chat([{"role": "user", "content": "hello"}])

    assert result["content"] == "before"


def test_health_check_true():
    def handler(request):
        assert request.method == "GET"
        assert str(request.url) == "http://lmstudio.test/v1/models"
        return httpx.Response(200, json={"data": []})

    provider = _make_provider(handler)

    assert provider.health_check() is True


def test_health_check_false():
    provider = _make_provider(
        lambda request: httpx.Response(503, text="unavailable")
    )

    assert provider.health_check() is False


@pytest.mark.asyncio
async def test_retries_on_server_error():
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(500, text="temporary")
        return _completion("recovered")

    provider = _make_provider(handler, max_retries=2)

    result = await provider.chat([{"role": "user", "content": "hello"}])

    assert attempts == 3
    assert result["content"] == "recovered"


@pytest.mark.asyncio
async def test_retries_on_timeout():
    attempts = 0

    async def handler(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("timed out", request=request)
        return _completion("after-timeout")

    provider = _make_provider(handler, max_retries=1)

    result = await provider.chat([{"role": "user", "content": "hello"}])

    assert attempts == 2
    assert result["content"] == "after-timeout"


@pytest.mark.asyncio
async def test_semaphore_serializes_when_max_concurrency_is_one():
    active = 0
    max_active = 0

    async def handler(request):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.05)
        active -= 1
        return _completion("ok")

    provider = _make_provider(handler, max_concurrency=1)

    await asyncio.gather(
        provider.chat([{"role": "user", "content": "one"}]),
        provider.chat([{"role": "user", "content": "two"}]),
    )

    assert max_active == 1


def test_chat_model_adapter_invoke_returns_content():
    provider = _make_provider(lambda request: _completion("adapter"))
    model = provider.get_chat_model()

    result = model.invoke([{"role": "user", "content": "hello"}])

    assert result.content == "adapter"


def test_factory_registers_provider_and_alias():
    config = LLMConfig(model="qwen3.5-4b@q4_k_m")

    provider = LLMProviderFactory.create(ProviderType.OPENAI_COMPATIBLE, config)
    alias_provider = LLMProviderFactory.create(ProviderType.LMSTUDIO, config)

    assert provider.get_info().provider_name == "openai_compatible"
    assert alias_provider.get_info().provider_name == "openai_compatible"
