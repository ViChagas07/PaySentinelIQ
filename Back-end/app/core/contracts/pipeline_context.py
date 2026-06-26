# ============================================================
# PaySentinelIQ — Pipeline Context
# ============================================================
# The SINGLE object that flows through ALL pipeline stages.
# Mutable by design — each stage enriches it, never replaces it.
# Replaces the current pattern of passing dicts/kwargs/tuples.
# ============================================================

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.contracts.evidence import Evidence
from app.core.contracts.pipeline_status import PipelineStatus


@dataclass
class PipelineContext:
    """Central context object traversing all pipeline stages.

    Each stage receives this context, adds its findings, and passes
    it forward. No stage ever creates a new context or returns a
    different object type.

    Lifecycle:
        1. Created by IngestStage with file data
        2. Enriched by ExtractStage with OCR + metadata
        3. Enriched by ValidateStage with deterministic Evidence[]
        4. Enriched by EnrichStage with BrasilAPI data
        5. Enriched by RiskStage with initial risk assessment
        6. (Future) Enriched by CrewAI with agent Evidence[]
        7. Consumed by FusionEngine to produce final score
        8. Serialized by ReportEngine into API response
    """

    # ── Identity ──
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""

    # ── Raw Input ──
    file_bytes: bytes = b""
    filename: str = ""
    mime_type: str = ""
    document_type: str = "unknown"  # "boleto", "contracheque", "holerite"

    # ── Extraction Results ──
    extracted_text: str = ""
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    ocr_confidence: float = 0.0
    extraction_method: str = ""
    page_count: int = 0

    # ── Evidence (universal currency) ──
    evidences: list[Evidence] = field(default_factory=list)

    # ── Scores ──
    deterministic_score: float = 0.0
    fused_score: float = 0.0
    risk_level: str = "LOW"

    # ── AI Results ──
    crew_result: dict[str, Any] = field(default_factory=dict)
    agent_findings: list[dict[str, Any]] = field(default_factory=list)

    # ── External Enrichment ──
    brasilapi_result: dict[str, Any] = field(default_factory=dict)

    # ── Execution Metadata ──
    processing_times: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    pipeline_status: PipelineStatus = PipelineStatus.SUCCESS
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""

    # ── Convenience Methods ──

    def add_evidence(self, evidence: Evidence) -> None:
        """Add a single evidence item. Deduplicates by code."""
        if not any(e.code == evidence.code for e in self.evidences):
            self.evidences.append(evidence)

    def add_evidences(self, evidences: list[Evidence]) -> None:
        """Add multiple evidence items, deduplicating by code."""
        existing_codes = {e.code for e in self.evidences}
        for ev in evidences:
            if ev.code not in existing_codes:
                self.evidences.append(ev)
                existing_codes.add(ev.code)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        if self.pipeline_status == PipelineStatus.SUCCESS:
            self.pipeline_status = PipelineStatus.PARTIAL

    def record_stage_time(self, stage_name: str, duration_seconds: float) -> None:
        self.processing_times[stage_name] = duration_seconds

    def mark_completed(self) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize context for debugging/logging. NOT for API response."""
        return {
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "document_type": self.document_type,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "evidence_count": len(self.evidences),
            "deterministic_score": self.deterministic_score,
            "fused_score": self.fused_score,
            "risk_level": self.risk_level,
            "pipeline_status": self.pipeline_status.value,
            "processing_times": self.processing_times,
            "warnings": self.warnings,
            "errors": self.errors,
            "text_length": len(self.extracted_text),
            "ocr_confidence": self.ocr_confidence,
        }
