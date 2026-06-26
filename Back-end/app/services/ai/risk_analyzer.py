# ============================================================
# PaySentinelIQ — Deterministic Risk Analyzer
# Pre-LLM risk engine that runs BEFORE the AI copilot.
# Pure business logic — no AI/LLM dependency.
# ============================================================

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskFlag:
    """A single risk flag detected by the deterministic engine."""

    code: str
    description: str
    severity: str  # "info", "low", "medium", "high", "critical"
    category: str  # "entity", "financial", "document", "date", "duplicate"
    evidence: str = ""


@dataclass
class RiskAssessment:
    """Result of the deterministic risk analysis."""

    risk_score: float = 0.0
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    flags: list[RiskFlag] = field(default_factory=list)

    @property
    def flag_count(self) -> int:
        return len(self.flags)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.flags if f.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.flags if f.severity == "high")


class RiskAnalyzer:
    """Deterministic pre-LLM risk analysis engine.

    Runs BEFORE the AI copilot. Uses pure business rules — no LLM calls.
    Produces risk_score (0-100) and risk_flags that feed into the FraudAnalysisContext.

    Risk levels (CALIBRATED 2025-06-25 for fraud detection — skeptical bias):
      0-39   → LOW
      40-69  → MEDIUM
      70-100 → HIGH
    Note: CRITICAL is now merged into HIGH. Any CRITICAL flag → immediate HIGH.
    """

    # ── Severity weights for scoring ──
    # Increased weights to ensure fraud signals are not buried
    SEVERITY_WEIGHTS = {
        "critical": 35,   # Was 25 — single critical flag now pushes into HIGH range
        "high": 20,       # Was 15
        "medium": 10,     # Was 8  — two medium flags = 20, enough for MEDIUM range
        "low": 5,         # Was 3
        "info": 2,        # Was 1
    }

    def analyze(self, context: dict[str, Any]) -> RiskAssessment:
        """Run all deterministic risk checks against the provided context.

        Args:
            context: Dict with fields like cnpj, amount, dates, document metadata, etc.

        Returns:
            RiskAssessment with score and flags.
        """
        flags: list[RiskFlag] = []

        # ── Entity checks ──
        flags.extend(self._check_cnpj(context))
        flags.extend(self._check_company_name(context))

        # ── Financial checks ──
        flags.extend(self._check_amount(context))
        flags.extend(self._check_salary_consistency(context))
        flags.extend(self._check_tax_consistency(context))

        # ── Document checks ──
        flags.extend(self._check_document_tampering(context))
        flags.extend(self._check_ocr_quality(context))

        # ── Date checks ──
        flags.extend(self._check_dates(context))

        # ── Boleto-specific checks ──
        flags.extend(self._check_boleto(context))

        # ── Calculate score ──
        score = self._calculate_score(flags)

        # ── Classify risk level ──
        level = self._classify_level(score)

        return RiskAssessment(risk_score=score, risk_level=level, flags=flags)

    # ── Entity Checks ──

    def _check_cnpj(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        cnpj = ctx.get("cnpj") or ctx.get("company_cnpj")
        cnpj_valid = ctx.get("cnpj_valid")
        cnpj_active = ctx.get("cnpj_active")
        receita = ctx.get("receita_federal_status", "")

        if cnpj and cnpj_valid is False:
            flags.append(RiskFlag(
                code="CNPJ_INVALID",
                description=f"CNPJ {cnpj} failed checksum validation (Módulo 11).",
                severity="critical",
                category="entity",
                evidence=f"CNPJ checksum validation returned invalid for {cnpj}.",
            ))
        elif cnpj and cnpj_active is False:
            flags.append(RiskFlag(
                code="CNPJ_INACTIVE",
                description=f"CNPJ {cnpj} is marked as inactive/inapto.",
                severity="high",
                category="entity",
                evidence=f"Receita Federal status: {receita or 'INACTIVE'}.",
            ))
        elif cnpj and cnpj_valid is None and receita == "NOT_VERIFIED":
            flags.append(RiskFlag(
                code="CNPJ_NOT_VERIFIED",
                description=f"CNPJ {cnpj} could not be verified against Receita Federal.",
                severity="low",
                category="entity",
                evidence="External CNPJ verification was not performed or is unavailable.",
            ))

        return flags

    def _check_company_name(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        company = ctx.get("company_name") or ctx.get("razao_social")
        beneficiary = ctx.get("beneficiary_name") or ctx.get("beneficiario")

        if company and beneficiary and company.strip().upper() != beneficiary.strip().upper():
            flags.append(RiskFlag(
                code="BENEFICIARY_MISMATCH",
                description=f"Company name '{company}' does not match beneficiary '{beneficiary}'.",
                severity="high",
                category="entity",
                evidence=f"Document lists beneficiary as '{beneficiary}' but company is '{company}'.",
            ))

        return flags

    # ── Financial Checks ──

    def _check_amount(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        amount = ctx.get("amount") or ctx.get("valor_nominal")

        if amount is not None:
            if amount <= 0:
                flags.append(RiskFlag(
                    code="AMOUNT_ZERO_OR_NEGATIVE",
                    description=f"Amount R$ {amount:.2f} is zero or negative — invalid for a financial document.",
                    severity="critical",
                    category="financial",
                    evidence=f"Document amount field contains {amount}.",
                ))
            elif amount > 1_000_000:
                flags.append(RiskFlag(
                    code="AMOUNT_UNUSUALLY_HIGH",
                    description=f"Amount R$ {amount:,.2f} exceeds R$ 1,000,000 — verify legitimacy.",
                    severity="medium",
                    category="financial",
                    evidence=f"Document shows amount of R$ {amount:,.2f}.",
                ))

        return flags

    def _check_salary_consistency(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        gross = ctx.get("gross_salary") or ctx.get("salario_bruto")
        net = ctx.get("net_salary") or ctx.get("liquido")

        if gross is not None and net is not None and gross > 0:
            ratio = net / gross
            if ratio > 1.0:
                flags.append(RiskFlag(
                    code="NET_EXCEEDS_GROSS",
                    description=f"Net salary R$ {net:,.2f} exceeds gross salary R$ {gross:,.2f} — impossible.",
                    severity="critical",
                    category="financial",
                    evidence=f"Gross: R$ {gross:,.2f}, Net: R$ {net:,.2f}.",
                ))
            elif ratio < 0.3:
                flags.append(RiskFlag(
                    code="NET_TOO_LOW",
                    description=f"Net salary is only {ratio:.0%} of gross — unusually low.",
                    severity="medium",
                    category="financial",
                    evidence=f"Gross: R$ {gross:,.2f}, Net: R$ {net:,.2f} (ratio: {ratio:.1%}).",
                ))

        return flags

    def _check_tax_consistency(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        gross = ctx.get("gross_salary") or ctx.get("salario_bruto")
        inss = ctx.get("inss_amount") or ctx.get("inss")

        if gross is not None and inss is not None and gross > 0:
            if inss > gross * 0.15:
                flags.append(RiskFlag(
                    code="INSS_UNUSUALLY_HIGH",
                    description=f"INSS of R$ {inss:,.2f} is >15% of gross salary — above legal maximum.",
                    severity="medium",
                    category="financial",
                    evidence=f"INSS: R$ {inss:,.2f}, Gross: R$ {gross:,.2f}.",
                ))

        return flags

    # ── Document Integrity Checks ──

    def _check_document_tampering(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        layers = ctx.get("pdf_layers")
        font_issue = ctx.get("font_inconsistency")
        creation = ctx.get("creation_date")
        modification = ctx.get("modification_date")

        if layers is not None and layers > 2:
            flags.append(RiskFlag(
                code="PDF_MULTI_LAYER",
                description=f"PDF has {layers} layers — possible content overlay or tampering.",
                severity="high",
                category="document",
                evidence=f"PDF forensic analysis detected {layers} distinct layers.",
            ))

        if font_issue:
            flags.append(RiskFlag(
                code="FONT_INCONSISTENCY",
                description="Multiple inconsistent fonts detected — possible field injection.",
                severity="high",
                category="document",
                evidence="Font analysis detected serif and sans-serif mixing or unusual font metrics.",
            ))

        if creation and modification and creation > modification:
            flags.append(RiskFlag(
                code="DATE_ANOMALY",
                description="Document creation date is AFTER modification date — metadata tampering.",
                severity="high",
                category="document",
                evidence=f"Created: {creation}, Modified: {modification}.",
            ))

        return flags

    def _check_ocr_quality(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        ocr_conf = ctx.get("ocr_confidence")

        if ocr_conf is not None:
            if ocr_conf < 60:
                flags.append(RiskFlag(
                    code="OCR_VERY_LOW",
                    description=f"OCR confidence is {ocr_conf:.0f}% — text may be unreliable.",
                    severity="medium",
                    category="document",
                    evidence=f"OCR confidence score: {ocr_conf:.1f}%.",
                ))
            elif ocr_conf < 80:
                flags.append(RiskFlag(
                    code="OCR_MODERATE",
                    description=f"OCR confidence is {ocr_conf:.0f}% — verify critical fields manually.",
                    severity="low",
                    category="document",
                    evidence=f"OCR confidence score: {ocr_conf:.1f}%.",
                ))

        return flags

    # ── Date Checks ──

    def _check_dates(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        try:
            from datetime import datetime, timezone

            due_str = ctx.get("due_date")
            issue_str = ctx.get("issue_date")

            if due_str:
                due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)

                if due_date < now:
                    flags.append(RiskFlag(
                        code="DOCUMENT_EXPIRED",
                        description=f"Document due date {due_str} is in the past.",
                        severity="low",
                        category="date",
                        evidence=f"Due date: {due_str}, current date: {now.date().isoformat()}.",
                    ))

            if issue_str and due_str:
                issue_date = datetime.fromisoformat(issue_str.replace("Z", "+00:00"))
                due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                if issue_date > due_date:
                    flags.append(RiskFlag(
                        code="ISSUE_AFTER_DUE",
                        description=f"Issue date {issue_str} is after due date {due_str}.",
                        severity="medium",
                        category="date",
                        evidence=f"Issue: {issue_str}, Due: {due_str}.",
                    ))
        except (ValueError, TypeError):
            flags.append(RiskFlag(
                code="DATE_PARSE_ERROR",
                description="Could not parse one or more dates — format may be invalid.",
                severity="low",
                category="date",
                evidence="Date parsing failed for provided date strings.",
            ))

        return flags

    # ── Boleto Checks (EXPANDED 2025-06-25) ──

    def _check_boleto(self, ctx: dict[str, Any]) -> list[RiskFlag]:
        flags = []
        doc_type = ctx.get("document_type", "")
        checksum = ctx.get("checksum_valid")
        bank_valid = ctx.get("bank_valid")
        bank_code = ctx.get("bank_code", "")

        if doc_type in ("boleto", "bank-slip", "bank_slip"):
            # Check barcode checksum
            if checksum is False:
                flags.append(RiskFlag(
                    code="BOLETO_CHECKSUM_FAILED",
                    description=(
                        "Boleto barcode checksum validation failed "
                        "(FEBRABAN Modulo 10/11) — possible tampering."
                    ),
                    severity="critical",
                    category="document",
                    evidence="FEBRABAN Modulo 10/11 checksum returned invalid.",
                ))

            # Check bank code validity
            if bank_valid is False:
                flags.append(RiskFlag(
                    code="BANK_CODE_INVALID",
                    description=(
                        f"Bank code '{bank_code}' is not registered in "
                        "BACEN ISPB registry — possible fabricated boleto."
                    ),
                    severity="critical",
                    category="entity",
                    evidence=(
                        f"BACEN bank validation returned invalid for "
                        f"bank code: {bank_code}."
                    ),
                ))

            # Check for overdue boleto
            due_date_str = ctx.get("due_date")
            if due_date_str:
                try:
                    from datetime import datetime, timezone
                    due_date = datetime.fromisoformat(
                        due_date_str.replace("Z", "+00:00")
                    )
                    now = datetime.now(timezone.utc)
                    days_overdue = (now - due_date).days
                    if days_overdue > 365:
                        flags.append(RiskFlag(
                            code="BOLETO_SEVERELY_OVERDUE",
                            description=(
                                f"Boleto vencido há mais de 1 ano "
                                f"({days_overdue} dias). Altamente suspeito."
                            ),
                            severity="critical",
                            category="date",
                            evidence=(
                                f"Due date: {due_date_str}, "
                                f"{days_overdue} days overdue."
                            ),
                        ))
                    elif days_overdue > 30:
                        flags.append(RiskFlag(
                            code="BOLETO_OVERDUE",
                            description=(
                                f"Boleto vencido há {days_overdue} dias. "
                                "Verificar legitimidade."
                            ),
                            severity="high",
                            category="date",
                            evidence=(
                                f"Due date: {due_date_str}, "
                                f"{days_overdue} days overdue."
                            ),
                        ))
                except (ValueError, TypeError):
                    pass

            # Check for suspiciously round amounts
            amount = ctx.get("amount") or ctx.get("valor_nominal")
            if amount is not None and amount >= 100 and amount % 100 == 0:
                flags.append(RiskFlag(
                    code="BOLETO_ROUND_AMOUNT",
                    description=(
                        f"Valor do boleto (R$ {amount:,.2f}) é redondo — "
                        "comum em boletos fraudulentos sem serviço discriminado."
                    ),
                    severity="medium",
                    category="financial",
                    evidence=f"Amount: R$ {amount:,.2f}",
                ))

        return flags

    # ── Scoring ──

    def _calculate_score(self, flags: list[RiskFlag]) -> float:
        """Calculate risk score from flags with severity-weighted accumulation.

        Uses calibrated weights that ensure fraud signals aren't buried.
        """
        if not flags:
            return 0.0

        total = 0.0
        for flag in flags:
            total += self.SEVERITY_WEIGHTS.get(flag.severity, 1)

        # Count critical flags — each additional critical adds a multiplier
        critical_count = sum(1 for f in flags if f.severity == "critical")
        if critical_count >= 2:
            # Multiple criticals → compound effect
            total *= 1.5

        # Cap at 100
        return min(100.0, total)

    def _classify_level(self, score: float) -> str:
        """Calibrated thresholds for fraud detection (skeptical bias).

        LOW:    0-39  — No critical indicators
        MEDIUM: 40-69 — At least one concerning indicator
        HIGH:   70+   — Multiple indicators or one CRITICAL
        """
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        return "LOW"
