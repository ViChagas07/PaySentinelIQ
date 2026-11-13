"""Canary regression tests for residual logging/response sanitization.

Each canary is synthetic and must never reach formatted logs or API responses.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.main import create_app
from app.shared.settings import Settings

CANARY_CREDENTIAL = "AKIA-RESIDUAL-CANARY-CREDENTIAL-7D2E"
CANARY_ENDPOINT = "https://residual-canary.invalid.internal"
CANARY_KEY = "receipts/residual-canary-tenant/residual-canary.pdf"
CANARY_FILE_NAME = "residual-canary-secret-file.pdf"
CANARY_SQL = "SELECT password_hash FROM residual_canary_users WHERE token='canary'"
CANARY_MESSAGE = (
    f"credential={CANARY_CREDENTIAL}; endpoint={CANARY_ENDPOINT}; "
    f"key={CANARY_KEY}; file_name={CANARY_FILE_NAME}; sql={CANARY_SQL}"
)
CANARIES = (
    CANARY_CREDENTIAL,
    CANARY_ENDPOINT,
    CANARY_KEY,
    CANARY_FILE_NAME,
    CANARY_SQL,
)


def _assert_no_canaries(*texts: str) -> None:
    for text in texts:
        for canary in CANARIES:
            assert canary not in text


def _assert_no_traceback(caplog: pytest.LogCaptureFixture) -> None:
    for record in caplog.records:
        assert record.exc_info is None
        assert record.exc_text is None
    assert "Traceback" not in caplog.text


class _NoOpInstrumentator:
    def instrument(self, app: object) -> "_NoOpInstrumentator":
        return self

    def expose(self, app: object, **kwargs: object) -> "_NoOpInstrumentator":
        return self


@pytest.fixture(scope="module")
def canary_app() -> Any:
    base_settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=False,
        ENABLE_CANONICAL_EXTRACTION=False,
        ENABLE_SHADOW_PIPELINE=False,
    )
    with patch("app.main.settings", base_settings), patch(
        "app.main.Instrumentator",
        new=lambda *args, **kwargs: _NoOpInstrumentator(),
    ):
        app = create_app()
    with patch(
        "app.shared.settings.get_settings",
        lambda: base_settings,
    ):
        yield app


@pytest.mark.asyncio
async def test_notification_db_failure_logs_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    from app.api.documents import router as documents_router

    def _explode_engine() -> None:
        raise RuntimeError(CANARY_MESSAGE)

    monkeypatch.setattr("app.shared.database.get_engine", _explode_engine)

    correlation_id = str(uuid.uuid4())
    ctx = PipelineContext(
        document_type="boleto",
        filename=CANARY_FILE_NAME,
    )
    result = PipelineResult(
        risk_score=91.0,
        risk_level="HIGH",
        confidence=95.0,
    )

    await documents_router._send_analysis_notification(
        ctx,
        result,
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        correlation_id=correlation_id,
    )

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert "event=notification_persist_failed" in caplog.text
    assert f"correlation_id={correlation_id}" in caplog.text
    assert "error_type=RuntimeError" in caplog.text


@pytest.mark.asyncio
async def test_analysis_event_publish_failure_logs_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    from app.api.documents import router as documents_router

    class _ExplodingPublisher:
        async def publish(self, _event: object) -> None:
            raise RuntimeError(CANARY_MESSAGE)

    monkeypatch.setattr(
        "app.messaging.infrastructure.factory.get_event_publisher",
        lambda: _ExplodingPublisher(),
    )

    correlation_id = str(uuid.uuid4())
    await documents_router._publish_analysis_event(
        "document.analysis.started",
        document_id=str(uuid.uuid4()),
        document_type="boleto",
        file_name=CANARY_FILE_NAME,
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
    )

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert "event=analysis_event_publish_failed" in caplog.text
    assert f"correlation_id={correlation_id}" in caplog.text
    assert "error_type=RuntimeError" in caplog.text


@pytest.mark.asyncio
async def test_health_full_does_not_echo_internal_errors(
    canary_app: Any,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    from app import main as main_module

    class _ExplodingEngine:
        def connect(self) -> None:
            raise RuntimeError(CANARY_MESSAGE)

    async def _explode_redis() -> None:
        raise RuntimeError(CANARY_MESSAGE)

    async def _explode_rabbitmq() -> None:
        raise RuntimeError(CANARY_MESSAGE)

    async def _explode_llm_service() -> None:
        raise RuntimeError(CANARY_MESSAGE)

    async def _allow_rate_limit(
        self: object, **kwargs: object
    ) -> dict[str, int]:
        return {"limit": 1000, "remaining": 1000, "reset": 0}

    monkeypatch.setattr(main_module, "engine", _ExplodingEngine())
    monkeypatch.setattr(main_module, "get_redis", _explode_redis)
    monkeypatch.setattr(
        "app.observability.health._check_rabbitmq",
        _explode_rabbitmq,
    )
    monkeypatch.setattr(
        "app.ai_agents.llm_service.get_llm_service",
        _explode_llm_service,
    )
    monkeypatch.setattr(
        "app.shared.rate_limiter.RateLimiter.check",
        _allow_rate_limit,
    )

    async with AsyncClient(
        transport=ASGITransport(app=canary_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health/full")

    assert response.status_code == 200
    _assert_no_canaries(response.text, caplog.text)
    _assert_no_traceback(caplog)
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"]["database"] == {
        "status": "unhealthy",
        "error_type": "RuntimeError",
    }
    assert "error" not in payload["dependencies"]["database"]


def test_document_task_failure_logs_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    from app.tasks import document_tasks

    class _RetrySignal(Exception):
        pass

    class _FakeStorage:
        def download_file(self, _key: str) -> bytes:
            return b"canary"

    def _explode(_coro: Any) -> None:
        raise RuntimeError(CANARY_MESSAGE)

    def _retry(*_args: Any, **_kwargs: Any) -> None:
        raise _RetrySignal()

    monkeypatch.setattr(document_tasks, "_run_async", _explode)
    monkeypatch.setattr(
        "app.services.storage.S3StorageProvider",
        lambda: _FakeStorage(),
    )
    monkeypatch.setattr(
        "app.services.pipeline_service.get_pipeline_service",
        lambda: object(),
    )
    monkeypatch.setattr(
        document_tasks.analyze_document_async,
        "retry",
        _retry,
    )

    with pytest.raises(_RetrySignal):
        # _orig_run is bound to the task instance, so self.retry() resolves
        # to the patched method instead of touching a broker.
        document_tasks.analyze_document_async._orig_run(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            CANARY_KEY,
        )

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert CANARY_KEY not in caplog.text
    assert "event=background_analysis_failed" in caplog.text
    assert "error_type=RuntimeError" in caplog.text


@pytest.mark.asyncio
async def test_request_validation_does_not_echo_inputs(
    canary_app: Any,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    async def _allow_rate_limit(
        self: object, **kwargs: object
    ) -> dict[str, int]:
        return {"limit": 1000, "remaining": 1000, "reset": 0}

    monkeypatch.setattr(
        "app.shared.rate_limiter.RateLimiter.check",
        _allow_rate_limit,
    )

    async with AsyncClient(
        transport=ASGITransport(app=canary_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json={
                "email": f"{CANARY_SQL}@invalid",
                "password": CANARY_CREDENTIAL,
                "consent_given": True,
            },
        )

    assert response.status_code == 422
    _assert_no_canaries(response.text, caplog.text)
    _assert_no_traceback(caplog)
    detail = response.json()["detail"]
    assert detail
    assert all("input" not in error for error in detail)
    assert all("ctx" not in error for error in detail)
