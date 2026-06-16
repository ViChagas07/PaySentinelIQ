# ============================================================
# PaySentinelIQ — Enrichment Service
# Orchestrates BrasilAPI fetch → enrichment → risk analysis.
# ============================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.services.enrichment.brasilapi_client import BrasilApiClient, BrasilApiError
from app.services.enrichment.models import CompanyEnrichment
from app.services.enrichment.company_risk_analyzer import (
    CompanyRiskAnalyzer,
    CompanyRiskResult,
)

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service that orchestrates CNPJ enrichment and risk analysis.

    Flow:
        1. Sanitize CNPJ
        2. Fetch from BrasilAPI (with Redis cache)
        3. Compute age, status
        4. Run risk analyzer (10 rules)
        5. Return enriched data + risk score
    """

    def __init__(
        self,
        brasilapi_client: BrasilApiClient | None = None,
        risk_analyzer: CompanyRiskAnalyzer | None = None,
    ):
        self._brasilapi = brasilapi_client or BrasilApiClient()
        self._risk_analyzer = risk_analyzer or CompanyRiskAnalyzer()

    async def enrich(
        self,
        cnpj: str,
        document_context: dict[str, Any] | None = None,
    ) -> tuple[CompanyEnrichment | None, CompanyRiskResult | None]:
        """Enrich a CNPJ with BrasilAPI data and run risk analysis.

        Args:
            cnpj: CNPJ to look up (formatted or raw).
            document_context: Optional document data for cross-validation.

        Returns:
            Tuple of (CompanyEnrichment, CompanyRiskResult). Both may be None
            if the CNPJ is invalid or BrasilAPI is unreachable.
        """
        # Sanitize
        clean_cnpj = BrasilApiClient.sanitize_cnpj(cnpj)
        if not clean_cnpj or len(clean_cnpj) != 14:
            logger.warning("Invalid CNPJ for enrichment: %s", cnpj)
            return None, None

        enrichment = CompanyEnrichment(cnpj=clean_cnpj)

        # Fetch from BrasilAPI
        try:
            company = await self._brasilapi.get_cnpj(clean_cnpj)
        except BrasilApiError as e:
            logger.error("BrasilAPI failed for CNPJ %s: %s", clean_cnpj, e)
            # Still return enrichment with CNPJ_NOT_FOUND-like result
            enrichment.fetched_at = datetime.now(timezone.utc).isoformat()
            risk = self._risk_analyzer.analyze(enrichment, document_context or {})
            return enrichment, risk

        if company is None:
            # CNPJ not found
            enrichment.fetched_at = datetime.now(timezone.utc).isoformat()
            risk = self._risk_analyzer.analyze(enrichment, document_context or {})
            return enrichment, risk

        # Map BrasilAPI data to enrichment model
        enrichment.razao_social = company.razao_social
        enrichment.nome_fantasia = company.nome_fantasia
        enrichment.situacao_cadastral = company.situacao_cadastral
        enrichment.cnae = company.cnae_fiscal
        enrichment.cnae_descricao = company.cnae_fiscal_descricao
        enrichment.municipio = company.municipio
        enrichment.uf = company.uf
        enrichment.porte = company.porte
        enrichment.natureza_juridica = company.natureza_juridica
        enrichment.capital_social = company.capital_social
        enrichment.data_abertura = company.data_abertura
        enrichment.data_situacao_cadastral = company.data_situacao_cadastral
        enrichment.cep = company.cep
        enrichment.telefone = company.ddd_telefone_1
        enrichment.email = company.email
        enrichment.fetched_at = datetime.now(timezone.utc).isoformat()

        # Compute derived fields
        enrichment.compute_age()
        enrichment.compute_status()

        # Run risk analysis
        risk = self._risk_analyzer.analyze(enrichment, document_context or {})

        logger.info(
            "CNPJ enriched: %s — %s — score=%.0f (%s) — %d flags",
            clean_cnpj,
            enrichment.razao_social,
            risk.risk_score,
            risk.risk_level,
            risk.flag_count,
        )

        return enrichment, risk

    async def enrich_for_context(
        self,
        cnpj: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Enrich a FraudAnalysisContext dict with company data.

        Modifies the context dict in-place with enrichment data.
        """
        enrichment, risk = await self.enrich(cnpj, context)

        if enrichment:
            context["company_enrichment"] = enrichment.to_dict()
            context["company_name"] = enrichment.razao_social or context.get("company_name")
            context["cnpj_valid"] = enrichment.is_valid and enrichment.empresa_ativa
            context["cnpj_active"] = enrichment.empresa_ativa

        if risk:
            context["company_risk_score"] = risk.risk_score
            context["company_risk_level"] = risk.risk_level
            if risk.flags:
                existing_flags = context.get("risk_flags", [])
                context["risk_flags"] = existing_flags + risk.flags
                context["risk_score"] = max(
                    context.get("risk_score", 0),
                    risk.risk_score,
                )

        return context

    async def close(self) -> None:
        await self._brasilapi.close()
