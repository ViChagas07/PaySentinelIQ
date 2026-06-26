# ============================================================
# PaySentinelIQ — Fase 4 Production Readiness Tests
# ============================================================

import pytest
from app.observability.correlation import CorrelationContext, get_correlation, set_correlation
from app.observability.metrics import PipelineMetrics, get_metrics
from app.observability.security import validate_file, ValidationResult


class TestCorrelation:
    def test_default_context(self):
        ctx = get_correlation()
        assert ctx.request_id
        assert ctx.trace_id

    def test_set_and_get(self):
        ctx = CorrelationContext(
            pipeline_id="pipe-1", tenant_id="tenant-1", user_id="user-1",
        )
        set_correlation(ctx)
        result = get_correlation()
        assert result.pipeline_id == "pipe-1"
        assert result.tenant_id == "tenant-1"

    def test_to_dict(self):
        ctx = CorrelationContext(pipeline_id="p1", tenant_id="t1")
        d = ctx.to_dict()
        assert d["pipeline_id"] == "p1"
        assert d["tenant_id"] == "t1"


class TestPipelineMetrics:
    def test_record_pipeline(self):
        m = PipelineMetrics()
        m.record_pipeline("success", "boleto")
        assert m.pipeline_requests == 1
        assert m.documents_processed == 1
        assert m.pipeline_success == 1

    def test_record_stage(self):
        m = PipelineMetrics()
        m.record_stage("IngestStage", 150.0)
        m.record_stage("IngestStage", 200.0)
        m.record_stage("IngestStage", 100.0, error=True)
        assert len(m.stage_durations["IngestStage"]) == 3
        assert m.errors_by_stage["IngestStage"] == 1

    def test_record_risk_level(self):
        m = PipelineMetrics()
        m.record_risk_level("HIGH")
        m.record_risk_level("HIGH")
        m.record_risk_level("LOW")
        assert m.risk_levels["HIGH"] == 2
        assert m.risk_levels["LOW"] == 1

    def test_record_llm(self):
        m = PipelineMetrics()
        m.record_llm_call(True)
        m.record_llm_call(True)
        m.record_llm_call(False)
        assert m.llm_requests == 3
        assert m.llm_failures == 1

    def test_to_dict(self):
        m = PipelineMetrics()
        m.record_pipeline("success")
        m.record_stage("Test", 100.0)
        d = m.to_dict()
        assert d["pipeline"]["requests"] == 1
        assert "Test" in d["stages"]

    def test_singleton_same_instance(self):
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2


class TestSecurityValidation:
    def test_valid_pdf(self):
        pdf_bytes = b"%PDF-1.4\n" + b"x" * 150  # 150 bytes total, passes 100-byte minimum
        result = validate_file("boleto.pdf", pdf_bytes, "application/pdf")
        assert result.is_valid

    def test_empty_file(self):
        result = validate_file("test.pdf", b"", "application/pdf")
        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_wrong_magic_bytes(self):
        result = validate_file("fake.pdf", b"NOT A PDF FILE AT ALL JUST RANDOM BYTES......", "application/pdf")
        assert not result.is_valid or any("MIME" in e or "magic" in e.lower() for e in result.errors + result.warnings)

    def test_dangerous_extension(self):
        result = validate_file("virus.exe", b"%PDF-1.4\n.........", "application/pdf")
        assert not result.is_valid

    def test_double_extension(self):
        result = validate_file("boleto.pdf.exe", b"%PDF-1.4\n.........", "application/pdf")
        assert not result.is_valid

    def test_large_file(self):
        result = validate_file("big.pdf", b"x" * 60_000_000, "application/pdf")
        assert not result.is_valid


class TestRateLimiter:
    def test_allows_within_limit(self):
        from app.observability.rate_limit import RateLimiter
        rl = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert rl.is_allowed("key1")

    def test_blocks_over_limit(self):
        from app.observability.rate_limit import RateLimiter
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert rl.is_allowed("key1")
        assert not rl.is_allowed("key1")

    def test_remaining(self):
        from app.observability.rate_limit import RateLimiter
        rl = RateLimiter(max_requests=5, window_seconds=60)
        assert rl.remaining("key1") == 5
        rl.is_allowed("key1")
        assert rl.remaining("key1") == 4
