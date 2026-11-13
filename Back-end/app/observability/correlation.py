# ============================================================
# PaySentinelIQ — Correlation IDs (Fase 4)
# ============================================================

from __future__ import annotations

import uuid
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass, field

CORRELATION_HEADER = "X-Correlation-ID"


@dataclass
class CorrelationContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = ""
    tenant_id: str = ""
    user_id: str = ""

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "pipeline_id": self.pipeline_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
        }


_correlation_ctx: ContextVar[CorrelationContext] = ContextVar(
    "correlation_ctx", default=CorrelationContext()
)


def get_correlation() -> CorrelationContext:
    return _correlation_ctx.get()


def set_correlation(ctx: CorrelationContext) -> None:
    _correlation_ctx.set(ctx)


def _validated_correlation_id(value: str | None) -> str | None:
    """Return a canonical UUID or ``None`` when the value is not safe."""
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except (AttributeError, TypeError, ValueError):
        return None


def resolve_correlation_id(headers: Mapping[str, str] | None = None) -> str:
    """Return a client-supplied correlation ID when valid, else a new UUID."""
    if headers is not None:
        candidate = headers.get(CORRELATION_HEADER)
        if candidate is None:
            candidate = headers.get(CORRELATION_HEADER.lower())
        validated = _validated_correlation_id(candidate)
        if validated is not None:
            return validated
    return str(uuid.uuid4())


def bind_request_correlation(
    headers: Mapping[str, str] | None = None,
    *,
    tenant_id: str = "",
    user_id: str = "",
) -> str:
    """Bind one correlation ID to the shared logging context."""
    correlation_id = resolve_correlation_id(headers)
    set_correlation(
        CorrelationContext(
            request_id=correlation_id,
            trace_id=correlation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    )
    return correlation_id
