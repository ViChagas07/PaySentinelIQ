from datetime import date
from decimal import Decimal

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.canonical_pipeline import CanonicalPipeline
from app.services.pipeline.stages.deterministic_rules_stage import (
    DeterministicRulesStage,
)
from app.services.validation.febraban import decode_linha_digitavel
from app.shared.settings import Settings
from tests.unit._validation_helpers import build_linha_digitavel


def _boleto_fields():
    line = build_linha_digitavel(factor=9999, value_cents=123456)
    decoded = decode_linha_digitavel(line, today=date(2025, 2, 22))
    return {
        "linha_digitavel": line,
        "valor_nominal": Decimal("1234.56"),
        "data_vencimento": date(2025, 2, 21),
        "codigo_barras": decoded["codigo_barras"],
        "codigo_banco": "001",
    }


def _payslip_fields():
    return {
        "salario_bruto": Decimal("5000.00"),
        "total_descontos": Decimal("501.51"),
        "salario_liquido": Decimal("4498.49"),
        "inss": Decimal("501.51"),
        "irrf": Decimal("0.00"),
        "fgts": Decimal("400.00"),
        "base_inss": Decimal("5000.00"),
        "base_fgts": Decimal("5000.00"),
        "dependentes": "0",
        "cargo": "Analista",
        "periodo": "01/2026",
        "data_admissao": "15/03/2020",
        "cpf": "123.456.789-09",
        "cnpj": "12.345.678/0001-95",
    }


def _context(document_type: str, fields: dict) -> PipelineContext:
    return PipelineContext(
        document_type=document_type,
        extracted_fields=fields,
        extracted_text="Banco: 001",
    )


def test_stage_order_includes_deterministic_rules():
    names = [stage.name for stage in CanonicalPipeline()._stages]

    assert names.index("DeterministicRulesStage") == names.index(
        "ValidateStage"
    ) + 1
    assert names.index("DeterministicRulesStage") < names.index("RiskStage")


def test_consistent_boleto_has_no_evidence():
    context = _context("boleto", _boleto_fields())

    DeterministicRulesStage().execute(context)

    assert context.evidences == []
    assert context.metadata["validation"]["boleto_decoded"]["status"] == "ok"
    assert context.metadata["validation"]["skipped_rules"] == []


def test_adulterated_boleto_adds_critical_evidence():
    fields = _boleto_fields()
    fields["valor_nominal"] = Decimal("1300.00")
    context = _context("boleto", fields)

    DeterministicRulesStage().execute(context)

    codes = {evidence.code for evidence in context.evidences}
    assert "BOLETO_AMOUNT_MISMATCH" in codes
    assert context.metadata["validation"]["findings"][
        "BOLETO_AMOUNT_MISMATCH"
    ]


def test_consistent_payslip_has_no_evidence():
    context = _context("contracheque", _payslip_fields())

    DeterministicRulesStage().execute(context)

    assert context.evidences == []
    assert context.metadata["validation"]["payslip_expected"][
        "inss_expected"
    ] == "501.51"


def test_inferred_document_type_is_used():
    context = _context("unknown", _boleto_fields())
    context.metadata["extraction"] = {
        "document_type_inferred": "boleto",
    }

    DeterministicRulesStage().execute(context)

    assert context.metadata["validation"]["document_type"] == "boleto"
    assert context.evidences == []


def test_rule_exception_is_captured(monkeypatch):
    context = _context("boleto", _boleto_fields())

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.services.validation.febraban.validate_boleto",
        fail,
    )

    DeterministicRulesStage().execute(context)

    assert any("Deterministic rules failed" in w for w in context.warnings)


def test_disabled_flag_skips_stage(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: Settings(
            _env_file=None,
            ENABLE_DETERMINISTIC_RULES=False,
        ),
    )
    context = _context("boleto", _boleto_fields())

    DeterministicRulesStage().execute(context)

    assert "validation" not in context.metadata
