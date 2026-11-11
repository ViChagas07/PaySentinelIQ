from datetime import date, timedelta

from app.core.contracts.pipeline_context import PipelineContext
from app.services.ai.risk_analyzer import RiskAnalyzer
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.pipeline.stages.validate_stage import ValidateStage


def _aware(value: date) -> str:
    return f"{value.isoformat()}T00:00:00+00:00"


def _severities(context: PipelineContext) -> dict[str, str]:
    return {
        evidence.code: evidence.severity.value
        for evidence in context.evidences
    }


def test_overdue_and_round_amount_severities_are_policy_levels():
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={
            "valor_nominal": 1000.0,
            "data_vencimento": (date.today() - timedelta(days=800)).isoformat(),
        },
        extracted_text="Documento sintetico com vencimento antigo " * 3,
    )

    ValidateStage().execute(context)

    severities = _severities(context)
    assert severities["BOLETO_SEVERELY_OVERDUE"] == "low"
    assert severities["ROUND_AMOUNT_SUSPICIOUS"] == "low"


def test_overdue_between_30_and_365_days_is_info():
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={
            "valor_nominal": 1234.56,
            "data_vencimento": (date.today() - timedelta(days=60)).isoformat(),
        },
        extracted_text="Documento sintetico " * 4,
    )

    ValidateStage().execute(context)

    assert _severities(context)["BOLETO_OVERDUE"] == "info"


def test_payslip_never_emits_boleto_due_evidence():
    context = PipelineContext(
        document_type="contracheque",
        extracted_fields={
            "cpf": "123.456.789-09",
            "cnpj": "12.345.678/0001-95",
            "data_admissao": "24/08/2020",
        },
        extracted_text=(
            "Empregador\nCNPJ do Empregador: 12.345.678/0001-95\n"
            "Data de Admissao\n24/08/2020\n" * 3
        ),
    )

    ValidateStage().execute(context)
    RiskStage().execute(context)

    codes = set(_severities(context))
    assert not any(code.startswith("BOLETO_") for code in codes)
    assert "DOCUMENT_EXPIRED" not in codes


def test_extracted_due_date_wins_over_text_scan():
    future_due = date.today() + timedelta(days=45)
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={
            "valor_nominal": 1234.56,
            "data_vencimento": future_due.strftime("%d/%m/%Y"),
        },
        extracted_text=(
            "Boleto sintetico com data antiga 01/01/2020 no corpo. " * 3
        ),
    )

    ValidateStage().execute(context)

    codes = set(_severities(context))
    assert "BOLETO_OVERDUE" not in codes
    assert "BOLETO_SEVERELY_OVERDUE" not in codes
    assert "BOLETO_VENCIDO" not in codes


def test_text_scan_is_kept_without_extracted_due_date():
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={"valor_nominal": 1234.56},
        extracted_text="Boleto sintetico vencido em 01/01/2020. " * 3,
    )

    ValidateStage().execute(context)

    severities = _severities(context)
    assert "BOLETO_SEVERELY_OVERDUE" in severities
    assert severities["BOLETO_SEVERELY_OVERDUE"] == "low"
    assert severities.get("BOLETO_VENCIDO") == "info"


def test_risk_analyzer_uses_new_policy_severities():
    assessment = RiskAnalyzer().analyze(
        {
            "document_type": "boleto",
            "valor_nominal": 1000.0,
            "due_date": _aware(date.today() - timedelta(days=800)),
        }
    )
    severities = {flag.code: flag.severity for flag in assessment.flags}

    assert severities["DOCUMENT_EXPIRED"] == "info"
    assert severities["BOLETO_SEVERELY_OVERDUE"] == "low"
    assert severities["BOLETO_ROUND_AMOUNT"] == "low"


def test_risk_stage_preserves_flag_severity():
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={
            "valor_nominal": 1000.0,
            "data_vencimento": (date.today() - timedelta(days=800)).isoformat(),
            "due_date": _aware(date.today() - timedelta(days=800)),
        },
    )

    RiskStage().execute(context)

    severities = _severities(context)
    assert severities["DOCUMENT_EXPIRED"] == "info"
    assert severities["BOLETO_SEVERELY_OVERDUE"] == "low"
    assert severities["BOLETO_ROUND_AMOUNT"] == "low"
