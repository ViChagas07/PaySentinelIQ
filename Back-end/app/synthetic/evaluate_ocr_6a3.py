# mypy: ignore-errors
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import tempfile
from typing import Any

import fitz

from app.services.ocr.native_text_provider import NativeTextFirstOCRProvider
from app.services.ocr.remote_provider import RemoteOCRProvider
from app.services.pipeline.canonical_pipeline import CanonicalPipeline
from app.services.pipeline.stages.crewai_stage import CrewAIStage
from app.synthetic.evaluate import (
    Observation,
    _ForbiddenOCRProvider,
    _evidence_dump,
    _instrument_stages,
    _native_observation,
    _ocr_observation,
    _to_document,
)
from app.synthetic.render import render_all

EVAL_SPLITS = ("test_iid", "test_shift")
LEGIT_PER_SPLIT = 20
SUFFICIENT_N = 5
TAMPERS = [f"B{index}" for index in range(1, 9)] + [
    f"P{index}" for index in range(1, 10)
]
EXPERTS = {"B6", "B7", "P4"}
CLEAN_VARIANTS = ("scanned_clean", "image_png")
DEGRADED_VARIANTS = ("scanned_rot", "scanned_blur")
DEFAULT_CREATOR = "PaySentinelIQ Synthetic Generator"


def _load_records(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _document_for_render(item: dict[str, Any]):
    document = _to_document(item)
    edit = item.get("pdf_edit")
    if edit and edit.get("before_text") and edit.get("after_text"):
        document.pdf_edit = edit
        before = str(edit["before_text"])
        after = str(edit["after_text"])
        document.original_lines = [
            line.replace(after, before) if after in line else line
            for line in document.lines
        ]
    return document


def select_sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fraud = [
        record
        for record in records
        if record["is_fraud"] and record["split"] in EVAL_SPLITS
    ]
    legitimate = []
    for split in EVAL_SPLITS:
        candidates = sorted(
            (
                record
                for record in records
                if not record["is_fraud"] and record["split"] == split
            ),
            key=lambda record: record["id"],
        )
        legitimate.extend(candidates[:LEGIT_PER_SPLIT])
    return sorted([*fraud, *legitimate], key=lambda record: record["id"])


def plan_lines(records: list[dict[str, Any]]) -> list[str]:
    sample = select_sample(records)
    by_split = Counter(record["split"] for record in sample)
    legit = sum(1 for record in sample if not record["is_fraud"])
    fraud = len(sample) - legit
    type_counts: Counter[str] = Counter()
    for record in sample:
        if record["is_fraud"]:
            type_counts.update(record["tamper_types"])
    lines = [
        "# 6A.3 — Plano de amostra (definido antes da execução)",
        "",
        "- Dataset: v2.1",
        f"- Splits de avaliação: {', '.join(EVAL_SPLITS)}",
        f"- Documentos: **{len(sample)}** ({fraud} adulterados, {legit} legítimos)",
        f"- Legítimos por split: até {LEGIT_PER_SPLIT} (ordenados por ID)",
        f"- Por split: {dict(by_split)}",
        "- Variantes OCR limpas: `scanned_clean`, `image_png`",
        "- Variantes OCR degradadas: `scanned_rot`, `scanned_blur`",
        f"- Suficiente para tabela: N >= {SUFFICIENT_N} documentos por tipo/path; "
        "abaixo disso é indicativo.",
        "",
        "| Tipo | N documentos |",
        "|---|---:|",
    ]
    for tamper in TAMPERS:
        lines.append(f"| {tamper} | {type_counts.get(tamper, 0)} |")
    lines.extend(
        [
            "",
            "Observação: as variantes de um mesmo documento permanecem no mesmo "
            "split. A agregação por path é feita por documento (detecção em "
            "qualquer variante do grupo), não por chamada OCR.",
            "",
        ]
    )
    return lines


def _detected(item: dict[str, Any]) -> bool:
    return bool(
        {evidence["code"] for evidence in item["evidences"]}
        & set(item["expected_codes_any_of"])
    )


def _forensic_signal(path: Path) -> bool:
    try:
        document = fitz.open(str(path))
        metadata = document.metadata or {}
        document.close()
    except Exception:
        return False
    creator = str(metadata.get("creator") or "")
    producer = str(metadata.get("producer") or "")
    return creator != DEFAULT_CREATOR or producer != DEFAULT_CREATOR


def _best_by_doc(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["document_id"], row["path"])
        current = best.get(key)
        if current is None or row["score"] > current["score"]:
            best[key] = row
    return best


def _rendered_from_disk(
    root: Path,
    sample: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, str]]]:
    rendered: dict[str, dict[str, dict[str, str]]] = {}
    base = root / "eval_ocr" / "files"
    suffixes = {
        "native": ".pdf",
        "scanned_clean": ".pdf",
        "scanned_rot": ".pdf",
        "scanned_blur": ".pdf",
        "image_png": ".png",
    }
    for record in sample:
        files: dict[str, dict[str, str]] = {}
        for variant, suffix in suffixes.items():
            path = base / variant / f"{record['id']}{suffix}"
            if path.exists():
                files[variant] = {"path": str(path)}
        rendered[record["id"]] = files
    return rendered


def _report(
    sample: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    rendered: dict[str, dict[str, dict[str, str]]],
) -> str:
    best = _best_by_doc(rows)
    paths = ("A_native", "B_ocr_clean", "C_ocr_degraded")
    type_counts: Counter[str] = Counter()
    for record in sample:
        if record["is_fraud"]:
            type_counts.update(record["tamper_types"])

    lines = [
        "# 6A.3 — Avaliação OCR ampliada",
        "",
        f"Dataset v2.1; N = **{len(sample)}** documentos "
        f"({sum(1 for r in sample if r['is_fraud'])} adulterados, "
        f"{sum(1 for r in sample if not r['is_fraud'])} legítimos).",
        f"Suficiente: N >= {SUFFICIENT_N} por tipo/path; caso contrário, indicativo.",
        "",
        "## Amostra por tipo",
        "",
        "| Tipo | N | Suficiente? |",
        "|---|---:|---|",
    ]
    for tamper in TAMPERS:
        count = type_counts.get(tamper, 0)
        lines.append(
            f"| {tamper} | {count} | {'sim' if count >= SUFFICIENT_N else 'indicativo'} |"
        )

    lines.extend(
        [
            "",
            "## Cobertura por path",
            "",
            "| Path | Documentos |",
            "|---|---:|",
        ]
    )
    for path_name in paths:
        lines.append(
            f"| {path_name} | "
            f"{sum(1 for key in best if key[1] == path_name)} |"
        )

    lines.extend(
        [
            "",
            "## Detecção por código (naive/multi; especialistas à parte)",
            "",
            "| Tipo | Path | N | Detectados | Cobertura | Amostra |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for tamper in TAMPERS:
        if tamper in EXPERTS:
            continue
        records = [
            record
            for record in sample
            if record["is_fraud"]
            and tamper in record["tamper_types"]
            and record["sophistication"] in {"naive", "multi"}
        ]
        for path_name in paths:
            selected = [
                best[(record["id"], path_name)]
                for record in records
                if (record["id"], path_name) in best
            ]
            hits = sum(_detected(observation) for observation in selected)
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | {hits} | "
                f"{(100 * hits / len(selected) if selected else 0):.1f}% | "
                f"{'suficiente' if len(selected) >= SUFFICIENT_N else 'indicativo'} |"
            )

    lines.extend(
        [
            "",
            "## Especialistas (seção separada)",
            "",
            "| Tipo | Path | N | Detectados | Cobertura |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for tamper in sorted(EXPERTS):
        records = [
            record
            for record in sample
            if record["is_fraud"] and tamper in record["tamper_types"]
        ]
        for path_name in paths:
            selected = [
                best[(record["id"], path_name)]
                for record in records
                if (record["id"], path_name) in best
            ]
            hits = sum(_detected(observation) for observation in selected)
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | {hits} | "
                f"{(100 * hits / len(selected) if selected else 0):.1f}% |"
            )

    lines.extend(
        [
            "",
            "## Falsos positivos em legítimos",
            "",
            "| Path | Legítimos | >= 70 | >= 40 |",
            "|---|---:|---:|---:|",
        ]
    )
    for path_name in paths:
        legitimate = [
            record
            for record in sample
            if not record["is_fraud"] and (record["id"], path_name) in best
        ]
        scores = [
            best[(record["id"], path_name)]["score"] for record in legitimate
        ]
        lines.append(
            f"| {path_name} | {len(scores)} | "
            f"{sum(score >= 70 for score in scores)} | "
            f"{sum(score >= 40 for score in scores)} |"
        )

    lines.extend(
        [
            "",
            "## B8 / P9 — aritmética vs. sinal forense",
            "",
            "| Tipo | Path | N | Código aritmético | Sinal forense |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for tamper in ("B8", "P9"):
        records = [
            record
            for record in sample
            if record["is_fraud"] and tamper in record["tamper_types"]
        ]
        for path_name in paths:
            selected = [
                best[(record["id"], path_name)]
                for record in records
                if (record["id"], path_name) in best
            ]
            arithmetic = sum(_detected(observation) for observation in selected)
            if path_name == "A_native":
                forensic = 0
                for record in records:
                    files = rendered.get(record["id"], {})
                    native = files.get("native")
                    if native and _forensic_signal(Path(native["path"])):
                        forensic += 1
            else:
                forensic = 0
            lines.append(
                f"| {tamper} | {path_name} | {len(selected)} | "
                f"{arithmetic} | {forensic} |"
            )
    lines.extend(
        [
            "",
            "Sinal forense = metadados `creator`/`producer` diferentes do gerador "
            "padrão no PDF nativo. OCR rasteriza o PDF e remove esse sinal; a "
            "ausência não prova autenticidade.",
            "",
            "## Limitações",
            "",
            "- N por tipo é pequeno em vários casos; a coluna `Amostra` separa "
            "suficiente de indicativo.",
            "- A agregação por path usa a melhor variante do documento, não "
            "multiplica variantes como observações independentes.",
            "- Nenhuma regra, extração, peso ou threshold foi alterado por esta "
            "avaliação.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../data/synthetic/v2.1")
    parser.add_argument("--report", default="docs/eval/6a3_ocr_expanded.md")
    parser.add_argument("--plan", default="docs/eval/6a3_sample_plan.md")
    parser.add_argument(
        "--dump",
        default="../data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl",
    )
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--refresh-native", action="store_true")
    parser.add_argument("--service-url", default="http://127.0.0.1:8010")
    args = parser.parse_args()

    root = Path(args.out)
    records = _load_records(root / "records.jsonl")
    sample = select_sample(records)
    plan_path = Path(args.plan)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("\n".join(plan_lines(records)), encoding="utf-8")
    print(f"plan={plan_path} sample={len(sample)}")
    if args.plan_only:
        return
    if args.refresh_native:
        base = root / "eval_ocr" / "files" / "native"
        for record in sample:
            document = _document_for_render(record)
            from app.synthetic.render import render_variant

            render_variant(
                document,
                "native",
                base / f"{record['id']}.pdf",
            )
        print(f"native refreshed={len(sample)}")
        return
    if args.report_only:
        dump_path = Path(args.dump)
        rows = [
            json.loads(line)
            for line in dump_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        rendered = _rendered_from_disk(root, sample)
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _report(sample, rows, rendered),
            encoding="utf-8",
        )
        print(f"report={report_path} rows={len(rows)}")
        return

    CrewAIStage._execute = lambda self, ctx: None
    pipeline = CanonicalPipeline()
    holder = _instrument_stages(pipeline)
    native_provider = NativeTextFirstOCRProvider(
        primary=_ForbiddenOCRProvider(),
        dpi=200,
        max_pages=10,
        min_native_chars=50,
    )
    provider = RemoteOCRProvider(
        url=args.service_url,
        timeout=120,
        engine="tesseract",
    )
    eval_root = root / "eval_ocr"
    rendered: dict[str, dict[str, dict[str, str]]] = {}
    observations: list[Observation] = []

    with tempfile.TemporaryDirectory(prefix="psi_6a3_native_") as temp:
        temp_dir = Path(temp)
        for index, item in enumerate(sample):
            document = _document_for_render(item)
            files = render_all(document, eval_root / "files")
            rendered[item["id"]] = files
            observations.append(
                asyncio.run(
                    _native_observation(
                        item,
                        pipeline,
                        native_provider,
                        temp_dir,
                        holder,
                    )
                )
            )
            for group, variants in (
                ("B_ocr_clean", CLEAN_VARIANTS),
                ("C_ocr_degraded", DEGRADED_VARIANTS),
            ):
                for variant in variants:
                    observations.append(
                        asyncio.run(
                            _ocr_observation(
                                item,
                                variant,
                                Path(files[variant]["path"]),
                                pipeline,
                                provider,
                                group,
                                holder,
                            )
                        )
                    )
            if index and index % 10 == 0:
                print(f"sample {index}/{len(sample)}")

    dump_path = Path(args.dump)
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with dump_path.open("w", encoding="utf-8", newline="\n") as handle:
        for observation in observations:
            row = _evidence_dump(observation)
            rows.append(row)
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = _report(sample, rows, rendered)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"report={report_path} dump={dump_path} observations={len(observations)}")


if __name__ == "__main__":
    main()
