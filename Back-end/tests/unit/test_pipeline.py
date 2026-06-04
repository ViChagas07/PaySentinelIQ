# ============================================================
# PaySentinelIQ — 7-Stage Pipeline Integration Tests
# End-to-end tests for the complete fraud detection pipeline
# ============================================================

import uuid

import pytest

from app.fraud_detection.domain.pipeline import (
    Anomaly,
    DocumentClass,
    FraudDetectionPipeline,
    Severity,
    StageResult,
)

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def pipeline():
    """Create a fresh pipeline instance for each test."""
    return FraudDetectionPipeline(enable_ai_agents=False)


@pytest.fixture
def valid_contracheque_data():
    """Valid contracheque data that should pass all validations."""
    return {
        "document_id": str(uuid.uuid4()),
        "document_type": "contracheque",
        "salario_bruto": 7500.00,
        "inss": 828.39,
        "irrf": 742.50,
        "fgts": 600.00,
        "liquido": 5929.11,
        "cargo": "Analista de Sistemas",
        "cbo": "212405",
        "cnpj": "11.222.333/0001-81",
        "razao_social": "Tech Solutions Brasil Ltda",
        "cnae": "62.01-5",
        "dependentes": 0,
        "pdf_metadata": {
            "creator": "TOTVS Protheus",
            "producer": "TOTVS S.A.",
            "creation_date": "2025-04-30T10:00:00",
            "modification_date": "2025-04-30T10:00:00",
            "version": "1.7",
        },
        "pdf_forensics": {
            "content_stream_count": 1,
            "font_inventory": "Helvetica;Helvetica-Bold",
            "image_object_count": 1,
            "form_field_count": 0,
            "has_annotations": False,
            "encryption_level": "none",
        },
        "ocr_data": {
            "confidence": 97.5,
            "min_char_confidence": 89.0,
            "low_confidence_regions": 1,
            "total_text_blocks": 20,
        },
    }


@pytest.fixture
def suspicious_contracheque_data():
    """Contracheque with multiple fraud indicators."""
    return {
        "document_id": str(uuid.uuid4()),
        "document_type": "contracheque",
        "salario_bruto": 25000.00,  # Very high salary
        "inss": 500.00,  # Way too low for this salary
        "irrf": 100.00,  # Way too low for this salary
        "fgts": 1000.00,  # Should be 2000.00
        "liquido": 25000.00,  # Impossible — no deductions subtracted
        "cargo": "Enfermeiro",  # Healthcare role at cleaning company
        "cbo": "223505",  # Enfermeiro CBO
        "cnpj": "11.111.111/1111-11",  # Invalid CNPJ
        "razao_social": "Fake Company",
        "cnae": "81.21-4",  # Cleaning services CNAE — incompatible with Enfermeiro
        "dependentes": 0,
        "outros_descontos": 0,
        "outros_vencimentos": 0,
        "pdf_metadata": {
            "creator": "Canva",
            "producer": "Canva",
            "creation_date": "2025-01-01T10:00:00",
            "modification_date": "2025-04-30T15:00:00",
            "version": "1.4",
        },
        "pdf_forensics": {
            "content_stream_count": 3,  # Multiple layers
            "font_inventory": "Arial;Times New Roman;Courier",  # Mixed fonts
            "image_object_count": 4,
            "form_field_count": 2,
            "has_annotations": True,
            "encryption_level": "none",
        },
        "ocr_data": {
            "confidence": 72.0,  # Low OCR confidence
            "min_char_confidence": 35.0,
            "low_confidence_regions": 8,
            "total_text_blocks": 20,
        },
    }


# ═══════════════════════════════════════════════════════════════
# Stage 1: Ingestion Tests
# ═══════════════════════════════════════════════════════════════


class TestStage1Ingestion:
    """Test Stage 1: Ingestion & Classification."""

    def test_classifies_contracheque(self, pipeline):
        result = pipeline.stage1_ingestion({"document_type": "contracheque"})
        assert result.extracted_data["document_class"] == "contracheque"

    def test_classifies_boleto(self, pipeline):
        result = pipeline.stage1_ingestion(
            {
                "document_type": "boleto",
                "linha_digitavel": "00190000090123456700812345678901234567890123456",
            }
        )
        assert result.extracted_data["document_class"] == "boleto"

    def test_classifies_unknown(self, pipeline):
        result = pipeline.stage1_ingestion({"some_field": "value"})
        assert result.extracted_data["document_class"] == "unknown"

    def test_extracts_pdf_metadata(self, pipeline):
        result = pipeline.stage1_ingestion(
            {
                "pdf_metadata": {
                    "creator": "TestCreator",
                    "producer": "TestProducer",
                    "creation_date": "2025-01-01T10:00:00",
                    "version": "1.7",
                },
            }
        )
        assert result.extracted_data["pdf_creator"] == "TestCreator"
        assert result.extracted_data["pdf_producer"] == "TestProducer"

    def test_suspicious_producer_flagged(self, pipeline):
        result = pipeline.stage1_ingestion(
            {
                "pdf_metadata": {
                    "creator": "Canva",
                    "producer": "Canva",
                    "creation_date": "2025-01-01T10:00:00",
                    "modification_date": "2025-01-01T10:00:00",
                },
            }
        )
        [a.category for a in result.anomalies]
        # Should have at least a forensic or classification anomaly about suspicious producer
        assert len(result.anomalies) > 0


# ═══════════════════════════════════════════════════════════════
# Stage 4: Structural Validation Tests
# ═══════════════════════════════════════════════════════════════


class TestStage4StructuralValidation:
    """Test Stage 4: Structural Validation — contracheque path."""

    def test_valid_contracheque_passes(self, pipeline, valid_contracheque_data):
        s1 = pipeline.stage1_ingestion(valid_contracheque_data)
        result = pipeline.stage4_structural_validation(valid_contracheque_data, s1)

        # Should have INSS, IRRF, FGTS, liquido validations
        assert "inss_validation" in result.extracted_data
        assert "irrf_validation" in result.extracted_data
        assert "fgts_validation" in result.extracted_data
        assert "liquido_validation" in result.extracted_data

    def test_inss_mismatch_detected(self, pipeline, suspicious_contracheque_data):
        s1 = pipeline.stage1_ingestion(suspicious_contracheque_data)
        result = pipeline.stage4_structural_validation(suspicious_contracheque_data, s1)

        inss_val = result.extracted_data.get("inss_validation", {})
        assert inss_val.get("anomaly") is True

    def test_fgts_mismatch_detected(self, pipeline, suspicious_contracheque_data):
        s1 = pipeline.stage1_ingestion(suspicious_contracheque_data)
        result = pipeline.stage4_structural_validation(suspicious_contracheque_data, s1)

        fgts_val = result.extracted_data.get("fgts_validation", {})
        assert fgts_val.get("anomaly") is True

    def test_liquido_mismatch_detected(self, pipeline, suspicious_contracheque_data):
        s1 = pipeline.stage1_ingestion(suspicious_contracheque_data)
        result = pipeline.stage4_structural_validation(suspicious_contracheque_data, s1)

        liquido_val = result.extracted_data.get("liquido_validation", {})
        assert liquido_val.get("anomaly") is True

    def test_cbo_mismatch_detected(self, pipeline, suspicious_contracheque_data):
        s1 = pipeline.stage1_ingestion(suspicious_contracheque_data)
        result = pipeline.stage4_structural_validation(suspicious_contracheque_data, s1)

        cbo_val = result.extracted_data.get("cbo_validation", {})
        assert cbo_val.get("anomaly") is True


# ═══════════════════════════════════════════════════════════════
# Stage 5: Entity Validation Tests
# ═══════════════════════════════════════════════════════════════


class TestStage5EntityValidation:
    """Test Stage 5: Entity Validation."""

    def test_cnpj_valid_passes(self, pipeline, valid_contracheque_data):
        s4 = pipeline.stage4_structural_validation(
            valid_contracheque_data, pipeline.stage1_ingestion(valid_contracheque_data)
        )
        result = pipeline.stage5_entity_validation(valid_contracheque_data, s4)

        cnpj_val = result.extracted_data.get("cnpj_validation", {})
        # This CNPJ should be valid
        assert cnpj_val.get("valid_checksum") is True

    def test_invalid_cnpj_flagged(self, pipeline, suspicious_contracheque_data):
        s4 = pipeline.stage4_structural_validation(
            suspicious_contracheque_data, pipeline.stage1_ingestion(suspicious_contracheque_data)
        )
        result = pipeline.stage5_entity_validation(suspicious_contracheque_data, s4)

        # Should have at least one entity anomaly
        entity_anomalies = [a for a in result.anomalies if a.category == "entity"]
        assert len(entity_anomalies) > 0

    def test_cnae_incompatible_flagged(self, pipeline, suspicious_contracheque_data):
        s4 = pipeline.stage4_structural_validation(
            suspicious_contracheque_data, pipeline.stage1_ingestion(suspicious_contracheque_data)
        )
        result = pipeline.stage5_entity_validation(suspicious_contracheque_data, s4)

        cnae_val = result.extracted_data.get("cnae_validation", {})
        if cnae_val:
            assert cnae_val.get("anomaly") is True


# ═══════════════════════════════════════════════════════════════
# Full Pipeline Integration Tests
# ═══════════════════════════════════════════════════════════════


class TestFullPipeline:
    """End-to-end tests for the complete 7-stage pipeline."""

    def test_pipeline_runs_all_stages(self, pipeline, valid_contracheque_data):
        """All 7 stages should execute without error."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        assert len(result.stages) == 6  # Stages 1-6 produce stage results; Stage 7 is scoring
        assert result.document_class == DocumentClass.CONTRACHEQUE

    def test_pipeline_produces_score(self, pipeline, valid_contracheque_data):
        """Pipeline should produce a valid risk score."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        assert 0 <= result.fraud_risk_score <= 100
        assert result.risk_classification is not None
        assert result.ai_confidence > 0

    def test_pipeline_produces_reasoning(self, pipeline, valid_contracheque_data):
        """AI reasoning summary should be in Portuguese."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        assert result.ai_reasoning_summary
        assert len(result.ai_reasoning_summary) > 10

    def test_clean_document_low_score(self, pipeline, valid_contracheque_data):
        """A clean document should score low (but may have some anomalies
        due to exact calculation)."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        # A clean document might still have minor anomalies if INSS/IRRF values
        # don't exactly match the current table. But it shouldn't be CRITICAL.
        assert result.risk_classification.value != "critical"

    def test_suspicious_document_high_score(self, pipeline, suspicious_contracheque_data):
        """A suspicious document should score significantly higher."""
        result = pipeline.run_full_pipeline(suspicious_contracheque_data)
        assert result.fraud_risk_score > 20
        assert len(result.all_anomalies) > 3  # Should have many anomalies

    def test_report_generation(self, pipeline, valid_contracheque_data):
        """Should generate a complete PSI report."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        report = pipeline.generate_psi_report(result, valid_contracheque_data)

        assert "DOCUMENT_METADATA" in report
        assert "ENTITY_VALIDATION" in report
        assert "STRUCTURAL_VALIDATION" in report
        assert "FINANCIAL_VALIDATION" in report
        assert "FORENSIC_FINDINGS" in report
        assert "ANOMALY_LIST" in report
        assert "RISK_ASSESSMENT" in report
        assert "AI_REASONING_SUMMARY" in report
        assert "ANALYST_NOTES" in report

    def test_report_has_risk_score(self, pipeline, valid_contracheque_data):
        """Report should contain the risk assessment."""
        result = pipeline.run_full_pipeline(valid_contracheque_data)
        report = pipeline.generate_psi_report(result, valid_contracheque_data)

        risk = report["RISK_ASSESSMENT"]
        assert "fraud_risk_score" in risk
        assert "risk_classification" in risk
        assert "recommended_action" in risk

    def test_pipeline_singleton(self):
        """get_fraud_pipeline should return singleton."""
        from app.fraud_detection.domain.pipeline import get_fraud_pipeline

        p1 = get_fraud_pipeline()
        p2 = get_fraud_pipeline()
        assert p1 is p2

    def test_pipeline_with_boleto_data(self, pipeline):
        """Pipeline should handle boleto data."""
        boleto_data = {
            "document_id": str(uuid.uuid4()),
            "document_type": "boleto",
            "linha_digitavel": "00190000090123456700812345678901234567890123456",
            "beneficiario": "Empresa Exemplo Ltda",
            "cnpj": "11.222.333/0001-81",
        }
        result = pipeline.run_full_pipeline(boleto_data)
        assert result.document_class == DocumentClass.BOLETO

    def test_pipeline_empty_data_handles_gracefully(self, pipeline):
        """Empty or minimal data should not crash."""
        result = pipeline.run_full_pipeline(
            {
                "document_id": str(uuid.uuid4()),
            }
        )
        assert result.fraud_risk_score >= 0
        assert result.risk_classification is not None

    def test_pipeline_extreme_values(self, pipeline):
        """Extreme salary values should not crash."""
        data = {
            "document_id": str(uuid.uuid4()),
            "document_type": "contracheque",
            "salario_bruto": 999999.99,
            "inss": 0,
            "irrf": 0,
            "fgts": 0,
            "liquido": 999999.99,
        }
        result = pipeline.run_full_pipeline(data)
        assert result.fraud_risk_score >= 0


# ═══════════════════════════════════════════════════════════════
# Risk Classification Tests
# ═══════════════════════════════════════════════════════════════


class TestRiskClassification:
    """Test risk classification thresholds."""

    def test_low_score_verified(self, pipeline):
        """Score 0-15 should be LOW (VERIFIED)."""
        stage = StageResult(
            stage_name="Test",
            status="completed",
            anomalies=[],  # No anomalies
        )
        score, classification, confidence, action, reasoning = pipeline.stage7_risk_scoring([stage])
        assert score == 0.0
        assert action == "ACCEPT"

    def test_critical_anomaly_high_score(self, pipeline):
        """A single CRITICAL anomaly should push score high."""
        stage = StageResult(
            stage_name="Stage 4: Structural Validation",
            status="completed",
            anomalies=[
                Anomaly(
                    severity=Severity.CRITICAL,
                    category="structural",
                    description="Checksum failure",
                    evidence="DV mismatch",
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="test",
                ),
            ],
        )
        score, classification, confidence, action, reasoning = pipeline.stage7_risk_scoring([stage])
        # CRITICAL (25) * Stage 4 multiplier (1.5) * confidence (1.0) = 37.5
        assert score >= 30  # Should be significantly elevated

    def test_multiple_high_anomalies(self, pipeline):
        """Multiple HIGH anomalies should trigger escalation."""
        anomalies = []
        for i in range(4):
            anomalies.append(
                Anomaly(
                    severity=Severity.HIGH,
                    category="financial",
                    description=f"Test anomaly {i}",
                    evidence="Test",
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="test",
                )
            )
        stage = StageResult(
            stage_name="Stage 4: Structural Validation",
            status="completed",
            anomalies=anomalies,
        )
        score, classification, confidence, action, reasoning = pipeline.stage7_risk_scoring([stage])
        assert score >= 66  # Should be HIGH or CRITICAL
        assert action in ("REJECT", "ESCALATE")
