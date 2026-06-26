# ============================================================
# PaySentinelIQ — Fase 3A Production Tests
# ============================================================

import time
import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.core.contracts.pipeline_status import PipelineStatus
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.services.pipeline.event_bus import (
    PipelineEvent, PipelineEventType, PipelineEventBus,
    create_logging_subscriber,
)
from app.services.pipeline.pipeline_comparison import PipelineComparison
from app.services.pipeline.exceptions import (
    PipelineException, FatalPipelineException, OCRException,
    ValidationException, CrewException, FusionException,
)


class TestEventBus:
    def test_subscribe_and_publish(self):
        events = []
        bus = PipelineEventBus()
        bus.subscribe(lambda e: events.append(e))
        bus.publish(PipelineEvent(PipelineEventType.STAGE_STARTED, stage_name="Test"))
        assert len(events) == 1
        assert events[0].stage_name == "Test"

    def test_multiple_subscribers(self):
        count = [0]
        bus = PipelineEventBus()
        bus.subscribe(lambda e: count.__setitem__(0, count[0] + 1))
        bus.subscribe(lambda e: count.__setitem__(0, count[0] + 1))
        bus.publish(PipelineEvent(PipelineEventType.PIPELINE_STARTED))
        assert count[0] == 2

    def test_unsubscribe(self):
        events = []
        bus = PipelineEventBus()
        handler = lambda e: events.append(e)
        bus.subscribe(handler)
        bus.unsubscribe(handler)
        bus.publish(PipelineEvent(PipelineEventType.STAGE_FINISHED))
        assert len(events) == 0

    def test_subscriber_exception_does_not_crash(self):
        bus = PipelineEventBus()
        bus.subscribe(lambda e: 1 / 0)  # Will raise
        bus.subscribe(lambda e: None)
        bus.publish(PipelineEvent(PipelineEventType.STAGE_STARTED))

    def test_logging_subscriber(self):
        handler = create_logging_subscriber()
        bus = PipelineEventBus()
        bus.subscribe(handler)
        bus.publish(PipelineEvent(PipelineEventType.PIPELINE_STARTED, document_id="abc123"))

    def test_event_timestamp(self):
        ev = PipelineEvent(PipelineEventType.STAGE_STARTED)
        assert ev.timestamp  # auto-generated

    def test_clear_subscribers(self):
        events = []
        bus = PipelineEventBus()
        bus.subscribe(lambda e: events.append(e))
        bus.clear()
        bus.publish(PipelineEvent(PipelineEventType.STAGE_STARTED))
        assert len(events) == 0


class TestPipelineComparison:
    def test_score_match(self):
        pc = PipelineComparison(
            legacy_score=72.5, legacy_level="HIGH",
            canonical_score=72.5, canonical_level="HIGH",
        )
        assert pc.score_match
        assert pc.level_match
        assert pc.score_delta == 0.0

    def test_significant_divergence(self):
        pc = PipelineComparison(
            legacy_score=6.0, legacy_level="LOW",
            canonical_score=72.5, canonical_level="HIGH",
        )
        assert pc.is_significant_divergence()
        assert not pc.level_match

    def test_minor_divergence(self):
        pc = PipelineComparison(
            legacy_score=70.0, legacy_level="HIGH",
            canonical_score=73.0, canonical_level="HIGH",
        )
        assert not pc.is_significant_divergence()
        assert pc.score_delta == 3.0

    def test_to_dict(self):
        pc = PipelineComparison(document_id="doc-1", document_type="boleto",
                                legacy_score=50, canonical_score=55)
        d = pc.to_dict()
        assert d["document_id"] == "doc-1"
        assert d["comparison"]["score_delta"] == 5.0


class TestPipelineExceptions:
    def test_hierarchy(self):
        assert issubclass(OCRException, PipelineException)
        assert issubclass(ValidationException, PipelineException)
        assert issubclass(CrewException, PipelineException)
        assert issubclass(FusionException, PipelineException)
        assert issubclass(FatalPipelineException, PipelineException)

    def test_catch_by_base(self):
        try:
            raise OCRException("OCR failed")
        except PipelineException:
            pass  # Caught by base

    def test_specific_catch(self):
        caught = False
        try:
            raise ValidationException("Invalid data")
        except ValidationException:
            caught = True
        except PipelineException:
            pass
        assert caught


class TestBackwardCompatibility:
    def test_pipeline_result_produces_legacy_format(self):
        result = PipelineResult(
            document_id="doc-1", document_type="boleto",
            risk_score=72.5, risk_level="HIGH",
            pipeline_status=PipelineStatus.SUCCESS,
        )
        d = result.to_dict()
        assert "RISK_ASSESSMENT" in d
        ra = d["RISK_ASSESSMENT"]
        assert ra["fraud_risk_score"] == 72.5
        assert ra["risk_classification"] == "HIGH"
        assert ra["recommended_action"] == "REJECT"

    def test_anomaly_list_in_legacy_format(self):
        ev = Evidence(code="TEST", description="Test", severity=Severity.CRITICAL,
                      source=EvidenceSource.DETERMINISTIC, category="structural")
        result = PipelineResult(evidence=[ev])
        d = result.to_dict()
        assert "ANOMALY_LIST" in d
        assert len(d["ANOMALY_LIST"]) == 1

    def test_new_and_legacy_fields_coexist(self):
        result = PipelineResult(risk_score=80, risk_level="HIGH",
                                pipeline_status=PipelineStatus.SUCCESS)
        d = result.to_dict()
        # New fields
        assert d["pipeline_status"] == "success"
        assert d["risk_score"] == 80
        # Legacy fields
        assert d["RISK_ASSESSMENT"]["fraud_risk_score"] == 80
