# ============================================================
# PaySentinelIQ — Enrichment + Risk Analyzer Tests
# ============================================================

import pytest
from datetime import datetime, timezone, timedelta

from app.services.enrichment.models import CompanyEnrichment
from app.services.enrichment.company_risk_analyzer import CompanyRiskAnalyzer


def make_enrichment(**overrides) -> CompanyEnrichment:
    """Factory for test CompanyEnrichment objects."""
    defaults = {
        "cnpj": "12345678000199",
        "razao_social": "Empresa Teste Ltda",
        "nome_fantasia": "Teste",
        "situacao_cadastral": "ATIVA",
        "cnae": "6201501",
        "cnae_descricao": "Desenvolvimento de software",
        "municipio": "São Paulo",
        "uf": "SP",
        "porte": "ME",
        "capital_social": 50000.0,
        "data_abertura": (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(),
        "data_situacao_cadastral": None,
        "cep": "01310100",
    }
    defaults.update(overrides)
    e = CompanyEnrichment(**defaults)
    e.compute_age()
    e.compute_status()
    return e


class TestCompanyRiskAnalyzer:
    """Test the 10 fraud detection rules."""

    def setup_method(self):
        self.analyzer = CompanyRiskAnalyzer()

    # Rule 1: Inactive company
    def test_inactive_company(self):
        e = make_enrichment(situacao_cadastral="INAPTA")
        result = self.analyzer.analyze(e)
        assert result.risk_score >= 40
        assert any(f["code"] == "COMPANY_NOT_ACTIVE" for f in result.flags)

    # Rule 2: Closed company (baixada)
    def test_closed_company(self):
        e = make_enrichment(situacao_cadastral="BAIXADA")
        result = self.analyzer.analyze(e)
        assert result.risk_score >= 60
        assert any(f["code"] == "COMPANY_CLOSED" for f in result.flags)

    # Rule 3: Very new company (<30 days)
    def test_new_company(self):
        e = make_enrichment(
            data_abertura=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        )
        e.compute_age()
        result = self.analyzer.analyze(e)
        assert result.risk_score >= 35
        assert any(f["code"] == "NEW_COMPANY" for f in result.flags)

    # Rule 4: Recent company (<90 days)
    def test_recent_company(self):
        e = make_enrichment(
            data_abertura=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
        )
        e.compute_age()
        result = self.analyzer.analyze(e)
        assert any(f["code"] == "RECENT_COMPANY" for f in result.flags)

    # Rule 5: Low capital + high amount
    def test_low_capital_high_transaction(self):
        e = make_enrichment(capital_social=1000.0)
        doc = {"amount": 150000.0}
        result = self.analyzer.analyze(e, doc)
        assert any(f["code"] == "LOW_CAPITAL_HIGH_TRANSACTION" for f in result.flags)

    # Rule 5 negative: high capital should NOT trigger flag
    def test_high_capital_no_flag(self):
        e = make_enrichment(capital_social=100000.0)
        doc = {"amount": 50000.0}
        result = self.analyzer.analyze(e, doc)
        assert not any(f["code"] == "LOW_CAPITAL_HIGH_TRANSACTION" for f in result.flags)

    # Rule 6: Company name mismatch
    def test_name_mismatch(self):
        e = make_enrichment(razao_social="Empresa Teste Ltda")
        doc = {"company_name": "Comércio de Alimentos S.A."}
        result = self.analyzer.analyze(e, doc)
        assert any(f["code"] == "COMPANY_NAME_MISMATCH" for f in result.flags)

    # Rule 6 negative: similar names should NOT trigger flag
    def test_name_match(self):
        e = make_enrichment(razao_social="Empresa Teste Ltda")
        doc = {"company_name": "Empresa Teste"}
        result = self.analyzer.analyze(e, doc)
        assert not any(f["code"] == "COMPANY_NAME_MISMATCH" for f in result.flags)

    # Rule 7: State mismatch
    def test_state_mismatch(self):
        e = make_enrichment(uf="SP")
        doc = {"uf": "RJ"}
        result = self.analyzer.analyze(e, doc)
        assert any(f["code"] == "STATE_MISMATCH" for f in result.flags)

    # Rule 7 negative: same state should NOT trigger
    def test_state_match(self):
        e = make_enrichment(uf="SP")
        doc = {"uf": "SP"}
        result = self.analyzer.analyze(e, doc)
        assert not any(f["code"] == "STATE_MISMATCH" for f in result.flags)

    # Rule 8: City mismatch
    def test_city_mismatch(self):
        e = make_enrichment(municipio="São Paulo")
        doc = {"municipio": "Rio de Janeiro"}
        result = self.analyzer.analyze(e, doc)
        assert any(f["code"] == "CITY_MISMATCH" for f in result.flags)

    # Rule 9: CNPJ not found
    def test_cnpj_not_found(self):
        e = CompanyEnrichment(cnpj="00000000000000")
        result = self.analyzer.analyze(e)
        assert any(f["code"] == "CNPJ_NOT_FOUND" for f in result.flags)

    # Rule 10: Combined risk pattern
    def test_combined_risk(self):
        e = make_enrichment(
            capital_social=5000.0,
            data_abertura=(datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
        )
        e.compute_age()
        doc = {"amount": 50000.0}
        result = self.analyzer.analyze(e, doc)
        assert any(f["code"] == "COMBINED_RISK_PATTERN" for f in result.flags)

    # Active company with no issues
    def test_clean_company(self):
        e = make_enrichment()
        result = self.analyzer.analyze(e)
        assert result.risk_score == 0
        assert result.risk_level == "LOW"
        assert result.flag_count == 0

    # Multiple flags accumulate score
    def test_multiple_flags_accumulate(self):
        e = make_enrichment(
            situacao_cadastral="INAPTA",
            capital_social=1000.0,
        )
        doc = {"amount": 200000.0, "company_name": "Empresa Diferente Ltda"}
        result = self.analyzer.analyze(e, doc)
        # Should have at least 3 flags
        assert result.flag_count >= 3
        assert result.risk_score > 40

    # Score caps at 100
    def test_score_capped(self):
        e = make_enrichment(
            situacao_cadastral="BAIXADA",
            capital_social=100.0,
            data_abertura=(datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        )
        e.compute_age()
        doc = {"amount": 500000.0, "company_name": "Outra Empresa S.A.", "uf": "RJ"}
        result = self.analyzer.analyze(e, doc)
        assert result.risk_score <= 100.0

    # Risk level classification
    def test_risk_levels(self):
        assert self.analyzer._classify(10) == "LOW"
        assert self.analyzer._classify(30) == "MEDIUM"
        assert self.analyzer._classify(60) == "HIGH"
        assert self.analyzer._classify(85) == "CRITICAL"


class TestCompanyEnrichment:
    """Test CompanyEnrichment model methods."""

    def test_compute_age(self):
        e = CompanyEnrichment(
            cnpj="123",
            data_abertura=(datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
        )
        e.compute_age()
        assert e.idade_empresa_dias == 365
        assert e.idade_empresa_anos == 1.0

    def test_compute_status_active(self):
        e = CompanyEnrichment(cnpj="123", situacao_cadastral="ATIVA")
        e.compute_status()
        assert e.empresa_ativa is True
        assert e.empresa_baixada is False

    def test_compute_status_closed(self):
        e = CompanyEnrichment(cnpj="123", situacao_cadastral="BAIXADA")
        e.compute_status()
        assert e.empresa_ativa is False
        assert e.empresa_baixada is True

    def test_is_valid(self):
        valid = CompanyEnrichment(cnpj="123", razao_social="Teste")
        invalid = CompanyEnrichment(cnpj="456")
        assert valid.is_valid is True
        assert invalid.is_valid is False

    def test_to_dict(self):
        e = CompanyEnrichment(cnpj="123", razao_social="Teste", uf="SP")
        d = e.to_dict()
        assert d["cnpj"] == "123"
        assert d["razao_social"] == "Teste"
        assert d["uf"] == "SP"
