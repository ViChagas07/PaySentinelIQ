from datetime import date
from decimal import Decimal

from app.core.contracts.pipeline_context import PipelineContext
from app.services.extraction.adapter import to_pipeline_fields
from app.services.extraction.boleto_extractor import extract_boleto_fields
from app.services.extraction.dates import parse_date
from app.services.extraction.payslip_extractor import extract_payslip_fields
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.validation.payslip_rules import validate_payslip
from app.synthetic.payslip_calc import irrf
from app.synthetic.records import build_document


def test_english_month_name_due_date_is_parsed_after_label():
    fields = extract_boleto_fields(
        "Due Date: December 04, 2026\n"
        "Document Amount: 1,425.91\n"
        "Digitable Line: 26098014243924799235518666694072216450000142591\n"
    )
    output = to_pipeline_fields(fields, "boleto")

    assert output["data_vencimento"] == "04/12/2026"
    assert output["valor_nominal"] == 1425.91


def test_layout_d_aliases_map_due_issue_and_amount():
    fields = extract_boleto_fields(
        "Credor do Título: Duna Inventada Facilities Ltda\n"
        "Data Limite de Pagamento: 17/08/2026\n"
        "Montante do Título: 6.000,00\n"
        "Data de Emissão: 10/08/2026\n"
        "Representação Numérica: "
        "23791758920921284341227320022141215410000600000\n"
    )
    output = to_pipeline_fields(fields, "boleto")

    assert output["data_vencimento"] == "17/08/2026"
    assert output["data_documento"] == "10/08/2026"
    assert output["valor_nominal"] == 6000.0


def test_set2_payslip_aliases_allow_irrf_validation():
    text = (
        "Empregador\nCriativa Fictícia Software Ltda\n"
        "CNPJ do Empregador: 70.707.632/0001-75\n"
        "Colaborador: Rafael Inventado Costa\n"
        "CPF: 110.605.297-85\n"
        "Mês de Referência: 08/2026\n"
        "Data de Contratação: 14/10/2023\n"
        "Remuneração Base: 6.433,37\n"
        "Previdência: 759,10\n"
        "Imposto de Renda: 643,40\n"
        "Fundo de Garantia: 547,18\n"
        "Total de Vencimentos: 6.839,81\n"
        "Abatimentos: 1.402,50\n"
        "Valor Líquido: 5.437,31\n"
        "Base Previdenciária: 6.839,81\n"
        "Base Fiscal: 6.839,81\n"
        "Base do Fundo: 6.839,81\n"
        "Número de Dependentes: 1\n"
    )
    fields = extract_payslip_fields(text)
    output = to_pipeline_fields(fields, "contracheque")

    assert output["inss"] == 759.10
    assert output["base_irrf"] == 6839.81
    assert output["dependentes"] == 1
    assert output["total_descontos"] == 1402.50
    assert output["fgts"] == 547.18

    evidences, _expected, skipped = validate_payslip(output)
    codes = {evidence.code for evidence in evidences}
    assert "PAYSLIP_IRRF_MISMATCH" not in codes
    assert "inss:missing_inss" not in skipped


def test_ambiguous_english_date_is_not_used_by_deterministic_rules():
    fields = extract_boleto_fields(
        "Due Date: 01/02/2026\n"
        "Document Amount: 1,234.56\n"
        "Digitable Line: 00191234567890123456789012345678901234567890\n"
    )
    output = to_pipeline_fields(fields, "boleto")

    assert output["data_vencimento"] is None
    assert output["due_date"] is None
    assert output["data_vencimento_ambiguous"] is True

    context = PipelineContext(
        document_type="boleto",
        extracted_fields=output,
        extracted_text="Boleto sintetico vencido em 01/02/2020. " * 3,
    )
    ValidateStage().execute(context)

    codes = {evidence.code for evidence in context.evidences}
    assert "BOLETO_OVERDUE" not in codes
    assert "BOLETO_SEVERELY_OVERDUE" not in codes
    assert "BOLETO_VENCIDO" not in codes
    assert "DOCUMENT_EXPIRED" not in codes


def test_english_ambiguous_date_keeps_month_first_display_value():
    parsed = parse_date("01/02/2026", "en")

    assert parsed.value == date(2026, 1, 2)
    assert parsed.ambiguous is True


def test_ambiguous_english_date_is_not_resurrected_by_legacy_fields():
    fields = extract_boleto_fields(
        "Due Date: 01/02/2026\n"
        "Document Amount: 1,234.56\n"
        "Digitable Line: 00191234567890123456789012345678901234567890\n"
    )
    adapted = to_pipeline_fields(fields, "boleto")
    context = PipelineContext(
        document_type="boleto",
        extracted_fields={
            "data_vencimento": "01/02/2026",
            "due_date": "2026-02-01T00:00:00+00:00",
        },
        extracted_text="Boleto vencido em 01/02/2020. " * 3,
    )
    context.extracted_fields.update(adapted)

    assert context.extracted_fields["data_vencimento"] is None
    assert context.extracted_fields["due_date"] is None
    assert context.extracted_fields["data_vencimento_ambiguous"] is True

    ValidateStage().execute(context)
    codes = {evidence.code for evidence in context.evidences}
    assert "BOLETO_OVERDUE" not in codes
    assert "BOLETO_SEVERELY_OVERDUE" not in codes
    assert "BOLETO_VENCIDO" not in codes


def test_locale_inconsistent_date_does_not_feed_due_rules():
    fields = extract_boleto_fields(
        "Beneficiário do Título: ACME Fictícia Ltda\n"
        "Data de Vencimento: 02/13/2026\n"
        "Valor Nominal: 1.234,56\n"
        "Linha Digitável: 00191234567890123456789012345678901234567890\n"
    )
    output = to_pipeline_fields(fields, "boleto")

    assert output["data_vencimento"] is None
    assert output["data_vencimento_locale_inconsistent"] is True

    context = PipelineContext(
        document_type="boleto",
        extracted_fields=output,
        extracted_text="Boleto vencido em 01/02/2020. " * 3,
    )
    ValidateStage().execute(context)

    codes = {evidence.code for evidence in context.evidences}
    assert "BOLETO_OVERDUE" not in codes
    assert "BOLETO_SEVERELY_OVERDUE" not in codes
    assert "BOLETO_VENCIDO" not in codes


def test_valid_native_due_date_still_feeds_rules():
    fields = extract_boleto_fields(
        "Beneficiário do Título: ACME Fictícia Ltda\n"
        "Data de Vencimento: 20/01/2027\n"
        "Valor Nominal: 1.234,56\n"
        "Linha Digitável: 00191234567890123456789012345678901234567890\n"
    )
    output = to_pipeline_fields(fields, "boleto")

    assert output["data_vencimento"] == "20/01/2027"
    assert output.get("data_vencimento_ambiguous") is None

    context = PipelineContext(
        document_type="boleto",
        extracted_fields=output,
        extracted_text="Boleto com vencimento futuro. " * 3,
    )
    ValidateStage().execute(context)

    codes = {evidence.code for evidence in context.evidences}
    assert "BOLETO_OVERDUE" not in codes
    assert "BOLETO_SEVERELY_OVERDUE" not in codes


def test_p3_tamper_never_uses_a_zero_irrf_base():
    for index in range(4):
        document = build_document(
            index=7000 + index,
            base_seed=42,
            doc_kind="contracheque",
            language="pt",
            layout="A",
            label_set="set1",
            split="train",
            tamper_types=["P3"],
            today=date(2026, 11, 11),
        )
        fields = document.fields
        original_irrf = irrf(
            Decimal(fields["salario_bruto"]),
            Decimal(fields["inss"]),
            int(fields["dependentes"]),
        )

        assert original_irrf > 0
        assert Decimal(fields["irrf"]) == Decimal("0.00")
