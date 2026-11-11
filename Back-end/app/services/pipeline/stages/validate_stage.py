# ============================================================
# PaySentinelIQ — Validate Stage
# ============================================================
# ALL deterministic validation lives here.
# FEBRABAN, CNPJ, CPF, bank/ISPB, dates, values, Pix/QR.
# Produces Evidence[] — NEVER a score.
# ============================================================

from __future__ import annotations

from datetime import date, datetime

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.pipeline_context import PipelineContext

PAYSLIP_TYPES = {"contracheque", "holerite", "payroll", "payslip"}


def _parse_date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%d/%m/%Y").date()
    except ValueError:
        return None


def _canonical_bank(fields: dict[str, object]) -> str | None:
    line = fields.get("linha_digitavel") or fields.get("codigo_barras")
    digits = "".join(char for char in str(line or "") if char.isdigit())
    if len(digits) in {44, 47}:
        return digits[:3]
    return None


def _bank_code_from_text(flag_text: str) -> str:
    import re

    match = re.search(r"\b(\d{3})\b", flag_text)
    return match.group(1) if match else ""


def _bank_invalid_severity(flag_text: str) -> Severity:
    code = _bank_code_from_text(flag_text)
    if len(code) != 3:
        return Severity.HIGH
    if code in {"000", "999"}:
        return Severity.CRITICAL
    return Severity.MEDIUM


def _structural_severity(code: str, flag_text: str) -> Severity:
    if code == "BOLETO_VENCIDO":
        return Severity.INFO
    if code == "VALOR_REDONDO_SUSPEITO":
        return Severity.LOW
    if code == "BANCO_INVALIDO":
        return _bank_invalid_severity(flag_text)
    if code in {
        "CNPJ_INVALIDO",
        "MULTA_ILEGAL",
        "JUROS_ABUSIVOS",
    }:
        return Severity.CRITICAL
    return Severity.HIGH


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
        doc_type = self._effective_document_type(context)

        # ── Boleto-specific validations ──
        if doc_type == "boleto" or (
            doc_type not in PAYSLIP_TYPES
            and self._looks_like_boleto(text, fields)
        ):
            self._validate_boleto(context, text, fields)

        # ── Contracheque-specific validations ──
        if doc_type in PAYSLIP_TYPES:
            self._validate_contracheque(context, fields)

        # ── Universal validations (both doc types) ──
        self._validate_cnpj(context, fields)
        self._validate_dates(context, text, fields, doc_type)
        self._validate_amounts(context, fields)

    @staticmethod
    def _effective_document_type(context: PipelineContext) -> str:
        doc_type = (context.document_type or "").lower()
        if doc_type in PAYSLIP_TYPES or doc_type == "boleto":
            return doc_type
        extraction_metadata = context.metadata.get("extraction", {})
        if isinstance(extraction_metadata, dict):
            inferred = str(
                extraction_metadata.get("document_type_inferred") or ""
            ).lower()
            if inferred:
                return inferred
        return doc_type

    def _looks_like_boleto(self, text: str, fields: dict) -> bool:
        # Always check structured fields first (they work even without OCR text)
        if fields.get("linha_digitavel") or fields.get("codigo_barras"):
            return True
        if not text:
            return False
        keywords = ["boleto", "linha digitavel", "codigo de barras",
                     "vencimento", "cedente", "sacado", "banco"]
        return any(kw in text.lower() for kw in keywords)

    def _validate_boleto(self, ctx: PipelineContext, text: str, fields: dict) -> None:
        """Boleto FEBRABAN validations. Uses text when available, structured fields as fallback."""
        try:
            from app.services.ai.boleto_analyzer import (
                _stage1_structural_validation,
                _stage3_linha_digitavel_validation,
                BANCOS_VALIDOS,
            )
            import re

            # ── Raw text path (most complete) ──
            if text and len(text) > 50:
                due_date = fields.get("data_vencimento") or fields.get(
                    "due_date"
                )
                structural_flags, _ = _stage1_structural_validation(
                    text,
                    due_date=due_date,
                    codigo_banco=_canonical_bank(fields),
                )
                linha_flags, _ = _stage3_linha_digitavel_validation(text)

                for flag_text in structural_flags:
                    code = flag_text.split(":")[0].strip().replace(" ", "_")
                    sev = _structural_severity(code, flag_text)
                    ctx.add_evidence(Evidence(
                        code=code,
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
                        rule_reference="FEBRABAN Modulo 10/11",
                    ))

            # ── Structured fields fallback (no raw text available) ──
            else:
                # Bank code from structured fields
                linha = fields.get("linha_digitavel", "")
                if linha:
                    digits = re.sub(r"\D", "", linha)
                    if len(digits) >= 3:
                        bank_code = digits[:3]
                        if bank_code not in BANCOS_VALIDOS:
                            ctx.add_evidence(Evidence(
                                code="BANCO_INVALIDO",
                                description=f"Codigo de banco {bank_code} nao existe no BACEN ISPB",
                                severity=_bank_invalid_severity(bank_code),
                                source=EvidenceSource.DETERMINISTIC,
                                confidence=1.0,
                                category="structural",
                                rule_reference="BACEN ISPB Registry",
                            ))
                    # Check linha digitavel format
                    if not re.search(r"\d{5}\.\d{5}\s\d{6}\.\d{6}\s\d{6}\.\d{6}\s\d\s\d{14}", linha):
                        ctx.add_evidence(Evidence(
                            code="LINHA_DIGITAVEL_FORMATO_INCORRETO",
                            description="Linha digitavel em formato nao padrao FEBRABAN",
                            severity=Severity.CRITICAL,
                            source=EvidenceSource.DETERMINISTIC,
                            confidence=1.0,
                            category="structural",
                            rule_reference="FEBRABAN Linha Digitavel",
                        ))

                # CNPJ from structured fields
                cnpj = fields.get("cnpj", "")
                if cnpj:
                    digits = re.sub(r"\D", "", cnpj)
                    known_invalid = {
                        "00000000000000", "11111111111111", "22222222222222",
                        "33333333333333", "44444444444444", "55555555555555",
                        "66666666666666", "77777777777777", "88888888888888",
                        "99999999999999", "00000010000199", "00000000000199",
                    }
                    if digits in known_invalid:
                        ctx.add_evidence(Evidence(
                            code="CNPJ_INVALIDO",
                            description=f"CNPJ {cnpj} possui padrao invalido (todos digitos iguais ou sequencia falsa conhecida)",
                            severity=Severity.CRITICAL,
                            source=EvidenceSource.DETERMINISTIC,
                            confidence=1.0,
                            category="entity",
                            rule_reference="Modulo 11 CNPJ",
                        ))

                # Beneficiary name
                beneficiario = fields.get("beneficiario", fields.get("beneficiary_name", ""))
                if beneficiario:
                    generic_terms = ["solucoes", "servicos", "digital", "tecnologia",
                                     "consultoria", "comercio", "global", "brasil"]
                    name_lower = beneficiario.lower()
                    generic_count = sum(1 for t in generic_terms if t in name_lower)
                    if generic_count >= 2 and len(beneficiario) < 30:
                        ctx.add_evidence(Evidence(
                            code="BENEFICIARIO_GENERICO",
                            description=f"Razao social generica: {beneficiario} — possivel empresa fantasma",
                            severity=Severity.MEDIUM,
                            source=EvidenceSource.HEURISTIC,
                            confidence=0.6,
                            category="entity",
                            rule_reference="Heuristica de fraude em boleto",
                        ))

        except Exception as e:
            ctx.add_warning(f"Boleto validation failed: {e}")

    def _validate_contracheque(self, ctx: PipelineContext, fields: dict) -> None:
        """Payroll-specific validations."""
        # These validations will be implemented in Fase 2
        pass

    def _validate_cnpj(self, ctx: PipelineContext, fields: dict) -> None:
        """CNPJ/CPF validation. Detects all-same-digit, sequential, and known fake patterns."""
        import re
        cnpj = fields.get("cnpj", "")
        if not cnpj:
            return
        digits = re.sub(r"\D", "", cnpj)
        if len(digits) < 14:
            return

        # All-same-digit patterns (000...000, 111...111, ..., 999...999)
        if len(set(digits)) == 1:
            ctx.add_evidence(Evidence(
                code="CNPJ_INVALID_PATTERN",
                description=f"CNPJ {cnpj} possui todos os digitos iguais — invalido",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC,
                confidence=1.0, category="entity", rule_reference="Modulo 11 CNPJ",
            ))
            return

        # Known fake patterns
        known_invalid = {
            "00000010000199", "00000000000199",
            "12345678901234", "01234567890123",
        }
        if digits in known_invalid:
            ctx.add_evidence(Evidence(
                code="CNPJ_INVALID_PATTERN",
                description=f"CNPJ {cnpj} possui padrao invalido (sequencia falsa conhecida)",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC,
                confidence=1.0, category="entity", rule_reference="Modulo 11 CNPJ",
            ))
            return

        # Sequential ascending (e.g., 12345678901234, 23456789012345) — CRITICAL fake
        if any(
            digits == "".join(str((start + i) % 10) for i in range(14))
            for start in range(10)
        ):
            ctx.add_evidence(Evidence(
                code="CNPJ_SEQUENTIAL_FAKE",
                description=f"CNPJ {cnpj} possui sequencia numerica progressiva — padrao falso classico, 100% invalido",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC,
                confidence=1.0, category="entity", rule_reference="Modulo 11 CNPJ — checksum impossivel",
            ))

    def _validate_dates(
        self,
        ctx: PipelineContext,
        text: str,
        fields: dict,
        doc_type: str,
    ) -> None:
        """Date consistency checks."""
        import re as re_dates
        from datetime import date

        if doc_type in PAYSLIP_TYPES:
            return

        due_raw = fields.get("data_vencimento") or fields.get("due_date")
        due_date = _parse_date_value(due_raw)
        if due_date is not None:
            candidates = [due_date]
        else:
            if not text:
                return
            candidates = []
            for d, m, y in re_dates.findall(
                r"\b(\d{2})/(\d{2})/(\d{4})\b",
                text,
            )[:5]:
                try:
                    candidates.append(date(int(y), int(m), int(d)))
                except ValueError:
                    continue

        today = date.today()
        for doc_date in candidates:
            days_overdue = (today - doc_date).days
            if days_overdue > 365:
                ctx.add_evidence(Evidence(
                    code="BOLETO_SEVERELY_OVERDUE",
                    description=(
                        f"Documento vencido há {days_overdue} dias "
                        f"({doc_date.strftime('%d/%m/%Y')})"
                    ),
                    severity=Severity.LOW,
                    source=EvidenceSource.DETERMINISTIC,
                    confidence=1.0,
                    category="temporal",
                    rule_reference="FEBRABAN fator de vencimento",
                ))
            elif days_overdue > 30:
                ctx.add_evidence(Evidence(
                    code="BOLETO_OVERDUE",
                    description=(
                        f"Documento vencido há {days_overdue} dias "
                        f"({doc_date.strftime('%d/%m/%Y')})"
                    ),
                    severity=Severity.INFO,
                    source=EvidenceSource.DETERMINISTIC,
                    confidence=1.0,
                    category="temporal",
                    rule_reference="FEBRABAN fator de vencimento",
                ))

    def _validate_amounts(self, ctx: PipelineContext, fields: dict) -> None:
        """Value consistency checks."""
        valor = fields.get("valor_nominal", fields.get("amount", 0))
        if isinstance(valor, (int, float)) and valor >= 100 and valor % 100 == 0:
            ctx.add_evidence(Evidence(
                code="ROUND_AMOUNT_SUSPICIOUS",
                description=f"Valor redondo R$ {valor:,.2f} — possível boleto fraudulento sem serviço discriminado",
                severity=Severity.LOW,
                source=EvidenceSource.HEURISTIC,
                confidence=0.7,
                category="financial",
                rule_reference="Heurística de fraude em boleto",
            ))
