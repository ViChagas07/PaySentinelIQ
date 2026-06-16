# ============================================================
# PaySentinelIQ — Company Risk Analyzer
# 10 fraud detection rules applied to BrasilAPI enrichment data.
# Extensible architecture — add new rules without touching existing ones.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.services.enrichment.models import CompanyEnrichment

logger = __import__("logging").getLogger(__name__)


@dataclass
class CompanyRiskRule:
    """A single risk detection rule."""

    name: str
    code: str
    description: str
    severity: str  # info, low, medium, high, critical
    weight: int    # points added to risk score
    check: Callable[..., tuple[bool, str]]


@dataclass
class CompanyRiskResult:
    """Result of company risk analysis."""

    cnpj: str
    risk_score: float = 0.0
    risk_level: str = "LOW"
    flags: list[dict[str, Any]] = field(default_factory=list)
    enrichment: CompanyEnrichment | None = None

    @property
    def flag_count(self) -> int:
        return len(self.flags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cnpj": self.cnpj,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "flags": self.flags,
            "flag_count": self.flag_count,
        }


class CompanyRiskAnalyzer:
    """Deterministic company risk analysis engine.

    Applies 10 fraud detection rules to BrasilAPI enrichment data.
    Extensible: add rules via register_rule() without modifying existing code.
    """

    def __init__(self):
        self._rules: list[CompanyRiskRule] = []
        self._register_default_rules()

    def register_rule(self, rule: CompanyRiskRule) -> None:
        """Register a custom risk rule."""
        self._rules.append(rule)

    def analyze(
        self,
        enrichment: CompanyEnrichment,
        document_context: dict[str, Any] | None = None,
    ) -> CompanyRiskResult:
        """Run all registered rules against enrichment data.

        Args:
            enrichment: Company data from BrasilAPI.
            document_context: Optional document data for cross-validation
                (e.g., extracted company name, amount, location).

        Returns:
            CompanyRiskResult with score, level, and all triggered flags.
        """
        result = CompanyRiskResult(cnpj=enrichment.cnpj, enrichment=enrichment)
        doc = document_context or {}

        for rule in self._rules:
            try:
                triggered, evidence = rule.check(enrichment, doc)
                if triggered:
                    result.flags.append({
                        "code": rule.code,
                        "name": rule.name,
                        "description": rule.description,
                        "severity": rule.severity,
                        "weight": rule.weight,
                        "evidence": evidence,
                    })
                    result.risk_score += rule.weight
            except Exception as e:
                logger.warning("Risk rule '%s' failed: %s", rule.code, e)

        # Cap at 100 and classify
        result.risk_score = min(100.0, result.risk_score)
        result.risk_level = self._classify(result.risk_score)

        # Store flags on enrichment
        enrichment.risk_signals = result.flags

        logger.info(
            "Company risk analysis: cnpj=%s score=%.0f level=%s flags=%d",
            enrichment.cnpj, result.risk_score, result.risk_level, result.flag_count,
        )

        return result

    # ── Default Rules ──

    def _register_default_rules(self) -> None:
        """Register the 10 built-in fraud detection rules."""

        # Rule 1: Inactive company
        self.register_rule(CompanyRiskRule(
            name="Empresa Inativa",
            code="COMPANY_NOT_ACTIVE",
            description="CNPJ is not in 'ATIVA' status with Receita Federal.",
            severity="high",
            weight=40,
            check=lambda e, d: (
                not e.empresa_ativa,
                f"Situação cadastral: {e.situacao_cadastral or 'DESCONHECIDA'}",
            ),
        ))

        # Rule 2: Company closed (baixada)
        self.register_rule(CompanyRiskRule(
            name="Empresa Baixada",
            code="COMPANY_CLOSED",
            description="CNPJ has been officially closed (baixado).",
            severity="critical",
            weight=60,
            check=lambda e, d: (
                e.empresa_baixada,
                f"CNPJ baixado. Data da situação: {e.data_situacao_cadastral or 'N/A'}",
            ),
        ))

        # Rule 3: Very new company (<30 days)
        self.register_rule(CompanyRiskRule(
            name="Empresa Muito Nova",
            code="NEW_COMPANY",
            description="Company was opened less than 30 days ago.",
            severity="high",
            weight=35,
            check=lambda e, d: (
                e.idade_empresa_dias is not None and e.idade_empresa_dias < 30,
                f"Idade da empresa: {e.idade_empresa_dias} dias ({e.data_abertura})",
            ),
        ))

        # Rule 4: Recent company (<90 days)
        self.register_rule(CompanyRiskRule(
            name="Empresa Recente",
            code="RECENT_COMPANY",
            description="Company was opened less than 90 days ago.",
            severity="medium",
            weight=20,
            check=lambda e, d: (
                e.idade_empresa_dias is not None and 30 <= e.idade_empresa_dias < 90,
                f"Idade da empresa: {e.idade_empresa_dias} dias ({e.data_abertura})",
            ),
        ))

        # Rule 5: Low capital + high transaction amount
        self.register_rule(CompanyRiskRule(
            name="Capital Social Suspeito",
            code="LOW_CAPITAL_HIGH_TRANSACTION",
            description="Capital social is very low compared to document amount.",
            severity="medium",
            weight=15,
            check=lambda e, d: (
                e.capital_social is not None
                and e.capital_social < 5000
                and d.get("amount", 0) > 50000,
                f"Capital social: R$ {e.capital_social:,.2f} vs. valor do documento: R$ {d.get('amount', 0):,.2f}",
            ),
        ))

        # Rule 6: Company name mismatch
        self.register_rule(CompanyRiskRule(
            name="Divergência de Nome",
            code="COMPANY_NAME_MISMATCH",
            description="Company name on document differs from Receita Federal registration.",
            severity="high",
            weight=30,
            check=lambda e, d: (
                self._name_mismatch(e.razao_social, d.get("company_name", "")),
                f"Documento: '{d.get('company_name', '')}' vs. Receita: '{e.razao_social}'",
            ),
        ))

        # Rule 7: State mismatch
        self.register_rule(CompanyRiskRule(
            name="UF Divergente",
            code="STATE_MISMATCH",
            description="Document state differs from company's registered state.",
            severity="low",
            weight=10,
            check=lambda e, d: (
                self._state_mismatch(e.uf, d.get("uf", "")),
                f"Documento UF: '{d.get('uf', '')}' vs. Cadastro: '{e.uf}'",
            ),
        ))

        # Rule 8: City mismatch
        self.register_rule(CompanyRiskRule(
            name="Município Divergente",
            code="CITY_MISMATCH",
            description="Document city differs from company's registered city.",
            severity="low",
            weight=10,
            check=lambda e, d: (
                self._city_mismatch(e.municipio, d.get("municipio", "")),
                f"Documento: '{d.get('municipio', '')}' vs. Cadastro: '{e.municipio}'",
            ),
        ))

        # Rule 9: CNPJ not found in BrasilAPI
        self.register_rule(CompanyRiskRule(
            name="CNPJ Não Encontrado",
            code="CNPJ_NOT_FOUND",
            description="CNPJ was not found in Receita Federal database via BrasilAPI.",
            severity="high",
            weight=50,
            check=lambda e, d: (
                not e.is_valid,
                "CNPJ não retornou dados da BrasilAPI — pode ser inválido ou inexistente.",
            ),
        ))

        # Rule 10: Combined risk pattern
        self.register_rule(CompanyRiskRule(
            name="Padrão de Risco Combinado",
            code="COMBINED_RISK_PATTERN",
            description="Multiple risk factors combined: new company + low capital + high amount.",
            severity="critical",
            weight=25,
            check=lambda e, d: (
                (e.idade_empresa_dias is not None and e.idade_empresa_dias < 90)
                and (e.capital_social is not None and e.capital_social < 10000)
                and d.get("amount", 0) > 10000,
                "Empresa recente com capital social baixo e valor de documento elevado.",
            ),
        ))

    # ── Helpers ──

    @staticmethod
    def _name_mismatch(razao: str | None, doc_name: str) -> bool:
        if not razao or not doc_name:
            return False
        # Normalize and compare
        r = razao.upper().strip()
        d = doc_name.upper().strip()
        # If one contains the other, it's a partial match — ignore
        if r in d or d in r:
            return False
        # Check word overlap
        r_words = set(r.split())
        d_words = set(d.split())
        if not r_words or not d_words:
            return False
        overlap = len(r_words & d_words) / max(len(r_words), len(d_words))
        return overlap < 0.3

    @staticmethod
    def _state_mismatch(uf: str | None, doc_uf: str) -> bool:
        if not uf or not doc_uf:
            return False
        return uf.upper().strip() != doc_uf.upper().strip()

    @staticmethod
    def _city_mismatch(municipio: str | None, doc_city: str) -> bool:
        if not municipio or not doc_city:
            return False
        return municipio.upper().strip() != doc_city.upper().strip()

    def _classify(self, score: float) -> str:
        if score >= 76:
            return "CRITICAL"
        elif score >= 51:
            return "HIGH"
        elif score >= 26:
            return "MEDIUM"
        return "LOW"
