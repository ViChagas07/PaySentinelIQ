# ============================================================
# PaySentinelIQ — Correlation IDs (Fase 4)
# ============================================================

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field


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
