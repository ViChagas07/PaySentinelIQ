# ============================================================
# PaySentinelIQ — Pipeline Metrics (Fase 4)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineMetrics:
    """In-memory metrics collector for pipeline observability.

    Ready for Prometheus integration via middleware.
    Currently: in-process counters. Future: prometheus_client.
    """

    pipeline_requests: int = 0
    pipeline_success: int = 0
    pipeline_partial: int = 0
    pipeline_failed: int = 0
    documents_processed: int = 0
    stage_durations: dict[str, list[float]] = field(default_factory=dict)
    errors_by_stage: dict[str, int] = field(default_factory=dict)
    risk_levels: dict[str, int] = field(default_factory=dict)
    llm_requests: int = 0
    llm_failures: int = 0
    retry_count: int = 0
    circuit_opens: int = 0
    timeouts: int = 0

    def record_pipeline(self, status: str, document_type: str = "unknown") -> None:
        self.pipeline_requests += 1
        self.documents_processed += 1
        if status == "success":
            self.pipeline_success += 1
        elif status == "partial":
            self.pipeline_partial += 1
        else:
            self.pipeline_failed += 1

    def record_stage(self, name: str, duration_ms: float, error: bool = False) -> None:
        if name not in self.stage_durations:
            self.stage_durations[name] = []
        self.stage_durations[name].append(duration_ms)
        if error:
            self.errors_by_stage[name] = self.errors_by_stage.get(name, 0) + 1

    def record_risk_level(self, level: str) -> None:
        self.risk_levels[level] = self.risk_levels.get(level, 0) + 1

    def record_llm_call(self, success: bool) -> None:
        self.llm_requests += 1
        if not success:
            self.llm_failures += 1

    def record_retry(self) -> None:
        self.retry_count += 1

    def record_circuit_open(self) -> None:
        self.circuit_opens += 1

    def record_timeout(self) -> None:
        self.timeouts += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline": {
                "requests": self.pipeline_requests,
                "success": self.pipeline_success,
                "partial": self.pipeline_partial,
                "failed": self.pipeline_failed,
                "documents_processed": self.documents_processed,
            },
            "stages": {
                name: {
                    "count": len(durations),
                    "avg_ms": round(sum(durations) / len(durations), 1) if durations else 0,
                    "max_ms": round(max(durations), 1) if durations else 0,
                    "errors": self.errors_by_stage.get(name, 0),
                }
                for name, durations in self.stage_durations.items()
            },
            "risk_levels": dict(self.risk_levels),
            "llm": {
                "requests": self.llm_requests,
                "failures": self.llm_failures,
                "success_rate": round(
                    (self.llm_requests - self.llm_failures) / max(self.llm_requests, 1), 3
                ),
            },
            "resilience": {
                "retries": self.retry_count,
                "circuit_opens": self.circuit_opens,
                "timeouts": self.timeouts,
            },
        }


_metrics = PipelineMetrics()


def get_metrics() -> PipelineMetrics:
    return _metrics
