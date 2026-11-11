from datetime import date
from decimal import Decimal

from app.services.extraction.boleto_extractor import extract_boleto_fields

LINHA = "00190.00009 01234.567008 12345.678901 2 34560000123456"
LINHA_DIGITS = "00190000090123456700812345678901234560000123456"
BARCODE = "12345678901234567890123456789012345678901234"

BOLETO_PT = f"""
BANCO DO BRASIL
Beneficiário: ACME SERVIÇOS LTDA
CNPJ: 12.345.678/0001-90
Pagador: JOÃO DA SILVA
Data de Vencimento: 20/01/2026
Valor do Documento: R$ 1.234,56
Valor Cobrado: 1.234,56
Nosso Número: 12345678901
Nº do Documento: 98765
Data do Documento: 15/01/2026
Local de Pagamento: PAGÁVEL EM QUALQUER BANCO
Carteira: 17
Agência/Código do Beneficiário: 1234/123456-7
Multa: 2,00%
Juros: 1,00% ao mês
Linha Digitável: {LINHA}
Código de Barras: {BARCODE}
"""

BOLETO_ES = f"""
Beneficiario: SERVICIOS ANDINOS S.A.
CNPJ: 12.345.678/0001-90
Pagador: JUAN PEREZ
Fecha de vencimiento: 20/01/2026
Valor del documento: R$ 1.234,56
Valor cobrado: 1.234,56
Nuestro número: 12345678901
Número del documento: 98765
Fecha del documento: 15/01/2026
Lugar de pago: PAGADERO EN CUALQUIER BANCO
Cartera: 17
Agencia/Código del beneficiario: 1234/123456-7
Multa: 2,00%
Intereses de mora: 1,00% mensual
Línea digitable: {LINHA}
"""

BOLETO_EN = f"""
Beneficiary: ANDEAN SERVICES INC.
CNPJ: 12.345.678/0001-90
Payer: JOHN DOE
Due Date: 20/01/2026
Document Amount: 1,234.56
Amount Charged: 1,234.56
Our Number: 12345678901
Document Number: 98765
Document Date: 15/01/2026
Place of Payment: PAYABLE AT ANY BANK
Wallet: 17
Agency/Beneficiary Code: 1234/123456-7
Fine: 2.00%
Late Interest: 1.00% per month
Digitable Line: {LINHA}
"""

BOLETO_NOISE = """
Beneficiario: ACME SERVICOS LTDA
CNPJ: 12.345.678/0001-9O
Pagador: JOAO DA SILVA
Data de Vencimento
2O/01/2026
Valor do Documento: R$ 1.234,5O
Nosso Numero: 1O23456789O
Numero do Documento: 98765
Data do Documento: 15/01/2026
Local de Pagamento: PAGAVEL EM QUALQUER BANCO
Carteira: 17
Agencia/Codigo do Beneficiario: 1234/123456-7
Multa: 2,00%
Juros: 1,00% ao mes
"""


def test_extract_boleto_pt():
    fields = extract_boleto_fields(BOLETO_PT)

    assert fields.language.lang == "pt"
    assert fields.beneficiario is not None
    assert fields.beneficiario.value == "ACME SERVIÇOS LTDA"
    assert fields.pagador is not None
    assert fields.pagador.value == "JOÃO DA SILVA"
    assert fields.data_vencimento is not None
    assert fields.data_vencimento.value == date(2026, 1, 20)
    assert fields.data_documento is not None
    assert fields.data_documento.value == date(2026, 1, 15)
    assert fields.valor_nominal is not None
    assert fields.valor_nominal.value == Decimal("1234.56")
    assert fields.valor_cobrado is not None
    assert fields.valor_cobrado.value == Decimal("1234.56")
    assert fields.nosso_numero is not None
    assert fields.nosso_numero.value == "12345678901"
    assert fields.numero_documento is not None
    assert fields.numero_documento.value == "98765"
    assert fields.local_pagamento is not None
    assert fields.local_pagamento.value == "PAGÁVEL EM QUALQUER BANCO"
    assert fields.carteira is not None
    assert fields.carteira.value == "17"
    assert fields.agencia_codigo_beneficiario is not None
    assert fields.multa is not None
    assert fields.multa.value == "2,00%"
    assert fields.juros is not None
    assert fields.juros.value == "1,00% ao mês"
    assert fields.cnpj is not None
    assert fields.cnpj.value == "12.345.678/0001-90"
    assert fields.linha_digitavel is not None
    assert fields.linha_digitavel.value == LINHA_DIGITS
    assert fields.codigo_barras is not None
    assert fields.codigo_barras.value == BARCODE
    assert fields.codigo_banco is not None
    assert fields.codigo_banco.value == "001"
    assert fields.warnings == []


def test_extract_boleto_es():
    fields = extract_boleto_fields(BOLETO_ES)

    assert fields.language.lang == "es"
    assert fields.beneficiario is not None
    assert fields.beneficiario.value == "SERVICIOS ANDINOS S.A."
    assert fields.data_vencimento is not None
    assert fields.data_vencimento.value == date(2026, 1, 20)
    assert fields.valor_nominal is not None
    assert fields.valor_nominal.value == Decimal("1234.56")
    assert fields.juros is not None
    assert fields.juros.value == "1,00% mensual"
    assert fields.linha_digitavel is not None
    assert fields.linha_digitavel.value == LINHA_DIGITS


def test_extract_boleto_en_uses_us_amount_and_labels():
    fields = extract_boleto_fields(BOLETO_EN)

    assert fields.language.lang == "en"
    assert fields.beneficiario is not None
    assert fields.beneficiario.value == "ANDEAN SERVICES INC."
    assert fields.pagador is not None
    assert fields.pagador.value == "JOHN DOE"
    assert fields.valor_nominal is not None
    assert fields.valor_nominal.value == Decimal("1234.56")
    assert fields.valor_cobrado is not None
    assert fields.valor_cobrado.value == Decimal("1234.56")
    assert fields.multa is not None
    assert fields.multa.value == "2.00%"
    assert fields.juros is not None
    assert fields.juros.value == "1.00% per month"


def test_extract_boleto_noise_and_next_line_value():
    fields = extract_boleto_fields(BOLETO_NOISE)

    assert fields.language.lang == "pt"
    assert fields.cnpj is not None
    assert fields.cnpj.value == "12.345.678/0001-90"
    assert fields.valor_nominal is not None
    assert fields.valor_nominal.value == Decimal("1234.50")
    assert fields.nosso_numero is not None
    assert fields.nosso_numero.value == "10234567890"
    assert fields.data_vencimento is not None
    assert fields.data_vencimento.value == date(2026, 1, 20)
    assert fields.data_vencimento.method == "label_next_line"
    assert fields.corrections


def test_ambiguous_amount_produces_warning():
    fields = extract_boleto_fields(
        "Beneficiário: ACME\nValor do Documento: 1.234\n"
    )

    assert fields.valor_nominal is not None
    assert fields.valor_nominal.value == Decimal("1234")
    assert fields.warnings


def test_missing_fields_remain_none():
    fields = extract_boleto_fields("Beneficiário: ACME")

    assert fields.beneficiario is not None
    assert fields.pagador is None
    assert fields.valor_nominal is None
    assert fields.data_vencimento is None
    assert fields.linha_digitavel is None
