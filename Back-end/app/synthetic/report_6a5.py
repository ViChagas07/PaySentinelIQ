from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from app.synthetic.evaluate import BOLETO_FIELDS, PAYSLIP_FIELDS, _compare
from app.synthetic.evaluate_ocr_6a3 import _forensic_signal
from app.synthetic.policy_6a import _score, _aggregate, v5_decision

PATHS = ("A_native", "B_ocr_clean", "C_ocr_degraded")
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


def _fields(item: dict[str, Any]) -> tuple[str, ...]:
    return BOLETO_FIELDS if item["document_type"] == "boleto" else PAYSLIP_FIELDS


def _match(item: dict[str, Any], field: str) -> bool | None:
    return _compare(
        {"doc_kind": item["document_type"], "fields": item["gabarito_fields"]},
        item["extracted_fields"],
        field,
    )


def _rate(hits: int, total: int) -> str:
    return f"{100 * hits / total:.1f}%" if total else "-"


def _accuracy_by(
    rows: list[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], str],
) -> dict[tuple[str, str], list[int]]:
    counts: dict[tuple[str, str], list[int]] = {}
    for item in rows:
        key = (item["path"], key_fn(item))
        for field in _fields(item):
            bucket = counts.setdefault(key, [0, 0])
            bucket[1] += 1
            if _match(item, field):
                bucket[0] += 1
    return counts


def _accuracy_table(rows: list[dict[str, Any]], title: str, key_fn: Callable[[dict[str, Any]], str]) -> list[str]:
    counts = _accuracy_by(rows, key_fn)
    lines = [
        f"### {title}",
        "",
        "| Caminho | Dimensão | Acertos | N |",
        "|---|---|---:|---:|",
    ]
    for (path_name, dimension), (hits, total) in sorted(counts.items()):
        lines.append(
            f"| {path_name} | {dimension} | {_rate(hits, total)} | {total} |"
        )
    lines.append("")
    return lines


def _detected(item: dict[str, Any]) -> bool:
    return bool(
        {evidence["code"] for evidence in item["evidences"]}
        & set(item["expected_codes_any_of"])
    )


def _detection_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Detecção por código",
        "",
        "| Tipo | Caminho | N | Detectados | Cobertura | Amostra |",
        "|---|---|---:|---:|---:|---|",
    ]
    for tamper in TAMPERS:
        if tamper in EXPERTS:
            continue
        documents = [
            item
            for item in rows
            if item["is_fraud"]
            and tamper in item["tamper_types"]
            and item["sophistication"] in {"naive", "multi"}
        ]
        for path_name in PATHS:
            selected = [item for item in documents if item["path"] == path_name]
            hits = sum(_detected(item) for item in selected)
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | {hits} | "
                f"{_rate(hits, len(selected))} | "
                f"{'suficiente' if len(selected) >= 5 else 'indicativo'} |"
            )
    lines.append("")
    return lines


def _band_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Recall por faixa (naive e multi)",
        "",
        "| Caminho | Classe | N | >=70 | >=40 |",
        "|---|---|---:|---:|---:|",
    ]
    for path_name in PATHS:
        for label, selector in (
            (
                "naive+multi",
                lambda item: item["sophistication"] in {"naive", "multi"},
            ),
            ("multi", lambda item: item["sophistication"] == "multi"),
        ):
            selected = [
                item
                for item in rows
                if item["path"] == path_name
                and item["is_fraud"]
                and selector(item)
            ]
            lines.append(
                f"| {path_name} | {label} | {len(selected)} | "
                f"{sum(item['score'] >= 70 for item in selected)} | "
                f"{sum(item['score'] >= 40 for item in selected)} |"
            )
    lines.append("")
    return lines


def _fp_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Falsos positivos",
        "",
        "| Caminho | Legítimos | >=70 | >=40 |",
        "|---|---:|---:|---:|",
    ]
    for path_name in PATHS:
        legitimate = [
            item
            for item in rows
            if item["path"] == path_name and not item["is_fraud"]
        ]
        lines.append(
            f"| {path_name} | {len(legitimate)} | "
            f"{sum(item['score'] >= 70 for item in legitimate)} | "
            f"{sum(item['score'] >= 40 for item in legitimate)} |"
        )
    lines.append("")
    return lines


def _expert_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Especialistas B6 / B7 / P4",
        "",
        "| Tipo | Caminho | N | Código esperado |",
        "|---|---|---:|---:|",
    ]
    for tamper in EXPERTS:
        documents = [
            item
            for item in rows
            if item["is_fraud"] and tamper in item["tamper_types"]
        ]
        for path_name in PATHS:
            selected = [item for item in documents if item["path"] == path_name]
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | "
                f"{sum(_detected(item) for item in selected)} |"
            )
    lines.append("")
    return lines


def _b8_p9_table(
    rows: list[dict[str, Any]],
    native_dump_rows: list[dict[str, Any]],
    eval_files: Path,
) -> list[str]:
    lines = [
        "## B8 / P9 — aritmética vs. sinal forense",
        "",
        "| Tipo | Caminho | N | Código aritmético | Sinal forense |",
        "|---|---|---:|---:|---:|",
    ]
    for tamper in ("B8", "P9"):
        documents = [
            item
            for item in rows
            if item["is_fraud"] and tamper in item["tamper_types"]
        ]
        for path_name in PATHS:
            selected = [item for item in documents if item["path"] == path_name]
            forensic = 0
            if path_name == "A_native":
                for item in selected:
                    path = eval_files / "native" / f"{item['document_id']}.pdf"
                    if path.exists() and _forensic_signal(path):
                        forensic += 1
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | "
                f"{sum(_detected(item) for item in selected)} | {forensic} |"
            )
    lines.extend(
        [
            "",
            "Sinal forense = `creator`/`producer` diferentes do gerador padrão no "
            "PDF nativo. OCR rasteriza o PDF e remove o metadado; ausência não "
            "prova autenticidade.",
            "",
        ]
    )
    return lines


def _policy_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Políticas shadow V0 / V2 / V4 / V5",
        "",
        "| Variante | Caminho | N | FP >=70 | FP >=40 | Recall naive >=40 | "
        "Recall naive >=70 | Recall multi >=40 | Recall multi >=70 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in ("V0", "V2", "V4"):
        for path_name in PATHS:
            items = [item for item in rows if item["path"] == path_name]
            legit = [item for item in items if not item["is_fraud"]]
            naive = [
                item
                for item in items
                if item["is_fraud"] and item["sophistication"] in {"naive", "multi"}
            ]
            multi = [
                item
                for item in items
                if item["is_fraud"] and item["sophistication"] == "multi"
            ]
            scores = {item["document_id"]: _score(item["evidences"], variant) for item in items}
            lines.append(
                f"| {variant} | {path_name} | {len(items)} | "
                f"{sum(scores[item['document_id']] >= 70 for item in legit)} | "
                f"{sum(scores[item['document_id']] >= 40 for item in legit)} | "
                f"{sum(scores[item['document_id']] >= 40 for item in naive)} | "
                f"{sum(scores[item['document_id']] >= 70 for item in naive)} | "
                f"{sum(scores[item['document_id']] >= 40 for item in multi)} | "
                f"{sum(scores[item['document_id']] >= 70 for item in multi)} |"
            )
    lines.extend(
        [
            "",
            "### V5 — decisão e revisão",
            "",
            "| Caminho | N | HIGH | MEDIUM | LOW | needs_review | Dados insuficientes | "
            "FP MEDIUM+ | Recall naive MEDIUM+ |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for path_name in PATHS:
        items = [item for item in rows if item["path"] == path_name]
        decisions = [v5_decision(item) for item in items]
        legit = [item for item in items if not item["is_fraud"]]
        naive = [
            item
            for item in items
            if item["is_fraud"] and item["sophistication"] in {"naive", "multi"}
        ]

        def material(items_: list[dict[str, Any]]) -> int:
            return sum(
                v5_decision(item)["decision"] in {"HIGH", "MEDIUM"}
                for item in items_
            )

        lines.append(
            f"| {path_name} | {len(items)} | "
            f"{sum(item['decision'] == 'HIGH' for item in decisions)} | "
            f"{sum(item['decision'] == 'MEDIUM' for item in decisions)} | "
            f"{sum(item['decision'] == 'LOW' for item in decisions)} | "
            f"{sum(item['needs_review'] for item in decisions)} | "
            f"{sum(bool(item['missing_fields']) for item in decisions)} | "
            f"{material(legit)} | {material(naive)} |"
        )
    lines.append("")
    return lines


def build_report(
    native_rows: list[dict[str, Any]],
    ocr_rows: list[dict[str, Any]],
    eval_files: Path,
) -> str:
    ocr_docs = [
        item
        for path_name in ("B_ocr_clean", "C_ocr_degraded")
        for item in _aggregate(ocr_rows, path_name)
    ]
    rows = [*native_rows, *ocr_docs]
    lines = [
        "# 6A.5 — Relatório final do checkpoint 6A",
        "",
        "Dataset v2.1. Native = dump completo (1000 documentos). OCR = 6A.3 "
        "(112 documentos; 40 legítimos), agregado por documento/path pela melhor "
        "variante. N é informado em todas as tabelas.",
        "",
        "Os conjuntos são de desenvolvimento/avaliação, não holdout intocado.",
        "",
        "## N por caminho",
        "",
        "| Caminho | N | Legítimos | Adulterados naive/multi |",
        "|---|---:|---:|---:|",
    ]
    for path_name in PATHS:
        selected = [item for item in rows if item["path"] == path_name]
        lines.append(
            f"| {path_name} | {len(selected)} | "
            f"{sum(1 for item in selected if not item['is_fraud'])} | "
            f"{sum(1 for item in selected if item['is_fraud'] and item['sophistication'] in {'naive', 'multi'})} |"
        )

    lines.extend(
        [
            "",
            "## Acurácia de extração",
            "",
            "N = campos comparados; OCR inclui todas as variantes observadas.",
            "",
        ]
    )
    extraction_rows = [*native_rows, *ocr_rows]
    counts: dict[tuple[str, str], list[int]] = {}
    for item in extraction_rows:
        for field in _fields(item):
            bucket = counts.setdefault((item["path"], field), [0, 0])
            bucket[1] += 1
            if _match(item, field):
                bucket[0] += 1
    lines.extend(
        [
            "| Caminho | Campo | Acertos | N |",
            "|---|---|---:|---:|",
        ]
    )
    for (path_name, field), (hits, total) in sorted(counts.items()):
        lines.append(
            f"| {path_name} | {field} | {_rate(hits, total)} | {total} |"
        )
    lines.append("")
    lines.extend(_accuracy_table(extraction_rows, "Por idioma", lambda item: item["language"]))
    lines.extend(_accuracy_table(extraction_rows, "Por layout", lambda item: item["layout"]))
    lines.extend(_accuracy_table(extraction_rows, "Por tipo", lambda item: item["document_type"]))
    lines.extend(_detection_table(rows))
    lines.extend(_band_table(rows))
    lines.extend(_fp_table(rows))
    lines.extend(_expert_table(rows))
    lines.extend(_b8_p9_table(rows, native_rows, eval_files))
    lines.extend(_policy_table(rows))
    lines.extend(
        [
            "## Artefatos e reprodutibilidade",
            "",
            "- Manifestos pequenos versionados: `docs/eval/manifests/v1.json`, "
            "`v2.json`, `v2.1.json` e `6a3_sample.json`.",
            "- Datasets grandes permanecem fora do Git (`data/synthetic/v1`, "
            "`v2`, `v2.1`).",
            "- Dumps: `data/synthetic/v2.1/eval/evidence_dump.jsonl` e "
            "`data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl`.",
            "- Commits de geração/avaliação estão nos manifestos.",
            "",
            "## Trade-offs e limitações",
            "",
            "- O aumento de extração veio de aliases de layout D e datas; o "
            "beneficiário continua sem correção dedicada.",
            "- OCR degradado perde B8 e parte de B1/B2/B4; a aritmética ainda "
            "detecta P9, mas o sinal forense de metadados desaparece na "
            "rasterização.",
            "- V4 e V5 são apenas simulações; nenhuma política foi ativada.",
            "- need_review é alto em OCR porque a amostra é pequena e a "
            "qualidade/ausência de campos impede conclusão segura.",
            "- B6/B7/P4 continuam fora da cobertura e são apresentados separados.",
            "- N por tipo é pequeno em várias células; a coluna Amostra marca "
            "indicativo quando N < 5.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native",
        default="../data/synthetic/v2.1/eval/evidence_dump.jsonl",
    )
    parser.add_argument(
        "--ocr",
        default="../data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl",
    )
    parser.add_argument(
        "--eval-files",
        default="../data/synthetic/v2.1/eval_ocr/files",
    )
    parser.add_argument("--out", default="docs/eval/6a5_report.md")
    args = parser.parse_args()
    native_rows = [
        row for row in _load(Path(args.native)) if row["path"] == "A_native"
    ]
    ocr_rows = [
        row for row in _load(Path(args.ocr)) if row["path"] != "A_native"
    ]
    report = build_report(native_rows, ocr_rows, Path(args.eval_files))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out} native={len(native_rows)} ocr={len(ocr_rows)}")


if __name__ == "__main__":
    main()
