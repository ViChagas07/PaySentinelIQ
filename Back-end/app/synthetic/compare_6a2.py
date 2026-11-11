from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Callable

from app.synthetic.evaluate import BOLETO_FIELDS, PAYSLIP_FIELDS, _compare

PATHS = ("A_native", "B_ocr_clean", "C_ocr_degraded")
SPLITS = ("train", "val", "test_iid", "test_shift")
TAMPERS = [f"B{index}" for index in range(1, 9)] + [
    f"P{index}" for index in range(1, 10)
]
EXPERTS = ("B6", "B7", "P4")


def _load(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rate(hits: int, total: int) -> str:
    return f"{100 * hits / total:.1f}%" if total else "-"


def _fields(item: dict[str, Any]) -> tuple[str, ...]:
    return BOLETO_FIELDS if item["document_type"] == "boleto" else PAYSLIP_FIELDS


def _match(item: dict[str, Any], field: str) -> bool | None:
    return _compare(
        {
            "doc_kind": item["document_type"],
            "fields": item["gabarito_fields"],
        },
        item["extracted_fields"],
        field,
    )


def _accuracy(
    dump: list[dict[str, Any]],
    selector: Callable[[dict[str, Any]], bool],
    field_name: str | None = None,
) -> tuple[int, int]:
    hits = total = 0
    for item in dump:
        if not selector(item):
            continue
        for field in _fields(item):
            if field_name is not None and field != field_name:
                continue
            total += 1
            if _match(item, field):
                hits += 1
    return hits, total


def _accuracy_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Acurácia de extração",
        "",
        "| Dimensão | Caminho | Antes | Depois |",
        "|---|---|---:|---:|",
    ]
    for path_name in PATHS:
        for label, selector in (
            ("geral", lambda item, p=path_name: item["path"] == p),
            (
                "test_shift",
                lambda item, p=path_name: item["path"] == p
                and item["split"] == "test_shift",
            ),
            (
                "test_iid",
                lambda item, p=path_name: item["path"] == p
                and item["split"] == "test_iid",
            ),
        ):
            b = _accuracy(before, selector)
            a = _accuracy(after, selector)
            lines.append(
                f"| {label} | {path_name} | {_rate(*b)} | {_rate(*a)} |"
            )
    lines.extend(
        [
            "",
            "### Por campo (test_shift)",
            "",
            "| Caminho | Campo | Antes | Depois |",
            "|---|---|---:|---:|",
        ]
    )
    for path_name in PATHS:
        for field in sorted(
            {
                field
                for item in after
                if item["path"] == path_name and item["split"] == "test_shift"
                for field in _fields(item)
            }
        ):
            selector = (
                lambda item, p=path_name: item["path"] == p
                and item["split"] == "test_shift"
            )
            b = _accuracy(before, selector, field_name=field)
            a = _accuracy(after, selector, field_name=field)
            lines.append(
                f"| {path_name} | {field} | {_rate(*b)} | {_rate(*a)} |"
            )
    lines.append("")
    return lines


def _taxonomy(dump: list[dict[str, Any]]) -> list[str]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for item in dump:
        if item["path"] != "A_native":
            continue
        for field in _fields(item):
            if _match(item, field):
                continue
            value = item["extracted_fields"].get(field)
            if item["extracted_fields"].get(f"{field}_ambiguous"):
                cause = "AMBIGUO"
            elif value in (None, "", []):
                cause = "AUSENTE"
            else:
                cause = "ERRADO"
            counts[
                (
                    cause,
                    item["document_type"],
                    field,
                    item["layout"],
                    item["language"],
                )
            ] += 1
    lines = [
        "## Erros de extração AUSENTE / ERRADO / AMBÍGUO (after, native)",
        "",
        "| Causa | Tipo | Campo | Layout | Idioma | Ocorrências |",
        "|---|---|---|---|---|---:|",
    ]
    for key, count in sorted(counts.items()):
        cause, doc_type, field, layout, language = key
        lines.append(
            f"| {cause} | {doc_type} | {field} | {layout} | {language} | "
            f"{count} |"
        )
    lines.append("")
    return lines


def _false_positive_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Falsos positivos",
        "",
        "| Caminho | Split | Legítimos | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for path_name in PATHS:
        for split in SPLITS:
            before_items = [
                item
                for item in before
                if item["path"] == path_name
                and item["split"] == split
                and not item["is_fraud"]
            ]
            after_items = [
                item
                for item in after
                if item["path"] == path_name
                and item["split"] == split
                and not item["is_fraud"]
            ]
            total = len(after_items)
            lines.append(
                f"| {path_name} | {split} | {total} | "
                f"{sum(item['score'] >= 70 for item in before_items)} | "
                f"{sum(item['score'] >= 70 for item in after_items)} | "
                f"{sum(item['score'] >= 40 for item in before_items)} | "
                f"{sum(item['score'] >= 40 for item in after_items)} |"
            )
    lines.append("")
    return lines


def _detection(
    dump: list[dict[str, Any]],
    path_name: str,
    split: str,
    tamper: str,
) -> tuple[int, int]:
    items = [
        item
        for item in dump
        if item["path"] == path_name
        and item["split"] == split
        and item["is_fraud"]
        and tamper in item["tamper_types"]
        and item["sophistication"] in {"naive", "multi"}
    ]
    hits = sum(
        bool(
            {evidence["code"] for evidence in item["evidences"]}
            & set(item["expected_codes_any_of"])
        )
        for item in items
    )
    return hits, len(items)


def _detection_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Detecção por código em naive/multi",
        "",
        "| Caminho | Split | Tipo | Antes | Depois |",
        "|---|---|---|---:|---:|",
    ]
    for path_name in PATHS:
        for split in SPLITS:
            for tamper in TAMPERS:
                b = _detection(before, path_name, split, tamper)
                a = _detection(after, path_name, split, tamper)
                if not b[1] and not a[1]:
                    continue
                lines.append(
                    f"| {path_name} | {split} | {tamper} | "
                    f"{b[0]}/{b[1]} | {a[0]}/{a[1]} |"
                )
    lines.append("")
    return lines


def _band_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Detecção por faixa em naive/multi",
        "",
        "| Caminho | Split | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for path_name in PATHS:
        for split in SPLITS:
            before_items = [
                item
                for item in before
                if item["path"] == path_name
                and item["split"] == split
                and item["is_fraud"]
                and item["sophistication"] in {"naive", "multi"}
            ]
            after_items = [
                item
                for item in after
                if item["path"] == path_name
                and item["split"] == split
                and item["is_fraud"]
                and item["sophistication"] in {"naive", "multi"}
            ]
            total = len(after_items)
            if not total:
                continue
            lines.append(
                f"| {path_name} | {split} | "
                f"{sum(item['score'] >= 70 for item in before_items)}/{total} | "
                f"{sum(item['score'] >= 70 for item in after_items)}/{total} | "
                f"{sum(item['score'] >= 40 for item in before_items)}/{total} | "
                f"{sum(item['score'] >= 40 for item in after_items)}/{total} |"
            )
    lines.append("")
    return lines


def _expert_table(after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Especialistas B6 / B7 / P4 (fora da cobertura)",
        "",
        "| Caminho | Tipo | Documentos | Evidência esperada presente | Faixa HIGH |",
        "|---|---|---:|---:|---:|",
    ]
    for path_name in PATHS:
        for tamper in EXPERTS:
            items = [
                item
                for item in after
                if item["path"] == path_name
                and item["is_fraud"]
                and tamper in item["tamper_types"]
            ]
            if not items:
                continue
            hits = sum(
                bool(
                    {evidence["code"] for evidence in item["evidences"]}
                    & set(item["expected_codes_any_of"])
                )
                for item in items
            )
            high = sum(item["risk_level"] == "HIGH" for item in items)
            lines.append(
                f"| {path_name} | {tamper} | {len(items)} | {hits} | {high} |"
            )
    lines.append("")
    return lines


def build_report(before: list[dict[str, Any]], after: list[dict[str, Any]], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "Antes = dataset v2 com extração anterior à 6A.2. Depois = mesmo dataset "
        "v2 com as correções cirúrgicas. Números de v1 não entram neste "
        "comparativo.",
        "",
    ]
    lines.extend(_accuracy_table(before, after))
    lines.extend(_taxonomy(after))
    lines.extend(_false_positive_table(before, after))
    lines.extend(_detection_table(before, after))
    lines.extend(_band_table(before, after))
    lines.extend(_expert_table(after))
    lines.extend(
        [
            "## Limitações",
            "",
            "- `test_shift` tem 100 documentos e 60 renderizações; os caminhos "
            "OCR têm poucas observações por tipo.",
            "- A avaliação OCR ainda não cobre todos os B1-B8/P1-P9; isso é "
            "escopo da 6A.3.",
            "- B6/B7/P4 continuam sem sinal interno suficiente e são reportados "
            "separadamente.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--title",
        default="6A.2 — comparação antes/depois no dataset v2",
    )
    args = parser.parse_args()
    report = build_report(
        _load(Path(args.before)),
        _load(Path(args.after)),
        args.title,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
