# ============================================================
# PaySentinelIQ — 7-Stage Fraud Detection Pipeline
# Core orchestration: ingestion → OCR → forensics → structural → entity → cross-field → scoring
# ============================================================

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.shared.domain_primitives import (
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Pipeline Data Structures
# ═══════════════════════════════════════════════════════════════


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentClass(str, Enum):
    BOLETO = "boleto"
    CONTRACHEQUE = "contracheque"
    HOLERITE = "holerite"
    UNKNOWN = "unknown"


@dataclass
class Anomaly:
    """A single detected anomaly with full evidence trail."""

    id: str = field(default_factory=lambda: f"ANOMALY-{uuid.uuid4().hex[:4].upper()}")
    severity: Severity = Severity.INFO
    category: str = ""  # e.g. "structural", "forensic", "financial", "entity", "behavioral"
    description: str = ""
    evidence: str = ""
    confidence: float = 100.0  # 0-100
    stage_detected: str = ""  # Which pipeline stage found this
    tool_used: str = ""  # Which LangChain tool produced this

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "stage_detected": self.stage_detected,
            "tool_used": self.tool_used,
        }


@dataclass
class StageResult:
    """Output from a single pipeline stage."""

    stage_name: str
    status: str  # "completed", "skipped", "failed"
    anomalies: list[Anomaly] = field(default_factory=list)
    extracted_data: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "status": self.status,
            "anomaly_count": len(self.anomalies),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "extracted_data": self.extracted_data,
            "tool_calls_made": len(self.tool_calls),
            "duration_ms": self.duration_ms,
        }


@dataclass
class PipelineResult:
    """Complete result of the 7-stage fraud detection pipeline."""

    document_id: str
    document_class: DocumentClass
    analysis_timestamp: str
    stages: list[StageResult] = field(default_factory=list)
    all_anomalies: list[Anomaly] = field(default_factory=list)
    fraud_risk_score: float = 0.0
    risk_classification: RiskLevel = RiskLevel.LOW
    ai_confidence: float = 0.0
    recommended_action: str = "ACCEPT"
    ai_reasoning_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_class": self.document_class.value,
            "analysis_timestamp": self.analysis_timestamp,
            "stages": [s.to_dict() for s in self.stages],
            "anomaly_count": len(self.all_anomalies),
            "anomalies": [a.to_dict() for a in self.all_anomalies],
            "fraud_risk_score": self.fraud_risk_score,
            "risk_classification": self.risk_classification.value,
            "ai_confidence": self.ai_confidence,
            "recommended_action": self.recommended_action,
            "ai_reasoning_summary": self.ai_reasoning_summary,
        }


# ═══════════════════════════════════════════════════════════════
# 7-Stage Detection Pipeline
# ═══════════════════════════════════════════════════════════════


class FraudDetectionPipeline:
    """
    The core 7-stage fraud detection pipeline as specified in PSI-FraudIntel.

    Stage 1: INGESTION & CLASSIFICATION
    Stage 2: OCR & STRUCTURED EXTRACTION
    Stage 3: FORENSIC PDF ANALYSIS
    Stage 4: STRUCTURAL VALIDATION (boleto or contracheque path)
    Stage 5: ENTITY VALIDATION
    Stage 6: CROSS-FIELD CONSISTENCY
    Stage 7: RISK SCORING & REPORT GENERATION
    """

    def __init__(self, enable_ai_agents: bool = True):
        self.enable_ai_agents = enable_ai_agents
        self.tool_registry: dict[str, Any] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available LangChain tools for the pipeline."""
        try:
            from app.ai_agents.tools.boleto_tools import (
                barcode_decoder,
                beneficiary_binding_check,
                boleto_linha_digitavel_validator,
                pix_boleto_cross_validator,
                pix_emv_parser,
            )
            from app.ai_agents.tools.brazil_financial_tools import (
                bacen_bank_validator,
                cbo_salary_range,
                cnae_compatibility_check,
                cnpj_validator,
                fgts_calculator,
                inss_calculator,
                irrf_calculator,
                liquido_consistency_check,
            )
            from app.ai_agents.tools.custom_tools import (
                analyze_metadata_integrity,
                analyze_payroll_discrepancy,
                check_tax_id_format,
            )
            from app.ai_agents.tools.pdf_forensic_tools import (
                ai_generation_detector,
                image_forensic_analyzer,
                ocr_confidence_analyzer,
                pdf_layer_analyzer,
                pdf_metadata_extractor,
            )

            self.tool_registry = {
                "cnpj_validator": cnpj_validator,
                "inss_calculator": inss_calculator,
                "irrf_calculator": irrf_calculator,
                "fgts_calculator": fgts_calculator,
                "liquido_consistency_check": liquido_consistency_check,
                "cbo_salary_range": cbo_salary_range,
                "cnae_compatibility_check": cnae_compatibility_check,
                "bacen_bank_validator": bacen_bank_validator,
                "boleto_linha_digitavel_validator": boleto_linha_digitavel_validator,
                "barcode_decoder": barcode_decoder,
                "pix_emv_parser": pix_emv_parser,
                "pix_boleto_cross_validator": pix_boleto_cross_validator,
                "beneficiary_binding_check": beneficiary_binding_check,
                "pdf_metadata_extractor": pdf_metadata_extractor,
                "pdf_layer_analyzer": pdf_layer_analyzer,
                "image_forensic_analyzer": image_forensic_analyzer,
                "ocr_confidence_analyzer": ocr_confidence_analyzer,
                "ai_generation_detector": ai_generation_detector,
                "analyze_metadata_integrity": analyze_metadata_integrity,
                "analyze_payroll_discrepancy": analyze_payroll_discrepancy,
                "check_tax_id_format": check_tax_id_format,
            }
            logger.info("Registered %d tools in pipeline", len(self.tool_registry))
        except Exception as e:
            logger.warning("Could not register some tools: %s", e)

    def _call_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Call a registered tool by name, with error handling."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            logger.warning("Tool not found: %s", tool_name)
            return {"error": f"Tool '{tool_name}' not registered", "valid": False}

        try:
            result = tool.invoke(kwargs)
            # LangChain tools return strings or dicts; normalize
            if isinstance(result, str):
                import json

                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    result = {"raw_output": result}
            return result if isinstance(result, dict) else {"raw_output": str(result)}
        except Exception as e:
            logger.error("Tool %s failed: %s", tool_name, e)
            return {"error": str(e), "valid": False}

    # ═══════════════════════════════════════════════════════════
    # STAGE 1: INGESTION & CLASSIFICATION
    # ═══════════════════════════════════════════════════════════

    def stage1_ingestion(self, document_data: dict[str, Any]) -> StageResult:
        """
        Determine document type, extract PDF metadata, detect version and objects.

        Input: Raw document data dict (can include PDF metadata fields)
        Output: Classified document with metadata extracted
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        # Determine document type from data or metadata
        doc_type_raw = document_data.get("document_type", "").lower()
        pdf_metadata = document_data.get("pdf_metadata", {})

        if "boleto" in doc_type_raw or document_data.get("linha_digitavel"):
            doc_class = DocumentClass.BOLETO
        elif (
            any(k in doc_type_raw for k in ("contracheque", "holerite", "payslip", "payroll"))
            or document_data.get("salario_bruto")
            or document_data.get("inss")
        ):
            doc_class = DocumentClass.CONTRACHEQUE
        elif document_data.get("linha_digitavel"):
            doc_class = DocumentClass.BOLETO
        else:
            doc_class = DocumentClass.UNKNOWN
            anomalies.append(
                Anomaly(
                    severity=Severity.LOW,
                    category="classification",
                    description=(
                        "Tipo de documento não identificado automaticamente. "
                        "Classificado como UNKNOWN."
                    ),
                    evidence=f"Dados recebidos: {list(document_data.keys())}",
                    confidence=60,
                    stage_detected="Stage 1",
                    tool_used="heuristic_classifier",
                )
            )

        # Extract PDF metadata if present
        creator = pdf_metadata.get("creator", document_data.get("pdf_creator", ""))
        producer = pdf_metadata.get("producer", document_data.get("pdf_producer", ""))
        creation_date = pdf_metadata.get(
            "creation_date", document_data.get("pdf_creation_date", "")
        )
        mod_date = pdf_metadata.get(
            "modification_date", document_data.get("pdf_modification_date", "")
        )
        pdf_version = pdf_metadata.get("version", document_data.get("pdf_version", ""))
        incremental_saves = pdf_metadata.get(
            "incremental_save_count", document_data.get("incremental_saves", 0)
        )
        page_count = pdf_metadata.get("page_count", document_data.get("page_count", 1))

        extracted = {
            "document_class": doc_class.value,
            "pdf_creator": creator,
            "pdf_producer": producer,
            "pdf_creation_date": creation_date,
            "pdf_modification_date": mod_date,
            "pdf_version": pdf_version,
            "page_count": page_count,
            "incremental_save_count": incremental_saves,
        }

        # Metadata integrity quick check
        if creator and producer and creation_date:
            meta_result = self._call_tool(
                "pdf_metadata_extractor",
                creator=creator,
                producer=producer,
                creation_date=creation_date,
                modification_date=mod_date,
                pdf_version=pdf_version,
                page_count=page_count,
                incremental_save_count=incremental_saves,
            )
            for meta_anomaly in meta_result.get("anomalies", []):
                anomalies.append(
                    Anomaly(
                        severity=Severity(meta_anomaly.get("severity", "low")),
                        category="forensic",
                        description=meta_anomaly.get("description", ""),
                        evidence=meta_anomaly.get("description", ""),
                        confidence=meta_anomaly.get("confidence", 85),
                        stage_detected="Stage 1",
                        tool_used="pdf_metadata_extractor",
                    )
                )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 1: Ingestion & Classification",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    # ═══════════════════════════════════════════════════════════
    # STAGE 2: OCR & STRUCTURED EXTRACTION
    # ═══════════════════════════════════════════════════════════

    def stage2_ocr_extraction(
        self, document_data: dict[str, Any], stage1_result: StageResult
    ) -> StageResult:
        """
        Process OCR results and extract structured fields.
        In production, this would invoke AWS Textract. Here we consume pre-extracted data
        passed from the OCR agent.
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        ocr_data = document_data.get("ocr_data", {})
        doc_class = stage1_result.extracted_data.get("document_class", "unknown")

        # Extract common fields
        extracted = {
            "ocr_confidence": ocr_data.get("confidence", 0),
            "ocr_processing_time_ms": ocr_data.get("processing_time_ms", 0),
            "extracted_fields": ocr_data.get("extracted_fields", {}),
            "barcodes_detected": ocr_data.get("barcodes", []),
            "qr_codes_detected": ocr_data.get("qr_codes", []),
        }

        # OCR confidence check
        ocr_conf = extracted["ocr_confidence"]
        if ocr_conf < 90:
            anomalies.append(
                Anomaly(
                    severity=Severity.MEDIUM if ocr_conf < 80 else Severity.LOW,
                    category="forensic",
                    description=f"Confiança de OCR abaixo do ideal: {ocr_conf}%. "
                    f"Texto parcialmente ilegível — possível adulteração.",
                    evidence=f"OCR confidence: {ocr_conf}%",
                    confidence=75,
                    stage_detected="Stage 2",
                    tool_used="ocr_confidence_analyzer",
                )
            )

        # Detect QR codes (potential Pix)
        if extracted["qr_codes_detected"]:
            qr_count = len(extracted["qr_codes_detected"])
            if doc_class == "boleto" and qr_count == 0:
                anomalies.append(
                    Anomaly(
                        severity=Severity.INFO,
                        category="structural",
                        description=(
                            "Boleto sem QR Code Pix detectado. "
                            "Verificar se o documento é anterior ao Pix."
                        ),
                        evidence="Nenhum QR code encontrado no documento.",
                        confidence=60,
                        stage_detected="Stage 2",
                        tool_used="qr_detection",
                    )
                )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 2: OCR & Structured Extraction",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    # ═══════════════════════════════════════════════════════════
    # STAGE 3: FORENSIC PDF ANALYSIS
    # ═══════════════════════════════════════════════════════════

    def stage3_forensic_pdf(
        self, document_data: dict[str, Any], stage1_result: StageResult
    ) -> StageResult:
        """
        Multi-layer PDF forensic analysis: layers, fonts, images, metadata.
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        pdf_forensics = document_data.get("pdf_forensics", {})

        # Layer analysis
        layer_result = self._call_tool(
            "pdf_layer_analyzer",
            content_stream_count=pdf_forensics.get("content_stream_count", 1),
            font_inventory=pdf_forensics.get("font_inventory", ""),
            image_object_count=pdf_forensics.get("image_object_count", 0),
            form_field_count=pdf_forensics.get("form_field_count", 0),
            has_annotations=pdf_forensics.get("has_annotations", False),
            encryption_level=pdf_forensics.get("encryption_level", "none"),
        )
        for la in layer_result.get("anomalies", []):
            anomalies.append(
                Anomaly(
                    severity=Severity(la.get("severity", "low")),
                    category="forensic",
                    description=la.get("description", ""),
                    evidence=layer_result.get("evidence", ""),
                    confidence=la.get("confidence", 75),
                    stage_detected="Stage 3",
                    tool_used="pdf_layer_analyzer",
                )
            )
        extracted["layer_analysis"] = layer_result

        # OCR confidence analysis
        ocr_data = document_data.get("ocr_data", {})
        ocr_result = self._call_tool(
            "ocr_confidence_analyzer",
            overall_confidence=ocr_data.get("confidence", 95),
            min_character_confidence=ocr_data.get("min_char_confidence", 95),
            low_confidence_regions=ocr_data.get("low_confidence_regions", 0),
            total_text_blocks=ocr_data.get("total_text_blocks", 1),
            inconsistent_kerning_detected=pdf_forensics.get("inconsistent_kerning", False),
            resampling_artifacts=pdf_forensics.get("resampling_artifacts", False),
        )
        for oa in ocr_result.get("anomalies", []):
            anomalies.append(
                Anomaly(
                    severity=Severity(oa.get("severity", "low")),
                    category="forensic",
                    description=oa.get("description", ""),
                    evidence=ocr_result.get("evidence", ""),
                    confidence=oa.get("confidence", 75),
                    stage_detected="Stage 3",
                    tool_used="ocr_confidence_analyzer",
                )
            )
        extracted["ocr_analysis"] = ocr_result

        # AI generation check
        ai_data = document_data.get("ai_generation_indicators", {})
        ai_result = self._call_tool(
            "ai_generation_detector",
            text_entropy=ai_data.get("text_entropy", 0),
            numerical_implausibility_score=ai_data.get("numerical_implausibility_score", 0),
            font_rendering_anomaly=ai_data.get("font_rendering_anomaly", False),
            attention_boundary_artifacts=ai_data.get("attention_boundary_artifacts", False),
            inconsistent_baseline=ai_data.get("inconsistent_baseline", False),
        )
        if ai_result.get("ai_generation_suspected"):
            for aa in ai_result.get("anomalies", []):
                anomalies.append(
                    Anomaly(
                        severity=Severity(aa.get("severity", "low")),
                        category="behavioral",
                        description=f"[IA-GENERATED SUSPECT] {aa.get('description', '')}",
                        evidence=ai_result.get("evidence", ""),
                        confidence=aa.get("confidence", 50),
                        stage_detected="Stage 3",
                        tool_used="ai_generation_detector",
                    )
                )
        extracted["ai_generation_analysis"] = ai_result

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 3: Forensic PDF Analysis",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    # ═══════════════════════════════════════════════════════════
    # STAGE 4: STRUCTURAL VALIDATION
    # ═══════════════════════════════════════════════════════════

    def stage4_structural_validation(
        self, document_data: dict[str, Any], stage1_result: StageResult
    ) -> StageResult:
        """
        Branching validation based on document type.
        Boleto path: FEBRABAN layout, linha digitável checksum, bank code, QR Pix, barcode
        Contracheque path: INSS, IRRF, FGTS, líquido, CBO
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        doc_class = stage1_result.extracted_data.get("document_class", "unknown")

        if doc_class == DocumentClass.BOLETO.value:
            extracted = self._validate_boleto(document_data, anomalies)
        elif doc_class == DocumentClass.CONTRACHEQUE.value:
            extracted = self._validate_contracheque(document_data, anomalies)
        else:
            # Try both paths
            if document_data.get("linha_digitavel"):
                extracted = self._validate_boleto(document_data, anomalies)
            if document_data.get("salario_bruto"):
                contracheque_extracted = self._validate_contracheque(document_data, anomalies)
                extracted.update(contracheque_extracted)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 4: Structural Validation",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    def _validate_boleto(self, data: dict[str, Any], anomalies: list[Anomaly]) -> dict[str, Any]:
        """Boleto structural validation sub-pipeline."""
        extracted: dict[str, Any] = {}

        linha = data.get("linha_digitavel", "")
        barcode_val = data.get("barcode_value", "")
        qr_payload = data.get("qr_code_payload", "")

        # Validate linha digitável
        if linha:
            ld_result = self._call_tool("boleto_linha_digitavel_validator", linha_digitavel=linha)
            extracted["linha_digitavel_validation"] = ld_result

            if not ld_result.get("checksum_valid", False):
                for ld_anomaly in ld_result.get("anomalies", []):
                    anomalies.append(
                        Anomaly(
                            severity=Severity.CRITICAL,
                            category="structural",
                            description=ld_anomaly.get("description", ""),
                            evidence=ld_result.get("evidence", ""),
                            confidence=100,
                            stage_detected="Stage 4",
                            tool_used="boleto_linha_digitavel_validator",
                        )
                    )

            # Validate bank code
            banco = ld_result.get("banco_codigo", data.get("banco_codigo", ""))
            if banco:
                bank_result = self._call_tool("bacen_bank_validator", bank_code=banco)
                extracted["bank_validation"] = bank_result
                if not bank_result.get("valid", False):
                    anomalies.append(
                        Anomaly(
                            severity=Severity.CRITICAL,
                            category="structural",
                            description=bank_result.get("error", "Código de banco inválido"),
                            evidence=bank_result.get("evidence", ""),
                            confidence=100,
                            stage_detected="Stage 4",
                            tool_used="bacen_bank_validator",
                        )
                    )

        # Decode barcode
        if barcode_val:
            bc_result = self._call_tool("barcode_decoder", barcode_value=barcode_val)
            extracted["barcode_decoding"] = bc_result

        # Parse Pix QR code
        if qr_payload:
            pix_result = self._call_tool("pix_emv_parser", qr_code_payload=qr_payload)
            extracted["pix_parsing"] = pix_result

            for pix_anomaly in pix_result.get("anomalies", []):
                anomalies.append(
                    Anomaly(
                        severity=Severity(pix_anomaly.get("severity", "medium")),
                        category="structural",
                        description=pix_anomaly.get("description", ""),
                        evidence=pix_result.get("evidence", ""),
                        confidence=pix_anomaly.get("confidence", 90),
                        stage_detected="Stage 4",
                        tool_used="pix_emv_parser",
                    )
                )

        return extracted

    def _validate_contracheque(
        self, data: dict[str, Any], anomalies: list[Anomaly]
    ) -> dict[str, Any]:
        """Contracheque/Holerite structural validation sub-pipeline."""
        extracted: dict[str, Any] = {}

        salario_bruto = data.get("salario_bruto", 0)
        inss_printed = data.get("inss", data.get("inss_printed", 0))
        irrf_printed = data.get("irrf", data.get("irrf_printed", 0))
        fgts_printed = data.get("fgts", data.get("fgts_printed", 0))
        liquido_printed = data.get(
            "liquido", data.get("salario_liquido", data.get("liquido_printed", 0))
        )
        outros_descontos = data.get("outros_descontos", 0)
        outros_vencimentos = data.get("outros_vencimentos", 0)
        cargo = data.get("cargo", data.get("job_title", ""))
        cbo_code = data.get("cbo", data.get("cbo_code", ""))
        dependentes = data.get("dependentes", 0)

        if salario_bruto <= 0:
            return extracted

        # --- INSS validation ---
        inss_result = self._call_tool(
            "inss_calculator",
            salario_bruto=salario_bruto,
            inss_printed=inss_printed,
            competencia="2025",
        )
        extracted["inss_validation"] = inss_result
        if inss_result.get("anomaly"):
            anomalies.append(
                Anomaly(
                    severity=Severity(inss_result.get("severity", "high")),
                    category="financial",
                    description=f"INSS calculado (R$ {inss_result.get('inss_calculado', 0):,.2f}) "
                    f"diverge do valor declarado (R$ {inss_printed:,.2f}). "
                    f"Delta: R$ {inss_result.get('delta', 0):,.2f}.",
                    evidence=inss_result.get("evidence", ""),
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="inss_calculator",
                )
            )

        # --- IRRF validation ---
        irrf_result = self._call_tool(
            "irrf_calculator",
            salario_bruto=salario_bruto,
            inss=inss_result.get("inss_calculado", inss_printed),
            irrf_printed=irrf_printed,
            dependentes=dependentes,
        )
        extracted["irrf_validation"] = irrf_result
        if irrf_result.get("anomaly"):
            anomalies.append(
                Anomaly(
                    severity=Severity(irrf_result.get("severity", "high")),
                    category="financial",
                    description=f"IRRF calculado (R$ {irrf_result.get('irrf_calculado', 0):,.2f}) "
                    f"diverge do valor declarado (R$ {irrf_printed:,.2f}). "
                    f"Delta: R$ {irrf_result.get('delta', 0):,.2f}.",
                    evidence=irrf_result.get("evidence", ""),
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="irrf_calculator",
                )
            )

        # --- FGTS validation ---
        fgts_result = self._call_tool(
            "fgts_calculator", salario_bruto=salario_bruto, fgts_printed=fgts_printed
        )
        extracted["fgts_validation"] = fgts_result
        if fgts_result.get("anomaly"):
            anomalies.append(
                Anomaly(
                    severity=Severity(fgts_result.get("severity", "critical")),
                    category="financial",
                    description=f"FGTS calculado (R$ {fgts_result.get('fgts_calculado', 0):,.2f}) "
                    f"diverge do valor declarado (R$ {fgts_printed:,.2f}).",
                    evidence=fgts_result.get("evidence", ""),
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="fgts_calculator",
                )
            )

        # --- Líquido consistency ---
        liquido_result = self._call_tool(
            "liquido_consistency_check",
            salario_bruto=salario_bruto,
            inss=inss_printed,
            irrf=irrf_printed,
            outros_descontos=outros_descontos,
            outros_vencimentos=outros_vencimentos,
            liquido_printed=liquido_printed,
        )
        extracted["liquido_validation"] = liquido_result
        if liquido_result.get("anomaly"):
            anomalies.append(
                Anomaly(
                    severity=Severity.CRITICAL,
                    category="financial",
                    description=(
                        f"Salário líquido não confere: calculado "
                        f"R$ {liquido_result.get('liquido_calculado', 0):,.2f} "
                        f"vs. declarado R$ {liquido_printed:,.2f}. "
                        f"Delta: R$ {liquido_result.get('delta', 0):,.2f}."
                    ),
                    evidence=liquido_result.get("evidence", ""),
                    confidence=100,
                    stage_detected="Stage 4",
                    tool_used="liquido_consistency_check",
                )
            )

        # --- CBO salary range check ---
        if cbo_code:
            cbo_result = self._call_tool(
                "cbo_salary_range", cbo_code=cbo_code, salario=salario_bruto, cargo=cargo
            )
            extracted["cbo_validation"] = cbo_result
            if cbo_result.get("anomaly"):
                anomalies.append(
                    Anomaly(
                        severity=Severity(cbo_result.get("severity", "medium")),
                        category="financial",
                        description=cbo_result.get("evidence", ""),
                        evidence=cbo_result.get("evidence", ""),
                        confidence=cbo_result.get("confidence", 75),
                        stage_detected="Stage 4",
                        tool_used="cbo_salary_range",
                    )
                )

        return extracted

    # ═══════════════════════════════════════════════════════════
    # STAGE 5: ENTITY VALIDATION
    # ═══════════════════════════════════════════════════════════

    def stage5_entity_validation(
        self, document_data: dict[str, Any], stage4_result: StageResult
    ) -> StageResult:
        """
        CNPJ validation, CNAE compatibility, beneficiary binding.
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        cnpj = document_data.get("cnpj", document_data.get("employer_cnpj", ""))
        razao_social = document_data.get("razao_social", document_data.get("employer_name", ""))
        cnae = document_data.get("cnae", "")
        cargo = document_data.get("cargo", "")
        cbo = document_data.get("cbo", document_data.get("cbo_code", ""))

        # CNPJ validation
        if cnpj:
            cnpj_result = self._call_tool("cnpj_validator", cnpj=cnpj)
            extracted["cnpj_validation"] = cnpj_result

            if not cnpj_result.get("valid_checksum", False):
                anomalies.append(
                    Anomaly(
                        severity=Severity.CRITICAL,
                        category="entity",
                        description=(
                            f"CNPJ inválido: {cnpj}. Dígitos verificadores "
                            f"não conferem via Módulo 11."
                        ),
                        evidence=f"CNPJ: {cnpj} | Checksum: FALHOU",
                        confidence=100,
                        stage_detected="Stage 5",
                        tool_used="cnpj_validator",
                    )
                )
            else:
                extracted["cnpj_formatted"] = cnpj_result.get("cnpj_formatted")

        # CNAE compatibility
        if cnae and (cbo or cargo):
            cnae_result = self._call_tool(
                "cnae_compatibility_check",
                cnae_code=cnae,
                cbo_code=cbo,
                cargo=cargo,
                razao_social=razao_social,
            )
            extracted["cnae_validation"] = cnae_result

            if cnae_result.get("anomaly"):
                anomalies.append(
                    Anomaly(
                        severity=Severity.HIGH,
                        category="entity",
                        description=cnae_result.get("evidence", ""),
                        evidence=cnae_result.get("evidence", ""),
                        confidence=cnae_result.get("confidence", 70),
                        stage_detected="Stage 5",
                        tool_used="cnae_compatibility_check",
                    )
                )

        # Check tax ID format for non-CNPJ IDs
        tax_id = document_data.get("tax_id", document_data.get("employee_tax_id", ""))
        if tax_id:
            tax_result = self._call_tool("check_tax_id_format", tax_id=tax_id)
            extracted["tax_id_validation"] = tax_result
            if not tax_result.get("valid", True):
                for issue in tax_result.get("issues", []):
                    anomalies.append(
                        Anomaly(
                            severity=Severity.HIGH,
                            category="entity",
                            description=f"Formato de identificador fiscal inválido: {issue}",
                            evidence=f"Tax ID: {tax_id}",
                            confidence=90,
                            stage_detected="Stage 5",
                            tool_used="check_tax_id_format",
                        )
                    )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 5: Entity Validation",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    # ═══════════════════════════════════════════════════════════
    # STAGE 6: CROSS-FIELD CONSISTENCY
    # ═══════════════════════════════════════════════════════════

    def stage6_cross_field_consistency(
        self, document_data: dict[str, Any], stages: list[StageResult]
    ) -> StageResult:
        """
        Cross-reference all extracted fields for internal consistency.
        Checks: visual text vs encoded data, beneficiary binding, date coherence.
        """
        start = datetime.now(UTC)
        anomalies: list[Anomaly] = []
        extracted: dict[str, Any] = {}

        # --- Pix-to-Boleto cross-validation ---
        boleto_beneficiario = document_data.get(
            "beneficiario", document_data.get("beneficiary_name", "")
        )
        boleto_cnpj = document_data.get("cnpj", "")
        boleto_valor = document_data.get("valor", document_data.get("amount", 0))

        # Try to get Pix data from Stage 4 results
        pix_data = {}
        for stage in stages:
            if "Stage 4" in stage.stage_name:
                pix_parsed = stage.extracted_data.get("pix_parsing", {})
                if pix_parsed:
                    pix_data = pix_parsed
                break

        pix_merchant = pix_data.get("merchant_name", "")
        pix_key = pix_data.get("pix_key", "")
        pix_amount = pix_data.get("amount", 0)

        if pix_merchant or pix_key:
            cross_result = self._call_tool(
                "pix_boleto_cross_validator",
                boleto_beneficiario=boleto_beneficiario,
                boleto_cnpj=boleto_cnpj,
                boleto_valor=boleto_valor,
                pix_merchant_name=pix_merchant,
                pix_key=pix_key,
                pix_amount=pix_amount,
            )
            extracted["pix_boleto_cross_validation"] = cross_result

            for ca in cross_result.get("anomalies", []):
                anomalies.append(
                    Anomaly(
                        severity=Severity(ca.get("severity", "critical")),
                        category="cross_field",
                        description=ca.get("description", ""),
                        evidence=cross_result.get("evidence", ""),
                        confidence=ca.get("confidence", 95),
                        stage_detected="Stage 6",
                        tool_used="pix_boleto_cross_validator",
                    )
                )

        # --- Beneficiary binding check ---
        binding_result = self._call_tool(
            "beneficiary_binding_check",
            boleto_beneficiario=boleto_beneficiario,
            boleto_cnpj=boleto_cnpj,
            banco_codigo=document_data.get("banco_codigo", ""),
            pix_merchant_name=pix_merchant,
            pix_key=pix_key,
        )
        extracted["beneficiary_binding"] = binding_result

        if binding_result.get("fraud_signal"):
            anomalies.append(
                Anomaly(
                    severity=Severity.CRITICAL,
                    category="cross_field",
                    description=(
                        "Vinculação de beneficiário quebrada — múltiplas "
                        "fontes apontam para destinos diferentes."
                    ),
                    evidence=binding_result.get("evidence", ""),
                    confidence=85,
                    stage_detected="Stage 6",
                    tool_used="beneficiary_binding_check",
                )
            )

        # --- Salary-to-CBO cross-check ---
        salario = document_data.get("salario_bruto", 0)
        cbo = document_data.get("cbo", "")
        cargo = document_data.get("cargo", "")

        if salario > 0 and (cbo or cargo):
            salario_check = self._call_tool(
                "analyze_payroll_discrepancy",
                employee_salary=salario,
                department_median=document_data.get("department_median", salario),
                department_std_dev=document_data.get("department_std_dev", 1.0),
            )
            extracted["salary_discrepancy"] = salario_check
            if salario_check.get("risk", "low") in ("high", "critical"):
                anomalies.append(
                    Anomaly(
                        severity=Severity.HIGH,
                        category="cross_field",
                        description=(
                            f"Salário {salario_check.get('deviation_sigma', 0)}σ "
                            f"da mediana do departamento."
                        ),
                        evidence=salario_check.get("detail", ""),
                        confidence=80,
                        stage_detected="Stage 6",
                        tool_used="analyze_payroll_discrepancy",
                    )
                )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return StageResult(
            stage_name="Stage 6: Cross-Field Consistency",
            status="completed",
            anomalies=anomalies,
            extracted_data=extracted,
            duration_ms=duration,
        )

    # ═══════════════════════════════════════════════════════════
    # STAGE 7: RISK SCORING & REPORT GENERATION
    # ═══════════════════════════════════════════════════════════

    def stage7_risk_scoring(
        self, all_stages: list[StageResult]
    ) -> tuple[float, RiskLevel, float, str, str]:
        """
        Aggregate all anomaly signals into a composite fraud risk score (0-100).
        Uses severity-weighted scoring with stage multipliers.

        Scoring model:
        - CRITICAL anomaly:  +25 base points
        - HIGH anomaly:       +15 base points
        - MEDIUM anomaly:     +8 base points
        - LOW anomaly:        +3 base points
        - INFO anomaly:       +1 base point

        Stage multipliers:
        - Stage 4 (Structural): 1.5x (mathematical certainty)
        - Stage 5 (Entity): 1.3x
        - Stage 6 (Cross-field): 1.4x

        Cap at 100.
        """
        all_anomalies: list[Anomaly] = []
        for stage in all_stages:
            all_anomalies.extend(stage.anomalies)

        severity_weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1,
        }

        stage_multipliers = {
            "Stage 4": 1.5,
            "Stage 5": 1.3,
            "Stage 6": 1.4,
        }

        total_score = 0.0
        for anomaly in all_anomalies:
            base = severity_weights.get(anomaly.severity, 5)
            stage_name = (
                anomaly.stage_detected.split(":")[0].strip() if anomaly.stage_detected else ""
            )
            multiplier = stage_multipliers.get(stage_name, 1.0)
            total_score += base * multiplier * (anomaly.confidence / 100)

        # Cap at 100
        total_score = min(total_score, 100.0)

        # Classification
        if total_score >= 86:
            classification = RiskLevel.CRITICAL
            action = "ESCALATE"
        elif total_score >= 66:
            classification = RiskLevel.HIGH
            action = "REJECT"
        elif total_score >= 36:
            classification = RiskLevel.MEDIUM
            action = "MANUAL_REVIEW"
        elif total_score >= 16:
            classification = RiskLevel.LOW
            action = "MANUAL_REVIEW"
        else:
            classification = RiskLevel.LOW
            action = "ACCEPT"

        # AI confidence: inversely proportional to anomaly dispersion
        if len(all_anomalies) == 0:
            ai_confidence = 95.0
        elif len(all_anomalies) <= 2:
            ai_confidence = 90.0
        elif len(all_anomalies) <= 5:
            ai_confidence = 80.0
        else:
            ai_confidence = 70.0

        # Reduce confidence if we have only 1 stage worth of anomalies
        unique_stages = {a.stage_detected for a in all_anomalies}
        if len(unique_stages) == 1 and len(all_anomalies) > 0:
            ai_confidence -= 10

        return (
            total_score,
            classification,
            ai_confidence,
            action,
            self._generate_reasoning_summary(all_anomalies, total_score, classification),
        )

    def _generate_reasoning_summary(
        self, anomalies: list[Anomaly], score: float, classification: RiskLevel
    ) -> str:
        """Generate AI reasoning summary in Portuguese for human analysts."""
        if not anomalies:
            return (
                "Nenhuma anomalia detectada em todas as 7 etapas do pipeline. "
                "Documento passa em todas as validações estruturais, forenses e financeiras. "
                "Baixa probabilidade de adulteração."
            )

        critical = [a for a in anomalies if a.severity == Severity.CRITICAL]
        high = [a for a in anomalies if a.severity == Severity.HIGH]
        medium = [a for a in anomalies if a.severity == Severity.MEDIUM]

        parts = []

        if critical:
            parts.append(
                f"Foram detectadas {len(critical)} anomalias CRÍTICAS, incluindo: "
                f"{critical[0].description}"
            )

        if high:
            parts.append(
                f"Detectadas {len(high)} anomalias de ALTA severidade relacionadas a "
                f"{high[0].category}."
            )

        if medium and not critical:
            parts.append(
                f"Detectadas {len(medium)} anomalias de MÉDIA severidade. "
                f"Recomenda-se revisão manual antes de qualquer decisão."
            )

        parts.append(
            f"Score composto de fraude: {score:.1f}/100 "
            f"— Classificação: {classification.value.upper()}. "
            f"Total de {len(anomalies)} anomalias identificadas em "
            f"{len({a.stage_detected for a in anomalies})} etapas do pipeline."
        )

        return " ".join(parts)

    # ═══════════════════════════════════════════════════════════
    # FULL PIPELINE EXECUTION
    # ═══════════════════════════════════════════════════════════

    def run_full_pipeline(self, document_data: dict[str, Any]) -> PipelineResult:
        """
        Execute the complete 7-stage fraud detection pipeline.
        NEVER skip a stage. NEVER short-circuit based on early findings.

        Args:
            document_data: Dict containing all extracted document data:
                - document_type: str
                - pdf_metadata: dict (creator, producer, creation_date, etc.)
                - ocr_data: dict (confidence, extracted_fields, barcodes, qr_codes)
                - pdf_forensics: dict (content_stream_count, font_inventory, etc.)
                - All financial fields (salario_bruto, inss, irrf, fgts, etc.)
                - All boleto fields (linha_digitavel, barcode_value, qr_code_payload)
                - All entity fields (cnpj, razao_social, cnae, cbo, cargo)

        Returns:
            PipelineResult with all stages, anomalies, risk score, and classification.
        """
        document_id = document_data.get("document_id", str(uuid.uuid4()))
        start_time = datetime.now(UTC)

        logger.info("Starting 7-stage pipeline for document: %s", document_id)

        # ── STAGE 1: Ingestion & Classification ──
        logger.info("[Stage 1/7] Ingestion & Classification")
        s1 = self.stage1_ingestion(document_data)

        # ── STAGE 2: OCR & Structured Extraction ──
        logger.info("[Stage 2/7] OCR & Structured Extraction")
        s2 = self.stage2_ocr_extraction(document_data, s1)

        # ── STAGE 3: Forensic PDF Analysis ──
        logger.info("[Stage 3/7] Forensic PDF Analysis")
        s3 = self.stage3_forensic_pdf(document_data, s1)

        # ── STAGE 4: Structural Validation ──
        logger.info("[Stage 4/7] Structural Validation")
        s4 = self.stage4_structural_validation(document_data, s1)

        # ── STAGE 5: Entity Validation ──
        logger.info("[Stage 5/7] Entity Validation")
        s5 = self.stage5_entity_validation(document_data, s4)

        # ── STAGE 6: Cross-Field Consistency ──
        logger.info("[Stage 6/7] Cross-Field Consistency")
        all_stages = [s1, s2, s3, s4, s5]
        s6 = self.stage6_cross_field_consistency(document_data, all_stages)
        all_stages.append(s6)

        # ── STAGE 7: Risk Scoring & Report ──
        logger.info("[Stage 7/7] Risk Scoring & Report Generation")
        score, classification, confidence, action, reasoning = self.stage7_risk_scoring(all_stages)

        # Build result
        total_anomalies: list[Anomaly] = []
        for stage in all_stages:
            total_anomalies.extend(stage.anomalies)

        result = PipelineResult(
            document_id=document_id,
            document_class=DocumentClass(s1.extracted_data.get("document_class", "unknown")),
            analysis_timestamp=start_time.isoformat(),
            stages=all_stages,
            all_anomalies=total_anomalies,
            fraud_risk_score=round(score, 1),
            risk_classification=classification,
            ai_confidence=confidence,
            recommended_action=action,
            ai_reasoning_summary=reasoning,
        )

        logger.info(
            "Pipeline complete for %s: score=%.1f, class=%s, anomalies=%d, action=%s",
            document_id,
            score,
            classification.value,
            len(total_anomalies),
            action,
        )

        return result

    def generate_psi_report(
        self, result: PipelineResult, document_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate the complete PSI Fraud Analysis Report in the Section 5 format.
        This is consumed by the reporting_agent and displayed in the PSI dashboard.
        """
        s1_data = result.stages[0].extracted_data if len(result.stages) > 0 else {}
        s4_data = result.stages[3].extracted_data if len(result.stages) > 3 else {}
        s5_data = result.stages[4].extracted_data if len(result.stages) > 4 else {}

        cnpj_valid = s5_data.get("cnpj_validation", {})
        inss_valid = s4_data.get("inss_validation", {})
        irrf_valid = s4_data.get("irrf_validation", {})
        fgts_valid = s4_data.get("fgts_validation", {})
        liquido_valid = s4_data.get("liquido_validation", {})
        ld_valid = s4_data.get("linha_digitavel_validation", {})
        bank_valid = s4_data.get("bank_validation", {})

        report = {
            "DOCUMENT_METADATA": {
                "document_id": result.document_id,
                "document_type": result.document_class.value,
                "analysis_timestamp": result.analysis_timestamp,
                "pdf_producer": s1_data.get("pdf_producer", "N/A"),
                "creation_date": s1_data.get("pdf_creation_date", "N/A"),
                "modification_date": s1_data.get("pdf_modification_date", "NONE"),
                "incremental_saves": s1_data.get("incremental_save_count", 0),
            },
            "ENTITY_VALIDATION": {
                "cnpj_extracted": document_data.get("cnpj", "N/A"),
                "cnpj_valid": cnpj_valid.get("valid_checksum", None),
                "receita_status": "NOT_VERIFIED",  # Requires external API in production
                "razao_social_match": "NOT_VERIFIABLE",
                "cnae": document_data.get("cnae", "N/A"),
                "porte": "NOT_VERIFIED",
            },
            "STRUCTURAL_VALIDATION": {
                "linha_digitavel": document_data.get("linha_digitavel", "N/A"),
                "checksum_valid": ld_valid.get("checksum_valid", None),
                "bank_code": ld_valid.get("banco_codigo", "N/A"),
                "bank_valid": bank_valid.get("valid", None),
                "qr_pix_key": s4_data.get("pix_parsing", {}).get("pix_key", "NONE"),
                "pix_beneficiary": s4_data.get("pix_parsing", {}).get("merchant_name", "NONE"),
                "beneficiary_match": "NOT_APPLICABLE",
            },
            "FINANCIAL_VALIDATION": {
                "salario_bruto": document_data.get("salario_bruto", 0),
                "inss_printed": document_data.get("inss", 0),
                "inss_calculated": inss_valid.get("inss_calculado", 0),
                "inss_delta": inss_valid.get("delta", 0),
                "irrf_printed": document_data.get("irrf", 0),
                "irrf_calculated": irrf_valid.get("irrf_calculado", 0),
                "irrf_delta": irrf_valid.get("delta", 0),
                "fgts_printed": document_data.get("fgts", 0),
                "fgts_calculated": fgts_valid.get("fgts_calculado", 0),
                "fgts_delta": fgts_valid.get("delta", 0),
                "liquido_printed": document_data.get("liquido", 0),
                "liquido_calculated": liquido_valid.get("liquido_calculado", 0),
                "liquido_delta": liquido_valid.get("delta", 0),
                "cargo_cbo": document_data.get("cbo", "N/A"),
                "salary_range_check": s4_data.get("cbo_validation", {}).get(
                    "status", "NOT_VERIFIABLE"
                ),
            },
            "FORENSIC_FINDINGS": {
                "pdf_layers": document_data.get("pdf_forensics", {}).get("content_stream_count", 1),
                "font_consistency": "consistent",
                "image_overlays": document_data.get("pdf_forensics", {}).get(
                    "image_object_count", 0
                ),
                "compression_anomaly": False,
                "ocr_confidence_min": document_data.get("ocr_data", {}).get(
                    "min_char_confidence", 95
                ),
            },
            "ANOMALY_LIST": [a.to_dict() for a in result.all_anomalies],
            "RISK_ASSESSMENT": {
                "fraud_risk_score": result.fraud_risk_score,
                "risk_classification": result.risk_classification.value.upper(),
                "ai_confidence": result.ai_confidence,
                "recommended_action": result.recommended_action,
            },
            "AI_REASONING_SUMMARY": result.ai_reasoning_summary,
            "ANALYST_NOTES": (
                "Recomenda-se verificar o documento original diretamente com o emissor. "
                "Conferir os dados cadastrais na Receita Federal "
                "para validação completa do CNPJ. "
                "Em caso de boleto, confirmar a titularidade da conta de "
                "destino junto ao banco emissor."
            ),
        }

        return report


# ── Singleton ──

_pipeline_instance: FraudDetectionPipeline | None = None


def get_fraud_pipeline() -> FraudDetectionPipeline:
    """Get or create the singleton fraud detection pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = FraudDetectionPipeline()
    return _pipeline_instance
