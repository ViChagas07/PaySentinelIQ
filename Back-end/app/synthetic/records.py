from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
import random
from typing import Any

from app.synthetic.febraban_builder import (
    build_linha_digitavel,
    factor_for_due_date,
)
from app.synthetic.payslip_calc import calculate_payslip
from app.synthetic.values import (
    BOLETO_BANKS,
    CITIES,
    COMPANIES,
    LABELS,
    PEOPLE,
    ROLES,
    SHIFT_BANKS,
    SHIFT_COMPANIES,
    format_amount,
    format_cnpj,
    format_cpf,
    format_date,
    generate_cnpj,
    generate_cpf,
)

TAMPER_CATALOG: dict[str, dict[str, Any]] = {
    "B1": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["BOLETO_AMOUNT_MISMATCH"],
        "intended_band": "HIGH",
    },
    "B2": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["BOLETO_DUE_DATE_MISMATCH"],
        "intended_band": "HIGH",
    },
    "B3": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": [
            "BOLETO_BANK_MISMATCH",
            "BANCO_INVALIDO",
        ],
        "intended_band": "HIGH",
    },
    "B4": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["BOLETO_GENERAL_DV_INVALID"],
        "intended_band": "HIGH",
    },
    "B5": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": [
            "BOLETO_AMOUNT_MISMATCH",
            "BOLETO_GENERAL_DV_INVALID",
        ],
        "intended_band": "HIGH",
    },
    "B6": {
        "sophistication": "expert",
        "detectable_by": "none",
        "expected_codes_any_of": [],
        "intended_band": "LOW",
    },
    "B7": {
        "sophistication": "expert",
        "detectable_by": "none",
        "expected_codes_any_of": [],
        "intended_band": "LOW",
    },
    "B8": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["BOLETO_AMOUNT_MISMATCH"],
        "intended_band": "HIGH",
    },
    "P1": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_NET_MISMATCH"],
        "intended_band": "HIGH",
    },
    "P2": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_INSS_MISMATCH"],
        "intended_band": "HIGH",
    },
    "P3": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_IRRF_MISMATCH"],
        "intended_band": "HIGH",
    },
    "P4": {
        "sophistication": "expert",
        "detectable_by": "none",
        "expected_codes_any_of": [],
        "intended_band": "LOW",
    },
    "P5": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_CPF_INVALID"],
        "intended_band": "HIGH",
    },
    "P6": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_PERIOD_FUTURE"],
        "intended_band": "HIGH",
    },
    "P7": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_FGTS_MISMATCH"],
        "intended_band": "MEDIUM",
    },
    "P8": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_DEDUCTIONS_INCONSISTENT"],
        "intended_band": "HIGH",
    },
    "P9": {
        "sophistication": "naive",
        "detectable_by": "arithmetic_rules",
        "expected_codes_any_of": ["PAYSLIP_NET_MISMATCH"],
        "intended_band": "HIGH",
    },
}


@dataclass
class SyntheticDocument:
    id: str
    seed: int
    doc_kind: str
    language: str
    layout: str
    label_set: str
    split: str
    is_fraud: bool
    tamper_types: list[str]
    sophistication: str
    detectable_by: str
    expected_codes_any_of: list[str]
    intended_band: str
    fields: dict[str, str]
    lines: list[str]
    original_lines: list[str] = field(default_factory=list)
    pdf_edit: dict[str, str] | None = None
    page_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "seed": self.seed,
            "doc_kind": self.doc_kind,
            "language": self.language,
            "layout": self.layout,
            "label_set": self.label_set,
            "split": self.split,
            "is_fraud": self.is_fraud,
            "tamper_types": self.tamper_types,
            "sophistication": self.sophistication,
            "detectable_by": self.detectable_by,
            "expected_codes_any_of": self.expected_codes_any_of,
            "intended_band": self.intended_band,
            "fields": self.fields,
            "page_text": self.page_text,
            "pdf_edit": self.pdf_edit,
        }


def _line(lines: list[str], label: str, value: str, layout: str) -> None:
    if layout == "A":
        lines.extend([label, value])
    else:
        lines.append(f"{label}: {value}")


def _value(fields: dict[str, str], key: str) -> str:
    return fields.get(key, "")


def _render_lines(
    document: SyntheticDocument,
) -> list[str]:
    fields = document.fields
    language = document.language
    layout = document.layout
    labels = LABELS[document.doc_kind][language][document.label_set]
    lines: list[str] = []

    if document.doc_kind == "boleto":
        _line(lines, labels["beneficiario"], fields["beneficiario"], layout)
        lines.append(f"CNPJ do BeneficiÃ¡rio: {format_cnpj(fields['beneficiario_cnpj'])}")
        _line(lines, labels["pagador"], fields["pagador"], layout)
        lines.append(f"CPF/CNPJ do Pagador: {fields['pagador_documento']}")
        _line(
            lines,
            labels["codigo_banco"],
            f"{fields['codigo_banco']}-1",
            layout,
        )
        _line(
            lines,
            labels["data_vencimento"],
            format_date(date.fromisoformat(fields["data_vencimento"]), language),
            layout,
        )
        _line(
            lines,
            labels["valor_nominal"],
            format_amount(
                Decimal(fields["valor_nominal"]),
                language,
                us_format=fields.get("number_style") == "us",
            ),
            layout,
        )
        _line(lines, labels["nosso_numero"], fields["nosso_numero"], layout)
        _line(
            lines,
            labels["numero_documento"],
            fields["numero_documento"],
            layout,
        )
        _line(
            lines,
            labels["data_documento"],
            format_date(date.fromisoformat(fields["data_documento"]), language),
            layout,
        )
        _line(lines, labels["local_pagamento"], fields["local_pagamento"], layout)
        _line(lines, labels["carteira"], fields["carteira"], layout)
        _line(
            lines,
            labels["agencia_codigo_beneficiario"],
            fields["agencia_codigo_beneficiario"],
            layout,
        )
        _line(lines, labels["multa"], fields["multa"], layout)
        _line(lines, labels["juros"], fields["juros"], layout)
        _line(
            lines,
            labels["linha_digitavel"],
            fields["linha_digitavel"],
            layout,
        )
        return lines

    _line(lines, labels["razao_social"], fields["razao_social"], layout)
    lines.append(f"CNPJ do Empregador: {format_cnpj(fields['cnpj_empregador'])}")
    _line(lines, labels["nome_funcionario"], fields["nome_funcionario"], layout)
    lines.append(f"CPF: {format_cpf(fields['cpf_funcionario'])}")
    _line(lines, labels["cargo"], fields["cargo"], layout)
    _line(lines, labels["cbo"], fields["cbo"], layout)
    _line(
        lines,
        labels["periodo"],
        fields["periodo"],
        layout,
    )
    _line(
        lines,
        labels["data_admissao"],
        format_date(date.fromisoformat(fields["data_admissao"]), language),
        layout,
    )
    _line(
        lines,
        labels["salario_base"],
        format_amount(
            Decimal(fields["salario_base"]),
            language,
            us_format=fields.get("number_style") == "us",
        ),
        layout,
    )
    if layout == "C":
        for code, key in (
            ("0010", "inss"),
            ("0020", "irrf"),
            ("0030", "fgts"),
        ):
            lines.append(
                f"{code} {labels[key]} 11,00 "
                f"{format_amount(Decimal(fields[key]), language, us_format=fields.get('number_style') == 'us')}"
            )
    else:
        for key in ("inss", "irrf", "fgts"):
            _line(
                lines,
                labels[key],
                format_amount(
                    Decimal(fields[key]),
                    language,
                    us_format=fields.get("number_style") == "us",
                ),
                layout,
            )
    for key in (
        "salario_bruto",
        "total_descontos",
        "salario_liquido",
        "base_inss",
        "base_irrf",
        "base_fgts",
    ):
        _line(
            lines,
            labels[key],
            format_amount(
                Decimal(fields[key]),
                language,
                us_format=fields.get("number_style") == "us",
            ),
            layout,
        )
    _line(lines, labels["dependentes"], fields["dependentes"], layout)
    return lines


def _tamper_meta(codes: list[str]) -> tuple[str, str, list[str], str]:
    if not codes:
        return "legitimate", "none", [], "LOW"
    if any(TAMPER_CATALOG[code]["sophistication"] == "expert" for code in codes):
        sophistication = "expert"
    elif len(codes) > 1:
        sophistication = "multi"
    else:
        sophistication = "naive"
    detectable = (
        "none"
        if all(TAMPER_CATALOG[code]["detectable_by"] == "none" for code in codes)
        else "arithmetic_rules"
    )
    expected = sorted(
        {
            code
            for item in codes
            for code in TAMPER_CATALOG[item]["expected_codes_any_of"]
        }
    )
    band = TAMPER_CATALOG[codes[0]]["intended_band"]
    return sophistication, detectable, expected, band


def _make_boleto(
    rng: random.Random,
    document: SyntheticDocument,
    today: date,
    bank_pool: tuple[str, ...],
    company_pool: tuple[str, ...],
    person_pool: tuple[str, ...],
) -> None:
    language = document.language
    bank = rng.choice(bank_pool)
    currency = "9"
    carteira = rng.choice(("17", "109", "SR"))
    free_field = "".join(str(rng.randrange(10)) for _ in range(25))
    nosso_numero = "".join(str(rng.randrange(10)) for _ in range(11))
    document_number = "".join(str(rng.randrange(10)) for _ in range(8))
    amount = Decimal(rng.randrange(5000, 900000)) / Decimal("100")
    if document.split == "golden":
        amount = Decimal(rng.randrange(6000, 450000)) / Decimal("100")
        if amount % Decimal("100") == 0:
            amount += Decimal("0.37")
    elif rng.random() < 0.10:
        amount = (amount / Decimal("100")).quantize(Decimal("1")) * Decimal("100")
    due_offset = rng.randint(-200, 120)
    if document.split == "golden":
        due_offset = rng.randint(30, 120)
    due_date = today + timedelta(days=due_offset)
    document_date = due_date - timedelta(days=rng.randint(1, 30))
    beneficiary = rng.choice(company_pool)
    beneficiary_cnpj = generate_cnpj(rng)
    payer = rng.choice(person_pool)
    payer_document = generate_cpf(rng)
    factor = factor_for_due_date(due_date)
    line, barcode = build_linha_digitavel(
        bank,
        currency,
        free_field,
        factor,
        int(amount * 100),
    )
    fields = {
        "codigo_banco": bank,
        "moeda": currency,
        "carteira": carteira,
        "campo_livre": free_field,
        "nosso_numero": nosso_numero,
        "numero_documento": document_number,
        "agencia_codigo_beneficiario": (
            f"{rng.randrange(1, 9999):04d}/"
            f"{rng.randrange(1, 999999):06d}-{rng.randrange(10)}"
        ),
        "valor_nominal": str(amount),
        "valor_codificado": str(amount),
        "data_vencimento": due_date.isoformat(),
        "data_documento": document_date.isoformat(),
        "beneficiario": beneficiary,
        "beneficiario_cnpj": beneficiary_cnpj,
        "pagador": payer,
        "pagador_documento": payer_document,
        "local_pagamento": CITIES[language],
        "multa": "2,00%",
        "juros": "1,00% ao mês",
        "linha_digitavel": line,
        "codigo_barras": barcode,
        "fator": str(factor),
        "number_style": (
            "us"
            if language == "en"
            and (document.split == "golden" or rng.random() < 0.30)
            else "br"
        ),
    }
    original_fields = dict(fields)
    original_lines = []

    if document.split == "golden":
        original_lines = _render_lines(
            SyntheticDocument(
                **{**document.__dict__, "fields": original_fields}
            )
        )

    for tamper in document.tamper_types:
        if tamper == "B1":
            fields["valor_nominal"] = str(
                Decimal(fields["valor_nominal"]) + Decimal("65.00")
            )
        elif tamper == "B2":
            fields["data_vencimento"] = (
                date.fromisoformat(fields["data_vencimento"])
                + timedelta(days=5)
            ).isoformat()
        elif tamper == "B3":
            fields["codigo_banco"] = "999"
        elif tamper == "B4":
            line = fields["linha_digitavel"]
            fields["linha_digitavel"] = (
                line[:32] + str((int(line[32]) + 1) % 10) + line[33:]
            )
        elif tamper == "B5":
            line = fields["linha_digitavel"]
            new_cents = int(fields["valor_codificado"].replace(".", ""))
            new_cents += 10000
            fields["linha_digitavel"] = (
                line[:37] + f"{new_cents:010d}"
            )
        elif tamper == "B6":
            new_amount = Decimal(fields["valor_nominal"]) + Decimal("250.00")
            new_line, new_barcode = build_linha_digitavel(
                fields["codigo_banco"],
                fields["moeda"],
                fields["campo_livre"],
                int(fields["fator"]),
                int(new_amount * 100),
            )
            fields["valor_nominal"] = str(new_amount)
            fields["valor_codificado"] = str(new_amount)
            fields["linha_digitavel"] = new_line
            fields["codigo_barras"] = new_barcode
        elif tamper == "B7":
            fields["beneficiario_cnpj"] = generate_cnpj(rng)
            fields["beneficiario"] = rng.choice(company_pool)
        elif tamper == "B8":
            fields["valor_nominal"] = str(
                Decimal(fields["valor_nominal"]) + Decimal("65.00")
            )
            document.pdf_edit = {
                "field": "valor_nominal",
                "before": original_fields["valor_nominal"],
                "after": fields["valor_nominal"],
                "before_text": format_amount(
                    Decimal(original_fields["valor_nominal"]),
                    language,
                    us_format=original_fields.get("number_style") == "us",
                ),
                "after_text": format_amount(
                    Decimal(fields["valor_nominal"]),
                    language,
                    us_format=fields.get("number_style") == "us",
                ),
            }

    document.fields = fields
    document.original_lines = original_lines
    document.lines = _render_lines(document)
    if "B3" in document.tamper_types and language != "pt":
        document.lines.append(
            f"Banco: {fields['codigo_banco']}-1"
        )
    document.page_text = "\n".join(document.lines)


def _make_payslip(
    rng: random.Random,
    document: SyntheticDocument,
    today: date,
    company_pool: tuple[str, ...],
    person_pool: tuple[str, ...],
) -> None:
    language = document.language
    if document.split == "golden":
        base_salary = Decimal(rng.randrange(600000, 800000)) / Decimal("100")
    else:
        base_salary = Decimal(rng.randrange(250000, 800000)) / Decimal("100")
    additional = Decimal(rng.randrange(0, 150000)) / Decimal("100")
    dependents = rng.randrange(0, 4)
    other = Decimal(rng.choice(("0.00", "50.00", "120.00", "200.00")))
    mode = rng.choice(("end", "truncate", "per_bracket"))
    values = calculate_payslip(
        base_salary=base_salary,
        additional=additional,
        dependents=dependents,
        other_deductions=other,
        mode=mode,
    )
    if document.split == "golden":
        period = "10/2026"
        admission = today - timedelta(days=20)
    else:
        period = f"{rng.randrange(1, 11):02d}/2026"
        admission = date(
            rng.randrange(2018, 2026),
            rng.randrange(1, 13),
            rng.randrange(1, 28),
        )
    fields = {
        "razao_social": rng.choice(company_pool),
        "cnpj_empregador": generate_cnpj(rng),
        "nome_funcionario": rng.choice(person_pool),
        "cpf_funcionario": generate_cpf(rng),
        "cargo": rng.choice(ROLES[language]),
        "cbo": f"{rng.randrange(100000, 999999)}",
        "periodo": period,
        "data_admissao": admission.isoformat(),
        "dependentes": str(dependents),
        "proventos_adicionais": values["proventos_adicionais"],
        "number_style": (
            "us"
            if language == "en" and rng.random() < 0.30
            else "br"
        ),
        **values,
    }
    original_fields = dict(fields)
    original_lines = []
    if document.split == "golden":
        original_lines = _render_lines(
            SyntheticDocument(
                **{**document.__dict__, "fields": original_fields}
            )
        )

    for tamper in document.tamper_types:
        if tamper == "P1":
            fields["salario_liquido"] = str(
                Decimal(fields["salario_liquido"]) + Decimal("500.00")
            )
        elif tamper == "P2":
            new_inss = (Decimal(fields["inss"]) * Decimal("0.8")).quantize(
                Decimal("0.01")
            )
            fields["inss"] = str(new_inss)
            fields["total_descontos"] = str(
                new_inss
                + Decimal(fields["irrf"])
                + Decimal("0.00")
            )
            fields["salario_liquido"] = str(
                Decimal(fields["salario_bruto"])
                - Decimal(fields["total_descontos"])
            )
        elif tamper == "P3":
            fields["irrf"] = "0.00"
            fields["total_descontos"] = str(
                Decimal(fields["inss"])
                + Decimal(fields["total_descontos"])
                - Decimal(fields["irrf"])
            )
            fields["salario_liquido"] = str(
                Decimal(fields["salario_bruto"])
                - Decimal(fields["total_descontos"])
            )
        elif tamper == "P4":
            new_base = Decimal(fields["salario_base"]) + Decimal("3000.00")
            recalculated = calculate_payslip(
                base_salary=new_base,
                additional=Decimal(fields["proventos_adicionais"]),
                dependents=int(fields["dependentes"]),
                other_deductions=Decimal("0.00"),
                mode="end",
            )
            fields.update(recalculated)
        elif tamper == "P5":
            fields["cpf_funcionario"] = "11111111111"
        elif tamper == "P6":
            fields["periodo"] = "12/2026"
        elif tamper == "P7":
            fields["fgts"] = str(Decimal(fields["fgts"]) + Decimal("100.00"))
        elif tamper == "P8":
            fields["total_descontos"] = str(
                Decimal(fields["inss"])
                + Decimal(fields["irrf"])
                - Decimal("10.00")
            )
            fields["salario_liquido"] = str(
                Decimal(fields["salario_bruto"])
                - Decimal(fields["total_descontos"])
            )
        elif tamper == "P9":
            fields["salario_liquido"] = str(
                Decimal(fields["salario_liquido"]) + Decimal("500.00")
            )
            document.pdf_edit = {
                "field": "salario_liquido",
                "before": original_fields["salario_liquido"],
                "after": fields["salario_liquido"],
                "before_text": format_amount(
                    Decimal(original_fields["salario_liquido"]),
                    language,
                    us_format=original_fields.get("number_style") == "us",
                ),
                "after_text": format_amount(
                    Decimal(fields["salario_liquido"]),
                    language,
                    us_format=fields.get("number_style") == "us",
                ),
            }

    document.fields = fields
    document.original_lines = original_lines
    document.lines = _render_lines(document)
    document.page_text = "\n".join(document.lines)


def build_document(
    *,
    index: int,
    base_seed: int,
    doc_kind: str,
    language: str,
    layout: str,
    label_set: str,
    split: str,
    tamper_types: list[str],
    today: date,
    shift: bool = False,
) -> SyntheticDocument:
    seed = base_seed + index * 1009
    rng = random.Random(seed)
    company_pool = SHIFT_COMPANIES[language] if shift else COMPANIES[language]
    bank_pool = SHIFT_BANKS if shift else BOLETO_BANKS
    sophistication, detectable, expected, band = _tamper_meta(tamper_types)
    document = SyntheticDocument(
        id=f"syn-{base_seed}-{index:05d}",
        seed=seed,
        doc_kind=doc_kind,
        language=language,
        layout=layout,
        label_set=label_set,
        split=split,
        is_fraud=bool(tamper_types),
        tamper_types=tamper_types,
        sophistication=sophistication,
        detectable_by=detectable,
        expected_codes_any_of=expected,
        intended_band=band,
        fields={},
        lines=[],
    )
    if doc_kind == "boleto":
        _make_boleto(
            rng,
            document,
            today,
            bank_pool,
            company_pool,
            PEOPLE[language],
        )
    else:
        _make_payslip(rng, document, today, company_pool, PEOPLE[language])
    return document


