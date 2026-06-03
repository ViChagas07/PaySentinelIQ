# ============================================================
# PaySentinelIQ — PDF Forensic Tools Tests
# ============================================================

import pytest

from app.ai_agents.tools.pdf_forensic_tools import (
    ai_generation_detector,
    image_forensic_analyzer,
    ocr_confidence_analyzer,
    pdf_layer_analyzer,
    pdf_metadata_extractor,
)


class TestPDFMetadataExtractor:
    """Test PDF metadata forensic analysis."""

    def test_legitimate_producer(self):
        """TOTVS producer should be identified as legitimate."""
        result = pdf_metadata_extractor.invoke({
            "producer": "TOTVS S.A.",
            "creator": "TOTVS Protheus",
            "creation_date": "2025-04-30T10:00:00",
            "modification_date": "2025-04-30T10:00:00",
        })
        assert result["legitimate_producer"] is True
        assert "TOTVS" in result.get("legitimate_producer_name", "")

    def test_suspicious_producer(self):
        """Canva should be flagged as suspicious."""
        result = pdf_metadata_extractor.invoke({
            "producer": "Canva",
            "creator": "Canva",
        })
        assert result["suspicious_producer_detected"] is True
        assert len(result["anomalies"]) > 0

    def test_consumer_editing_tool(self):
        """Adobe Acrobat should be flagged as editing tool."""
        result = pdf_metadata_extractor.invoke({
            "producer": "Adobe Acrobat Pro DC",
        })
        assert result["editing_tool_detected"] is True

    def test_creation_modification_gap(self):
        """More than 24h between creation and modification should flag."""
        result = pdf_metadata_extractor.invoke({
            "creation_date": "2025-01-01T10:00:00",
            "modification_date": "2025-01-05T10:00:00",
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "creation_modification_gap" in types

    def test_creation_after_modification(self):
        """Impossible timeline should flag."""
        result = pdf_metadata_extractor.invoke({
            "creation_date": "2025-01-05T10:00:00",
            "modification_date": "2025-01-01T10:00:00",
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "creation_after_modification" in types

    def test_incremental_saves(self):
        """Incremental saves should be detected."""
        result = pdf_metadata_extractor.invoke({
            "incremental_save_count": 3,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "incremental_saves_detected" in types

    def test_clean_document(self):
        """Clean metadata should return low risk."""
        result = pdf_metadata_extractor.invoke({
            "producer": "TOTVS S.A.",
            "creator": "TOTVS Protheus",
            "creation_date": "2025-04-30T10:00:00",
            "modification_date": "2025-04-30T10:00:00",
            "incremental_save_count": 0,
        })
        assert result["metadata_risk_score"] < 20


class TestPDFLayerAnalyzer:
    """Test PDF content layer and font analysis."""

    def test_single_layer_clean(self):
        """Single layer should be clean."""
        result = pdf_layer_analyzer.invoke({
            "content_stream_count": 1,
            "font_inventory": "Helvetica;Helvetica-Bold",
        })
        assert result["anomaly_count"] == 0

    def test_multiple_layers_suspicious(self):
        """Multiple content streams should flag."""
        result = pdf_layer_analyzer.invoke({
            "content_stream_count": 4,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "multiple_content_layers" in types

    def test_mixed_fonts(self):
        """Mixed serif and sans-serif fonts should flag."""
        result = pdf_layer_analyzer.invoke({
            "content_stream_count": 1,
            "font_inventory": "Helvetica;Times New Roman",
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "mixed_font_families" in types

    def test_font_consistency(self):
        """Two fonts of same family should not flag mixed font anomaly."""
        result = pdf_layer_analyzer.invoke({
            "content_stream_count": 1,
            "font_inventory": "Helvetica;Helvetica-Bold;Helvetica-Oblique",
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "mixed_font_families" not in types

    def test_excessive_images(self):
        """Many embedded images should flag."""
        result = pdf_layer_analyzer.invoke({
            "image_object_count": 5,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "excessive_images" in types

    def test_form_fields(self):
        """Interactive form fields should flag."""
        result = pdf_layer_analyzer.invoke({
            "form_field_count": 3,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "interactive_form_fields" in types

    def test_annotations(self):
        """Annotations should flag."""
        result = pdf_layer_analyzer.invoke({
            "has_annotations": True,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "annotations_present" in types


class TestOCRConfidenceAnalyzer:
    """Test OCR confidence analysis."""

    def test_high_confidence_clean(self):
        """High confidence OCR should be clean."""
        result = ocr_confidence_analyzer.invoke({
            "overall_confidence": 98.0,
            "min_character_confidence": 90.0,
            "low_confidence_regions": 0,
            "total_text_blocks": 20,
        })
        assert result["anomaly_count"] == 0

    def test_low_overall_confidence(self):
        """Low overall confidence should flag."""
        result = ocr_confidence_analyzer.invoke({
            "overall_confidence": 75.0,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "low_ocr_confidence" in types

    def test_character_level_low_confidence(self):
        """Very low character confidence should flag."""
        result = ocr_confidence_analyzer.invoke({
            "overall_confidence": 90.0,
            "min_character_confidence": 40.0,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "character_level_low_confidence" in types

    def test_high_ratio_low_confidence(self):
        """More than 30% low confidence regions should flag."""
        result = ocr_confidence_analyzer.invoke({
            "overall_confidence": 90.0,
            "low_confidence_regions": 10,
            "total_text_blocks": 20,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "high_ratio_low_confidence_regions" in types

    def test_inconsistent_kerning(self):
        """Kerning inconsistency should flag."""
        result = ocr_confidence_analyzer.invoke({
            "inconsistent_kerning_detected": True,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "inconsistent_kerning" in types

    def test_resampling_artifacts(self):
        """Resampling artifacts should flag."""
        result = ocr_confidence_analyzer.invoke({
            "resampling_artifacts": True,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "resampling_artifacts" in types


class TestImageForensicAnalyzer:
    """Test image forensic analysis."""

    def test_dpi_mismatch(self):
        """Image DPI significantly different from text should flag."""
        result = image_forensic_analyzer.invoke({
            "image_dpi": 72,
            "text_dpi": 300,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "dpi_mismatch" in types

    def test_jpeg_artifacts(self):
        """JPEG artifacts should flag."""
        result = image_forensic_analyzer.invoke({
            "has_jpeg_artifacts": True,
            "image_compression": "DCTDecode",
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "jpeg_artifacts_detected" in types

    def test_clean_image(self):
        """Clean image should have no anomalies."""
        result = image_forensic_analyzer.invoke({
            "image_dpi": 300,
            "text_dpi": 300,
            "has_jpeg_artifacts": False,
        })
        assert result["anomaly_count"] == 0


class TestAIGenerationDetector:
    """Test AI-generated document detection."""

    def test_no_indicators(self):
        """No indicators should not suspect AI."""
        result = ai_generation_detector.invoke({
            "text_entropy": 4.5,
        })
        assert result["ai_generation_suspected"] is False

    def test_multiple_indicators(self):
        """Multiple indicators should suspect AI generation."""
        result = ai_generation_detector.invoke({
            "text_entropy": 7.0,
            "numerical_implausibility_score": 0.9,
            "font_rendering_anomaly": True,
            "attention_boundary_artifacts": True,
        })
        assert result["ai_generation_suspected"] is True
        assert len(result["anomalies"]) > 0

    def test_uncertainty_range_provided(self):
        """AI detection should provide uncertainty range."""
        result = ai_generation_detector.invoke({
            "text_entropy": 7.0,
            "font_rendering_anomaly": True,
        })
        assert "uncertainty_range" in result
        assert len(result["uncertainty_range"]) == 2

    def test_disclaimer_present(self):
        """AI detection should include disclaimer about uncertainty."""
        result = ai_generation_detector.invoke({
            "text_entropy": 7.0,
        })
        assert "disclaimer" in result
        assert "emergente" in result["disclaimer"].lower() or "incerteza" in result["disclaimer"].lower()

    def test_baseline_inconsistency(self):
        result = ai_generation_detector.invoke({
            "inconsistent_baseline": True,
        })
        types = [a["type"] for a in result["anomalies"]]
        assert "baseline_inconsistency" in types
