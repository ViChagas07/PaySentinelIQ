from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from app.synthetic.evaluate import (
    BOLETO_FIELDS,
    PAYSLIP_FIELDS,
    _compare,
)

TAMPER_TYPES = [f"B{index}" for index in range(1, 9)] + [
    f"P{index}" for index in range(1, 10)
]
TRADE_OFF_TYPES = ("B1", "B2", "B4", "P1", "P2", "P5")
PATHS = ("A_native", "B_ocr_clean", "C_ocr_degraded")


def _load(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rate(hits: int, total: int) -> str:
    return f"{100 * hits / total:.1f}%" if total else "-"


def _by_path(dump: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in dump:
        grouped[item["path"]].append(item)
    return grouped


def _false_positive_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Falsos positivos por caminho",
        "",
        "| Caminho | Legítimos | Antes >= 70 | Antes >= 40 | Depois >= 70 | Depois >= 40 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    before_group = _by_path(before)
    after_group = _by_path(after)
    for path_name in PATHS:
        before_items = [item for item in before_group.get(path_name, []) if not item["is_fraud"]]
        after_items = [item for item in after_group.get(path_name, []) if not item["is_fraud"]]
        if not before_items and not after_items:
            continue
        total = len(after_items or before_items)
        lines.append(
            f"| {path_name} | {total} | "
            f"{sum(item['score'] >= 70 for item in before_items)} | "
            f"{sum(item['score'] >= 40 for item in before_items)} | "
            f"{sum(item['score'] >= 70 for item in after_items)} | "
            f"{sum(item['score'] >= 40 for item in after_items)} |"
        )
    lines.append("")
    return lines


def _top_codes(before: list[dict[str, Any]], after: list[dict[str, Any]], limit: int = 15) -> list[str]:
    lines = [
        "## Códigos em documentos legítimos (top 15)",
        "",
        "| Caminho | Código | Antes | Depois |",
        "|---|---|---:|---:|",
    ]
    before_group = _by_path(before)
    after_group = _by_path(after)
    for path_name in PATHS:
        before_counts = Counter(
            evidence["code"]
            for item in before_group.get(path_name, [])
            if not item["is_fraud"]
            for evidence in item["evidences"]
        )
        after_counts = Counter(
            evidence["code"]
            for item in after_group.get(path_name, [])
            if not item["is_fraud"]
            for evidence in item["evidences"]
        )
        codes = sorted(
            set(before_counts) | set(after_counts),
            key=lambda code: (-(before_counts[code] + after_counts[code]), code),
        )[:limit]
        for code in codes:
            lines.append(
                f"| {path_name} | {code} | {before_counts[code]} | "
                f"{after_counts[code]} |"
            )
    lines.append("")
    return lines


def _detection(
    dump: list[dict[str, Any]],
) -> dict[tuple[str, str], tuple[int, int]]:
    counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for item in dump:
        if not item["is_fraud"]:
            continue
        codes = {evidence["code"] for evidence in item["evidences"]}
        for tamper in item["tamper_types"]:
            counts[(item["path"], tamper)][1] += 1
            if codes & set(item["expected_codes_any_of"]):
                counts[(item["path"], tamper)][0] += 1
    return {key: (value[0], value[1]) for key, value in counts.items()}


def _detection_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Detecção por tipo de adulteração (B1-B8, P1-P9)",
        "",
        "| Caminho | Tipo | Antes | Depois |",
        "|---|---|---:|---:|",
    ]
    before_detection = _detection(before)
    after_detection = _detection(after)
    for path_name in PATHS:
        for tamper in TAMPER_TYPES:
            before_hits, before_total = before_detection.get(
                (path_name, tamper), (0, 0)
            )
            after_hits, after_total = after_detection.get(
                (path_name, tamper), (0, 0)
            )
            if not before_total and not after_total:
                continue
            lines.append(
                f"| {path_name} | {tamper} | "
                f"{before_hits}/{before_total} | {after_hits}/{after_total} |"
            )
    lines.append("")
    return lines


def _confusion_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Matriz de confusão da faixa",
        "",
        "| Caminho | Intenção | Antes L/M/H | Depois L/M/H |",
        "|---|---|---|---|",
    ]
    for path_name in PATHS:
        for intended in ("LOW", "MEDIUM", "HIGH"):
            before_counts = Counter(
                item["risk_level"]
                for item in before
                if item["path"] == path_name
                and item["is_fraud"]
                and item["intended_band"] == intended
            )
            after_counts = Counter(
                item["risk_level"]
                for item in after
                if item["path"] == path_name
                and item["is_fraud"]
                and item["intended_band"] == intended
            )
            if not before_counts and not after_counts:
                continue
            lines.append(
                f"| {path_name} | {intended} | "
                f"{before_counts['LOW']}/{before_counts['MEDIUM']}/{before_counts['HIGH']} | "
                f"{after_counts['LOW']}/{after_counts['MEDIUM']}/{after_counts['HIGH']} |"
            )
    lines.append("")
    return lines


def _field_accuracy(dump: list[dict[str, Any]]) -> tuple[dict[str, list[int]], dict[tuple[str, str], list[int]]]:
    overall: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_field: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for item in dump:
        fields = (
            BOLETO_FIELDS
            if item["document_type"] == "boleto"
            else PAYSLIP_FIELDS
        )
        source = {
            "doc_kind": item["document_type"],
            "fields": item["gabarito_fields"],
        }
        for field in fields:
            match = _compare(source, item["extracted_fields"], field)
            overall[item["path"]][1] += 1
            by_field[(item["path"], field)][1] += 1
            if match:
                overall[item["path"]][0] += 1
                by_field[(item["path"], field)][0] += 1
    return overall, by_field


def _extraction_table(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    before_overall, before_field = _field_accuracy(before)
    after_overall, after_field = _field_accuracy(after)
    lines = [
        "## Acurácia de extração por caminho",
        "",
        "| Caminho | Antes | Depois |",
        "|---|---:|---:|",
    ]
    for path_name in PATHS:
        b = before_overall.get(path_name, [0, 0])
        a = after_overall.get(path_name, [0, 0])
        lines.append(
            f"| {path_name} | {_rate(b[0], b[1])} | {_rate(a[0], a[1])} |"
        )
    lines.extend(
        [
            "",
            "### Acurácia por campo",
            "",
            "| Caminho | Campo | Antes | Depois |",
            "|---|---|---:|---:|",
        ]
    )
    for path_name in PATHS:
        fields = sorted(
            {
                key[1]
                for key in before_field
                if key[0] == path_name
            }
            | {
                key[1]
                for key in after_field
                if key[0] == path_name
            }
        )
        for field in fields:
            b = before_field.get((path_name, field), [0, 0])
            a = after_field.get((path_name, field), [0, 0])
            lines.append(
                f"| {path_name} | {field} | {_rate(b[0], b[1])} | "
                f"{_rate(a[0], a[1])} |"
            )
    lines.append("")
    return lines


def _taxonomy(dump: list[dict[str, Any]]) -> list[str]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for item in dump:
        extracted = item["extracted_fields"]
        fields = (
            BOLETO_FIELDS
            if item["document_type"] == "boleto"
            else PAYSLIP_FIELDS
        )
        source = {
            "doc_kind": item["document_type"],
            "fields": item["gabarito_fields"],
        }
        for field in fields:
            if _compare(source, extracted, field):
                continue
            value = extracted.get(field)
            cause = (
                "AUSENTE"
                if value is None or value == "" or value == []
                else "ERRADO"
            )
            counts[
                (
                    cause,
                    item["path"],
                    field,
                    item["layout"],
                    item["language"],
                )
            ] += 1
    lines = [
        "## Taxonomia de erros de extração (depois)",
        "",
        "| Causa | Caminho | Campo | Layout | Idioma | Ocorrências |",
        "|---|---|---|---|---|---:|",
    ]
    for key, count in sorted(counts.items()):
        cause, path_name, field, layout, language = key
        lines.append(
            f"| {cause} | {path_name} | {field} | {layout} | {language} | "
            f"{count} |"
        )
    lines.append("")
    return lines


def _score_detection(
    dump: list[dict[str, Any]],
    path_name: str,
    tamper: str,
) -> tuple[int, int, int, int]:
    items = [
        item
        for item in dump
        if item["path"] == path_name
        and item["is_fraud"]
        and tamper in item["tamper_types"]
    ]
    return (
        sum(item["score"] >= 70 for item in items),
        sum(item["score"] >= 40 for item in items),
        len(items),
        0,
    )


def _trade_off(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Trade-off do rebaixamento por OCR",
        "",
        "Detecção por score (não por presença de código) nos caminhos B e C "
        "para os tipos afetados pela mitigação provisória de OCR.",
        "",
        "| Caminho | Tipo | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for path_name in ("B_ocr_clean", "C_ocr_degraded"):
        for tamper in TRADE_OFF_TYPES:
            before_high, before_medium, before_total, _ = _score_detection(
                before, path_name, tamper
            )
            after_high, after_medium, after_total, _ = _score_detection(
                after, path_name, tamper
            )
            total = after_total or before_total
            if not total:
                lines.append(
                    f"| {path_name} | {tamper} | 0/0 | 0/0 | 0/0 | 0/0 |"
                )
                continue
            lines.append(
                f"| {path_name} | {tamper} | "
                f"{before_high}/{total} | {after_high}/{total} | "
                f"{before_medium}/{total} | {after_medium}/{total} |"
            )
    lines.append("")
    return lines


def build_report(
    before_path: Path,
    after_path: Path,
    attribution_path: Path,
    title: str,
) -> str:
    before = _load(before_path)
    after = _load(after_path)
    lines = [
        f"# {title}",
        "",
        "Antes = harness corrigido da 5B.0, sem correções de regra. "
        "Depois = mesmas 1000 documentos, seed 42, 60 renderizados, com as "
        "mudanças da 5B.2 a 5B.7.",
        "",
    ]
    lines.extend(_false_positive_table(before, after))
    lines.extend(_top_codes(before, after))
    lines.extend(_detection_table(before, after))
    lines.extend(_confusion_table(before, after))
    lines.extend(_extraction_table(before, after))
    lines.extend(_trade_off(before, after))
    lines.extend(_taxonomy(after))
    if attribution_path.exists():
        high_after = sum(
            1 for item in after if not item["is_fraud"] and item["score"] >= 70
        )
        lines.extend(
            [
                "## Atribuição de falsos positivos (depois)",
                "",
                f"Relatório completo: `{attribution_path.name}`. "
                f"Legítimos com score >= 70 depois: {high_after}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitações",
            "",
            "- Os números valem para o golden set sintético desta máquina, "
            "seed 42; não são uma estimativa de produção.",
            "- O caminho A usa a camada nativa via `run_ocr_prelude` com provider "
            "nativo-primeiro; B e C usam o serviço de OCR local.",
            "- A mitigação de OCR é provisória e troca recall por menos falsos "
            "positivos até existir corroboração por segunda leitura.",
            "- B6/B7/P4 continuam sem detector dedicado nesta fase.",
            "- O gerador ainda carrega artefatos históricos de codificação em "
            "alguns rótulos; a taxonomia abaixo mostra onde isso vira campo "
            "AUSENTE ou ERRADO.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--attribution", default="docs/eval/fp_attribution_after.md")
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--title",
        default="Medição depois da Fase 5B — comparação antes/depois",
    )
    args = parser.parse_args()
    report = build_report(
        Path(args.before),
        Path(args.after),
        Path(args.attribution),
        args.title,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
