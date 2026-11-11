from app.services.extraction.labels import normalize_label
from app.services.extraction.language import detect_language
from app.services.extraction.text_utils import (
    fix_digit_confusions,
    fold,
    normalize_text,
)


def test_normalize_text_preserves_line_breaks_and_collapses_spaces():
    text = "  Valor   do\r\nDocumento\t  R$   1.234,56  "

    assert normalize_text(text) == "Valor do\nDocumento R$ 1.234,56"


def test_fold_removes_accents_and_case():
    assert fold("Salário Líquido") == "salario liquido"
    assert normalize_label("Salário Líquido") == normalize_label("SALARIO LIQUIDO")


def test_fix_digit_confusions_only_numeric_sequences():
    fixed, corrections = fix_digit_confusions("1O0,5O")
    assert fixed == "100,50"
    assert corrections

    word, word_corrections = fix_digit_confusions("BOLETO")
    assert word == "BOLETO"
    assert word_corrections == []


def test_detect_language_pt_es_en():
    pt = detect_language(
        "Beneficiário Pagador Vencimento Valor do Documento "
        "Competência Proventos Descontos Líquido"
    )
    es = detect_language(
        "Beneficiario Pagador Vencimiento Importe del documento "
        "Período Haberes Descuentos Neto a pagar Dependientes"
    )
    en = detect_language(
        "Beneficiary Payer Due Date Document Amount "
        "Pay Period Earnings Deductions Net Pay Dependents"
    )

    assert pt.lang == "pt"
    assert es.lang == "es"
    assert en.lang == "en"
    assert pt.confidence > 0
    assert es.confidence > 0
    assert en.confidence > 0


def test_detect_language_without_signal_defaults_to_pt():
    guess = detect_language("123456 789")

    assert guess.lang == "pt"
    assert guess.confidence == 0.0
