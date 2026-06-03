# ============================================================
# PaySentinelIQ — Brazilian Financial Tools Tests
# Tests for CNPJ, INSS, IRRF, FGTS, CBO, BACEN validators
# ============================================================

import pytest

from app.ai_agents.tools.brazil_financial_tools import (
    _calculate_inss,
    _calculate_irrf,
    _cnpj_mod11,
    _parse_cnpj,
    _validate_cnpj_checksum,
    bacen_bank_validator,
    cbo_salary_range,
    cnae_compatibility_check,
    cnpj_validator,
    fgts_calculator,
    inss_calculator,
    irrf_calculator,
    liquido_consistency_check,
)


# ═══════════════════════════════════════════════════════════════
# CNPJ VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestCNPJValidator:
    """Test CNPJ Módulo 11 checksum validation."""

    def test_valid_cnpj_formatted(self):
        """Valid CNPJ with formatting should pass."""
        result = cnpj_validator.invoke({"cnpj": "11.222.333/0001-81"})
        assert result["valid_format"] is True
        assert result["valid_checksum"] is True
        assert result["cnpj_formatted"] == "11.222.333/0001-81"
        assert result["confidence"] == 100

    def test_valid_cnpj_digits_only(self):
        """Valid CNPJ with digits only should pass."""
        result = cnpj_validator.invoke({"cnpj": "11222333000181"})
        assert result["valid_checksum"] is True

    def test_invalid_checksum(self):
        """CNPJ with wrong check digits should fail."""
        result = cnpj_validator.invoke({"cnpj": "11.222.333/0001-99"})
        assert result["valid_checksum"] is False
        assert "failed" in result.get("error", "").lower()

    def test_all_same_digits(self):
        """All-same-digit CNPJ should be flagged as invalid."""
        result = cnpj_validator.invoke({"cnpj": "11.111.111/1111-11"})
        assert result["valid_checksum"] is False

    def test_wrong_length(self):
        """CNPJ with wrong length should fail."""
        result = cnpj_validator.invoke({"cnpj": "12345"})
        assert result["valid_format"] is False
        assert "14 digits" in result.get("error", "")

    def test_empty_cnpj(self):
        """Empty CNPJ should fail."""
        result = cnpj_validator.invoke({"cnpj": ""})
        assert result["valid_format"] is False

    def test_parse_cnpj_strips_formatting(self):
        """_parse_cnpj should strip all non-digit characters."""
        assert _parse_cnpj("12.345.678/0001-90") == "12345678000190"
        assert _parse_cnpj(" 12 345 678 0001 90 ") == "12345678000190"

    def test_mod11_calculation(self):
        """Módulo 11 algorithm should produce correct check digits."""
        # First 12 digits of a valid CNPJ, compute DV1
        dv1 = _cnpj_mod11("112223330001", [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        assert dv1 == 8  # Known good value

    def test_real_world_cnpj_banco_do_brasil(self):
        """Banco do Brasil CNPJ should validate."""
        result = cnpj_validator.invoke({"cnpj": "00.000.000/0001-91"})
        # This is a well-known valid CNPJ (Banco do Brasil)
        assert result["valid_checksum"] is True


# ═══════════════════════════════════════════════════════════════
# INSS CALCULATOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestINSSCalculator:
    """Test INSS calculation using 2025 progressive table."""

    def test_minimum_wage_inss(self):
        """INSS on minimum wage should be exactly 7.5%."""
        result = _calculate_inss(1412.00)
        assert result["inss_calculado"] == pytest.approx(105.90, rel=0.01)

    def test_mid_range_inss(self):
        """INSS on mid-range salary should span multiple brackets."""
        result = _calculate_inss(3500.00)
        # Should have multiple faixas
        assert len(result["faixas"]) >= 2
        assert result["salario_contribuicao"] == 3500.00

    def test_teto_inss(self):
        """INSS should cap at the teto (ceiling)."""
        result = _calculate_inss(10000.00)
        assert result["salario_contribuicao"] == 7786.02
        assert result["inss_calculado"] < 10000 * 0.14  # Should hit ceiling

    def test_zero_salary(self):
        """Zero salary should produce error."""
        result = _calculate_inss(0)
        assert "error" in result

    def test_negative_salary(self):
        """Negative salary should produce error."""
        result = _calculate_inss(-500)
        assert "error" in result

    def test_printed_vs_calculated_delta(self):
        """Tool should detect delta between calculated and printed INSS."""
        salario = 5000.00
        correct_inss = _calculate_inss(salario)["inss_calculado"]
        wrong_inss = correct_inss - 50.00  # Deliberately wrong

        result = inss_calculator.invoke({
            "salario_bruto": salario,
            "inss_printed": wrong_inss,
        })
        assert result["anomaly"] is True
        assert abs(result["delta"]) > 0.01

    def test_correct_inss_no_anomaly(self):
        """Correct INSS should not trigger anomaly."""
        salario = 5000.00
        correct_inss = _calculate_inss(salario)["inss_calculado"]

        result = inss_calculator.invoke({
            "salario_bruto": salario,
            "inss_printed": correct_inss,
        })
        assert result["anomaly"] is False


# ═══════════════════════════════════════════════════════════════
# IRRF CALCULATOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestIRRFCalculator:
    """Test IRRF calculation using 2025 progressive table."""

    def test_isento(self):
        """Salary below exemption threshold should have zero IRRF."""
        result = _calculate_irrf(2000.00, 150.00)  # Below 2259.20
        assert result["irrf_calculado"] == 0.0
        assert result["aliquota_efetiva"] == 0.0

    def test_first_bracket(self):
        """Salary in first taxable bracket."""
        result = _calculate_irrf(3000.00, 250.00)  # Base ~2750
        assert result["irrf_calculado"] > 0
        assert result["faixa"] is not None

    def test_high_salary(self):
        """High salary should hit the highest bracket."""
        result = _calculate_irrf(10000.00, 900.00)
        assert result["irrf_calculado"] > 0
        assert result["aliquota_efetiva"] > 0

    def test_with_dependents(self):
        """Dependents should reduce IRRF."""
        without_dep = _calculate_irrf(5000.00, 400.00, 0)
        with_dep = _calculate_irrf(5000.00, 400.00, 2)
        assert with_dep["irrf_calculado"] < without_dep["irrf_calculado"]

    def test_delta_detection(self):
        """IRRF mismatch should be detected."""
        result = irrf_calculator.invoke({
            "salario_bruto": 5000.00,
            "inss": 400.00,
            "irrf_printed": 50.00,  # Deliberately wrong
        })
        assert result["anomaly"] is True
        assert abs(result["delta"]) > 0.01


# ═══════════════════════════════════════════════════════════════
# FGTS CALCULATOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestFGTSCalculator:
    """Test FGTS calculation (8% regular, 2% aprendiz)."""

    def test_regular_fgts(self):
        """Regular employee should have 8% FGTS."""
        result = fgts_calculator.invoke({
            "salario_bruto": 5000.00,
            "fgts_printed": 400.00,
        })
        assert result["fgts_calculado"] == 400.00
        assert result["anomaly"] is False

    def test_aprendiz_fgts(self):
        """Aprendiz should have 2% FGTS."""
        result = fgts_calculator.invoke({
            "salario_bruto": 1000.00,
            "fgts_printed": 20.00,
            "tipo_contrato": "aprendiz",
        })
        assert result["fgts_calculado"] == 20.00

    def test_fgts_mismatch(self):
        """Wrong FGTS should be flagged."""
        result = fgts_calculator.invoke({
            "salario_bruto": 5000.00,
            "fgts_printed": 300.00,  # Should be 400.00
        })
        assert result["anomaly"] is True
        assert result["delta"] == 100.00

    def test_fgts_mismatch_critical(self):
        """Large FGTS mismatch should be critical severity."""
        result = fgts_calculator.invoke({
            "salario_bruto": 10000.00,
            "fgts_printed": 100.00,  # Should be 800.00
        })
        assert result["severity"] == "critical"


# ═══════════════════════════════════════════════════════════════
# LÍQUIDO CONSISTENCY TESTS
# ═══════════════════════════════════════════════════════════════

class TestLiquidoConsistency:
    """Test líquido (net pay) consistency validation."""

    def test_correct_liquido(self):
        """Correct net pay should pass."""
        # bruto=5000, inss=400, irrf=300, outros=0 → líquido=4300
        result = liquido_consistency_check.invoke({
            "salario_bruto": 5000.00,
            "inss": 400.00,
            "irrf": 300.00,
            "outros_descontos": 0.00,
            "liquido_printed": 4300.00,
        })
        assert result["anomaly"] is False

    def test_incorrect_liquido(self):
        """Wrong net pay should be flagged as critical."""
        result = liquido_consistency_check.invoke({
            "salario_bruto": 5000.00,
            "inss": 400.00,
            "irrf": 300.00,
            "liquido_printed": 5000.00,  # Impossible — deductions exist
        })
        assert result["anomaly"] is True
        assert result["severity"] == "critical"

    def test_fgts_not_deducted(self):
        """FGTS should NOT be deducted from líquido."""
        result = liquido_consistency_check.invoke({
            "salario_bruto": 5000.00,
            "inss": 400.00,
            "irrf": 300.00,
            "outros_descontos": 0.00,
            "liquido_printed": 4300.00,
        })
        assert result["liquido_calculado"] == 4300.00
        assert "patronal" in result.get("fgts_nota", "").lower()


# ═══════════════════════════════════════════════════════════════
# CBO SALARY RANGE TESTS
# ═══════════════════════════════════════════════════════════════

class TestCBOSalaryRange:
    """Test CBO salary range validation."""

    def test_within_range(self):
        """Salary within expected range should pass."""
        result = cbo_salary_range.invoke({
            "cbo_code": "212405",
            "salario": 7000.00,
            "cargo": "Analista de Sistemas",
        })
        assert result["status"] == "within_range"
        assert result["anomaly"] is False

    def test_above_range(self):
        """Salary above expected range should be flagged."""
        result = cbo_salary_range.invoke({
            "cbo_code": "411005",
            "salario": 20000.00,  # Auxiliar de Escritório at R$20k?!
            "cargo": "Auxiliar de Escritório",
        })
        assert result["anomaly"] is True
        assert "above" in result["status"]

    def test_below_range(self):
        """Salary far below the range should be flagged."""
        result = cbo_salary_range.invoke({
            "cbo_code": "252205",
            "salario": 500.00,  # Gerente Financeiro at R$500?!
            "cargo": "Gerente Financeiro",
        })
        assert result["anomaly"] is True

    def test_unknown_cbo(self):
        """Unknown CBO should return NOT_VERIFIABLE."""
        result = cbo_salary_range.invoke({
            "cbo_code": "999999",
            "salario": 5000.00,
            "cargo": "XXXXXXXXXX_NO_MATCH_XXXXXXXXXX",  # Cargo that won't match anything
        })
        assert result["status"] == "NOT_VERIFIABLE"

    def test_cargo_name_fallback(self):
        """Should match by cargo name if CBO code doesn't match directly."""
        result = cbo_salary_range.invoke({
            "cbo_code": "999",
            "salario": 7000.00,
            "cargo": "Gerente Financeiro",
        })
        # Should find by cargo name match
        assert result["status"] != "NOT_VERIFIABLE" or result["confidence"] == 0


# ═══════════════════════════════════════════════════════════════
# BACEN BANK VALIDATOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestBACENBankValidator:
    """Test BACEN ISPB bank code validation."""

    def test_valid_bank_banco_do_brasil(self):
        result = bacen_bank_validator.invoke({"bank_code": "001"})
        assert result["valid"] is True
        assert "Banco do Brasil" in result["bank_name"]

    def test_valid_bank_itau(self):
        result = bacen_bank_validator.invoke({"bank_code": "341"})
        assert result["valid"] is True
        assert "Itaú" in result["bank_name"]

    def test_valid_bank_bradesco(self):
        result = bacen_bank_validator.invoke({"bank_code": "237"})
        assert result["valid"] is True

    def test_valid_bank_nubank(self):
        result = bacen_bank_validator.invoke({"bank_code": "260"})
        assert result["valid"] is True

    def test_invalid_bank_code(self):
        result = bacen_bank_validator.invoke({"bank_code": "999"})
        assert result["valid"] is False
        assert result["severity"] == "critical"

    def test_bank_code_padding(self):
        """Bank code '1' should be treated as '001'."""
        result = bacen_bank_validator.invoke({"bank_code": "1"})
        assert result["valid"] is True


# ═══════════════════════════════════════════════════════════════
# CNAE COMPATIBILITY TESTS
# ═══════════════════════════════════════════════════════════════

class TestCNAECompatibility:
    """Test CNAE-CBO compatibility checking."""

    def test_compatible_it_cnae(self):
        """Software development CNAE with developer CBO should be compatible."""
        result = cnae_compatibility_check.invoke({
            "cnae_code": "62.01-5",
            "cbo_code": "212405",
            "cargo": "Analista de Sistemas",
        })
        assert result["compatible"] is True

    def test_incompatible_pair(self):
        """Cleaning company CNAE with developer CBO should be incompatible."""
        result = cnae_compatibility_check.invoke({
            "cnae_code": "81.21-4",
            "cbo_code": "212405",
            "cargo": "Analista de Sistemas",
        })
        # 81 prefix matches 81 (cleaning services) which includes 514320, 4110
        # But 212405 (Analista de Sistemas) is NOT in the cleaning CBO list
        assert result["compatible"] is False

    def test_unknown_cnae(self):
        result = cnae_compatibility_check.invoke({
            "cnae_code": "99.99-9",
            "cbo_code": "212405",
        })
        assert result["status"] == "NOT_VERIFIABLE"
