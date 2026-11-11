from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from app.synthetic.evaluate import (
    BOLETO_FIELDS,
    PAYSLIP_FIELDS,
    _compare,
)

TARGET_BOLETO = ("valor_nominal", "data_vencimento")
TARGET_PAYSLIP = (
    "salario_bruto",
    "salario_liquido",
    "total_descontos",
    "inss",
    "irrf",
    "fgts",
)
INTEREST = ("B1", "B2", "P1", "P2", "P3", "P7", "P8")


def _load(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _field(source: dict[str, Any], item: dict[str, Any], name: str) -> bool | None:
    return _compare(
        {"doc_kind": source["document_type"], "fields": source["gabarito_fields"]},
        source["extracted_fields"],
        name,
    )


def _evidence_codes(item: dict[str, Any]) -> set[str]:
    return {evidence["code"] for evidence in item["evidences"]}


def _same_date(first: Any, second: Any) -> bool:
    if not first or not second:
        return False
    from datetime import date, datetime

    def parse(value: Any) -> date | None:
        if isinstance(value, date):
            return value
        text = str(value)
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            try:
                return datetime.strptime(text[:10], "%d/%m/%Y").date()
            except ValueError:
                return None

    left, right = parse(first), parse(second)
    return left is not None and left == right


def _due_cause(item: dict[str, Any]) -> str:
    extracted = item["extracted_fields"]
    gabarito = item["gabarito_fields"]
    evidence = next(
        evidence
        for evidence in item["evidences"]
        if evidence["code"] == "BOLETO_DUE_DATE_MISMATCH"
    )
    metadata = evidence.get("metadata") or {}
    printed = metadata.get("impresso")
    encoded = metadata.get("codificado")
    due = extracted.get("data_vencimento")
    expected = gabarito.get("data_vencimento")
    if not due:
        return "DATA_AUSENTE"
    if _same_date(due, expected) and encoded and not _same_date(encoded, expected):
        return "VENCIMENTO_DECODIFICADO_ERRADO"
    if not _same_date(due, expected):
        if _same_date(extracted.get("data_emissao"), expected):
            return "DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO"
        if _same_date(extracted.get("data_documento"), expected):
            return "DATA_ERRADA_TROCA_DOCUMENTO_VENCIMENTO"
        if printed and not _same_date(printed, expected):
            return "DATA_ERRADA_LOCALE_OU_LEITURA"
    if printed == expected and encoded != expected:
        return "VENCIMENTO_DECODIFICADO_ERRADO"
    return "DIVERGENCIA_REAL_GERADOR"


def _section_due(dump: list[dict[str, Any]]) -> list[str]:
    items = [
        item
        for item in dump
        if item["path"] == "A_native"
        and not item["is_fraud"]
        and "BOLETO_DUE_DATE_MISMATCH" in _evidence_codes(item)
    ]
    lines = [
        "## 1. BOLETO_DUE_DATE_MISMATCH em legítimos",
        "",
        f"Total: **{len(items)}**.",
        "",
        "| ID | Idioma | Layout | data extraída | gabarito | data_documento | data_emissão | causa |",
        "|---|---|---|---|---|---|---|---|",
    ]
    counts: Counter[str] = Counter()
    for item in items:
        cause = _due_cause(item)
        counts[cause] += 1
        extracted = item["extracted_fields"]
        lines.append(
            f"| {item['document_id']} | {item['language']} | {item['layout']} | "
            f"{extracted.get('data_vencimento')} | "
            f"{item['gabarito_fields'].get('data_vencimento')} | "
            f"{extracted.get('data_documento')} | "
            f"{extracted.get('data_emissao')} | {cause} |"
        )
    lines.extend(
        [
            "",
            "| Causa | Ocorrências |",
            "|---|---:|",
            *[f"| {cause} | {count} |" for cause, count in counts.items()],
            "",
        ]
    )
    return lines


def _section_irrf(dump: list[dict[str, Any]]) -> list[str]:
    items = [
        item
        for item in dump
        if item["path"] == "A_native"
        and not item["is_fraud"]
        and "PAYSLIP_IRRF_MISMATCH" in _evidence_codes(item)
    ]
    lines = [
        "## 2. PAYSLIP_IRRF_MISMATCH em legítimos",
        "",
        f"Total: **{len(items)}**.",
        "",
        "| ID | Idioma | Layout | bruto | inss extraído | inss gabarito | irrf extraído | base_irrf extraída | dependentes | causa |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    counts: Counter[str] = Counter()
    for item in items:
        extracted = item["extracted_fields"]
        gabarito = item["gabarito_fields"]
        missing = []
        if extracted.get("inss") is None:
            missing.append("inss")
        if extracted.get("base_irrf") is None:
            missing.append("base_irrf")
        if extracted.get("salario_bruto") is None:
            missing.append("salario_bruto")
        cause = (
            "EXTRACAO_AUSENTE_" + "_".join(missing).upper()
            if missing
            else "DIVERGENCIA_REGRA_GERADOR"
        )
        counts[cause] += 1
        lines.append(
            f"| {item['document_id']} | {item['language']} | {item['layout']} | "
            f"{extracted.get('salario_bruto')} | {extracted.get('inss')} | "
            f"{gabarito.get('inss')} | {extracted.get('irrf')} | "
            f"{extracted.get('base_irrf')} | {extracted.get('dependentes')} | "
            f"{cause} |"
        )
    lines.extend(
        [
            "",
            "| Causa | Ocorrências |",
            "|---|---:|",
            *[f"| {cause} | {count} |" for cause, count in counts.items()],
            "",
        ]
    )
    return lines


def _section_low(dump: list[dict[str, Any]]) -> list[str]:
    items = [
        item
        for item in dump
        if item["is_fraud"]
        and item["sophistication"] in {"naive", "multi"}
        and item["score"] < 40
    ]
    lines = [
        "## 3. Adulterados naive/multi em LOW",
        "",
        f"Total: **{len(items)}** (todos os caminhos).",
        "",
        "| Caminho | ID | Tipos | Classe | Score | Faixa | Códigos esperados | Evidências (código/sev/fonte/ocr_uncertain) |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    counts: Counter[str] = Counter()
    for item in items:
        codes = _evidence_codes(item)
        expected = set(item["expected_codes_any_of"])
        if not (codes & expected):
            classification = "NENHUMA_EVIDENCIA_GERADA"
        else:
            classification = "EVIDENCIA_GERADA_SCORE_INSUFICIENTE"
        counts[classification] += 1
        evidence_text = "; ".join(
            f"{evidence['code']}/{evidence['severity']}/{evidence['source']}/"
            f"{bool((evidence.get('metadata') or {}).get('ocr_uncertain'))}"
            for evidence in item["evidences"]
        ) or "-"
        lines.append(
            f"| {item['path']} | {item['document_id']} | "
            f"{','.join(item['tamper_types'])} | "
            f"{classification} | {item['score']} | {item['risk_level']} | "
            f"{','.join(item['expected_codes_any_of'])} | {evidence_text} |"
        )
    lines.extend(
        [
            "",
            "| Classe | Ocorrências |",
            "|---|---:|",
            *[f"| {key} | {value} |" for key, value in counts.items()],
            "",
        ]
    )
    return lines


def _section_interest(dump: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 4. Falhas restantes por tipo de adulteração",
        "",
        "Somente `A_native`, naive/multi, código esperado ausente.",
        "",
        "| Tipo | ID | Idioma | Layout | Campos ausentes | Campos errados | Score |",
        "|---|---|---|---|---|---|---:|",
    ]
    for tamper in INTEREST:
        items = [
            item
            for item in dump
            if item["path"] == "A_native"
            and item["is_fraud"]
            and item["sophistication"] in {"naive", "multi"}
            and tamper in item["tamper_types"]
            and not (_evidence_codes(item) & set(item["expected_codes_any_of"]))
        ]
        for item in items:
            fields = (
                BOLETO_FIELDS
                if item["document_type"] == "boleto"
                else PAYSLIP_FIELDS
            )
            missing = [
                field
                for field in fields
                if _field(item, item, field) is False
                and item["extracted_fields"].get(field) in (None, "", [])
            ]
            wrong = [
                field
                for field in fields
                if _field(item, item, field) is False
                and item["extracted_fields"].get(field) not in (None, "", [])
            ]
            lines.append(
                f"| {tamper} | {item['document_id']} | {item['language']} | "
                f"{item['layout']} | {','.join(missing) or '-'} | "
                f"{','.join(wrong) or '-'} | {item['score']} |"
            )
    lines.append("")
    return lines


def _section_missing(dump: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 5. Cobertura dos campos-alvo",
        "",
        "A_native, legítimos + adulterados.",
        "",
        "| Tipo | Layout | Idioma | Campo | AUSENTE | ERRADO | OK |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for item in dump:
        if item["path"] != "A_native":
            continue
        fields: tuple[str, ...]
        if item["document_type"] == "boleto":
            fields = TARGET_BOLETO
        else:
            fields = TARGET_PAYSLIP
        for field in fields:
            value = item["extracted_fields"].get(field)
            match = _field(item, item, field)
            if match:
                state = "OK"
            elif value in (None, "", []):
                state = "AUSENTE"
            else:
                state = "ERRADO"
            counts[
                (
                    item["document_type"],
                    item["layout"],
                    item["language"],
                    field,
                    state,
                )
            ] += 1
    for key in sorted(counts):
        doc_type, layout, language, field, state = key
        if state == "OK":
            continue
        ok = counts[(doc_type, layout, language, field, "OK")]
        absent = counts[(doc_type, layout, language, field, "AUSENTE")]
        wrong = counts[(doc_type, layout, language, field, "ERRADO")]
        lines.append(
            f"| {doc_type} | {layout} | {language} | {field} | "
            f"{absent} | {wrong} | {ok} |"
        )
    lines.append("")
    return lines


def build(dump_path: Path) -> str:
    dump = _load(dump_path)
    lines = [
        "# 6A.0 — Auditoria antes das correções",
        "",
        f"Fonte: `{dump_path.as_posix()}` (dataset v1, pós-5B).",
        "",
    ]
    lines.extend(_section_due(dump))
    lines.extend(_section_irrf(dump))
    lines.extend(_section_low(dump))
    lines.extend(_section_interest(dump))
    lines.extend(_section_missing(dump))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dump",
        default="../data/synthetic/eval/evidence_dump.jsonl",
    )
    parser.add_argument("--out", default="docs/eval/6a0_audit.md")
    args = parser.parse_args()
    report = build(Path(args.dump))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
