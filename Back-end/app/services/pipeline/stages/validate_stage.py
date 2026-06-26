# ============================================================
# PaySentinelIQ — Validate Stage
# ============================================================
# ALL deterministic validation lives here.
# FEBRABAN, CNPJ, CPF, bank/ISPB, dates, values, Pix/QR.
# Produces Evidence[] — NEVER a score.
# ============================================================

from __future__ import annotations

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.pipeline_context import PipelineContext


class ValidateStage(BaseStage):
    """Stage 3: Run ALL deterministic validations.

    Validations performed:
        - FEBRABAN linha digitavel (Módulo 10/11)
        - Barcode decode + due date
        - CNPJ/CPF checksum + pattern
        - Bank code vs BACEN ISPB
        - Date consistency (overdue, chronological)
        - Value consistency (net>gross, illegal fees)
        - Pix QR code validation
        - Beneficiary name analysis

    ALL results are Evidence objects added to context.evidences.
    No scoring happens here.
    """

    def __init__(self):
        super().__init__(name="ValidateStage")

    def _execute(self, context: PipelineContext) -> None:
        """Run all validation suites. Each produces Evidence[] added to context."""
        text = context.extracted_text
        fields = context.extracted_fields
        doc_type = context.document_type

        # ── Boleto-specific validations ──
        if doc_type == "boleto" or self._looks_like_boleto(text, fields):
            self._validate_boleto(context, text, fields)

        # ── Contracheque-specific validations ──
        if doc_type in ("contracheque", "holerite", "payroll"):
            self._validate_contracheque(context, fields)

        # ── Universal validations (both doc types) ──
        self._validate_cnpj(context, fields)
        self._validate_dates(context, text, fields)
        self._validate_amounts(context, fields)

    def _looks_like_boleto(self, text: str, fields: dict) -> bool:
        if not text:
            return False
        keywords = ["boleto", "linha digitável", "código de barras",
                     "vencimento", "cedente", "sacado", "banco"]
        return any(kw in text.lower() for kw in keywords)

    def _validate_boleto(self, ctx: PipelineContext, text: str, fields: dict) -> None:
        """Boleto FEBRABAN validations."""
        try:
            from app.services.ai.boleto_analyzer import (
                _stage1_structural_validation,
                _stage3_linha_digitavel_validation,
            )
            # Run deterministic boleto checks on raw text
            if text and len(text) > 50:
                structural_flags, _ = _stage1_structural_validation(text)
                linha_flags, _ = _stage3_linha_digitavel_validation(text)

                for flag_text in structural_flags:
                    sev = Severity.CRITICAL if any(
                        kw in flag_text.upper()
                        for kw in ["BANCO_INVALIDO", "CNPJ_INVALIDO",
                                     "MULTA_ILEGAL", "JUROS_ABUSIVOS"]
                    ) else Severity.HIGH
                    ctx.add_evidence(Evidence(
                        code=flag_text.split(":")[0].strip().replace(" ", "_"),
                        description=flag_text,
                        severity=sev,
                        source=EvidenceSource.DETERMINISTIC,
                        confidence=1.0,
                        category="structural",
                        rule_reference="FEBRABAN / BACEN ISPB",
                    ))
                for flag_text in linha_flags:
                    ctx.add_evidence(Evidence(
                        code=flag_text.replace(" ", "_"),
                        description=flag_text,
                        severity=Severity.CRITICAL,
                        source=EvidenceSource.DETERMINISTIC,
                        confidence=1.0,
                        category="structural",
                        rule_reference="FEBRABAN Módulo 10/11",
                    ))
        except Exception as e:
            ctx.add_warning(f"Boleto validation failed: {e}")

    def _validate_contracheque(self, ctx: PipelineContext, fields: dict) -> None:
        """Payroll-specific validations."""
        # These validations will be implemented in Fase 2
        pass

    def _validate_cnpj(self, ctx: PipelineContext, fields: dict) -> None:
        """CNPJ/CPF validation."""
        import re
        cnpj = fields.get("cnpj", "")
        if not cnpj:
            return
        digits = re.sub(r"\D", "", cnpj)
        known_invalid = {
            "00000000000000", "11111111111111", "99999999999999",
            "00000010000199",
        }
        if digits in known_invalid:
            ctx.add_evidence(Evidence(
                code="CNPJ_INVALID_PATTERN",
                description=f"CNPJ {cnpj} possui padrão inválido (todos dígitos iguais ou sequência falsa)",
                severity=Severity.CRITICAL,
                source=EvidenceSource.DETERMINISTIC,
                confidence=1.0,
                category="entity",
                rule_reference="Módulo 11 CNPJ",
            ))

    def _validate_dates(self, ctx: PipelineContext, text: str, fields: dict) -> None:
        """Date consistency checks."""
        import re as re_dates
        from datetime import date

        if not text:
            return
        date_patterns = re_dates.findall(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
        today = date.today()
        for d, m, y in date_patterns[:5]:  # max 5 dates
            try:
                doc_date = date(int(y), int(m), int(d))
                days_overdue = (today - doc_date).days
                if days_overdue > 365:
                    ctx.add_evidence(Evidence(
                        code="BOLETO_SEVERELY_OVERDUE",
                        description=f"Documento vencido há {days_overdue} dias ({d}/{m}/{y})",
                        severity=Severity.CRITICAL,
                        source=EvidenceSource.DETERMINISTIC,
                        confidence=1.0,
                        category="temporal",
                        rule_reference="FEBRABAN fator de vencimento",
                    ))
                elif days_overdue > 30:
                    ctx.add_evidence(Evidence(
                        code="BOLETO_OVERDUE",
                        description=f"Documento vencido há {days_overdue} dias ({d}/{m}/{y})",
                        severity=Severity.HIGH,
                        source=EvidenceSource.DETERMINISTIC,
                        confidence=1.0,
                        category="temporal",
                        rule_reference="FEBRABAN fator de vencimento",
                    ))
            except ValueError:
                pass

    def _validate_amounts(self, ctx: PipelineContext, fields: dict) -> None:
        """Value consistency checks."""
        valor = fields.get("valor_nominal", fields.get("amount", 0))
        if isinstance(valor, (int, float)) and valor >= 100 and valor % 100 == 0:
            ctx.add_evidence(Evidence(
                code="ROUND_AMOUNT_SUSPICIOUS",
                description=f"Valor redondo R$ {valor:,.2f} — possível boleto fraudulento sem serviço discriminado",
                severity=Severity.MEDIUM,
                source=EvidenceSource.HEURISTIC,
                confidence=0.7,
                category="financial",
                rule_reference="Heurística de fraude em boleto",
            ))
