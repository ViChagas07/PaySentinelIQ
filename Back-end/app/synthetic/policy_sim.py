from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

SEVERITY_WEIGHTS: dict[str, float] = {
    "critical": 35.0,
    "high": 20.0,
    "medium": 10.0,
    "low": 5.0,
    "info": 2.0,
}

SOURCE_MULTIPLIERS: dict[str, float] = {
    "deterministic": 1.5,
    "knowledge_base": 1.3,
    "brasilapi": 1.3,
    "ocr": 1.2,
    "heuristic": 1.0,
    "crewai": 0.9,
    "user": 0.8,
}

VARIANTS = ("V0", "V1", "V2", "V3")


def _weights(variant: str) -> dict[str, float]:
    weights = dict(SEVERITY_WEIGHTS)
    if variant == "V2":
        weights["high"] = 30.0
    return weights


def simulate_score(
    evidences: list[dict[str, Any]],
    variant: str = "V0",
) -> float:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant: {variant}")

    selected = evidences
    if variant == "V3":
        selected = [
            evidence
            for evidence in evidences
            if str(evidence.get("severity", "info")) not in {"info", "low"}
        ]
    if not selected:
        return 0.0

    weights = _weights(variant)
    raw_score = 0.0
    critical_count = 0
    for evidence in selected:
        severity = str(evidence.get("severity", "info"))
        source = str(evidence.get("source", "heuristic"))
        confidence = float(evidence.get("confidence", 1.0))
        contribution = round(
            weights.get(severity, 2.0)
            * SOURCE_MULTIPLIERS.get(source, 1.0)
            * confidence,
            2,
        )
        raw_score += contribution
        if severity == "critical":
            critical_count += 1

    if critical_count >= 1:
        raw_score = max(raw_score, 70.0)
    if critical_count >= 3:
        raw_score = max(raw_score, 90.0)
    if critical_count >= 2:
        raw_score = min(raw_score * 1.2, 100.0)

    return round(min(raw_score, 100.0), 1)


def classify(score: float, variant: str = "V0") -> str:
    medium_threshold = 25.0 if variant == "V1" else 40.0
    if score >= 70.0:
        return "HIGH"
    if score >= medium_threshold:
        return "MEDIUM"
    return "LOW"


def _rate(hits: int, total: int) -> str:
    return f"{hits}/{total} ({100 * hits / total:.1f}%)" if total else "0/0"


def _load(dump_path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in dump_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _summary(dump: list[dict[str, Any]]) -> list[str]:
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in dump:
        by_path[item["path"]].append(item)

    lines = [
        "## Simulação de política (somente leitura)",
        "",
        "| Variante | Caminho | Legítimos >= 70 | Legítimos >= 40 | "
        "Recall naive >= 40 | Recall naive >= 70 | Recall multi >= 40 | "
        "Recall multi >= 70 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    confusion: dict[tuple[str, str, str, str], int] = Counter()
    for variant in VARIANTS:
        for path_name in sorted(by_path):
            items = by_path[path_name]
            legit = [item for item in items if not item["is_fraud"]]
            naive = [
                item
                for item in items
                if item["is_fraud"]
                and item["sophistication"] in {"naive", "multi"}
            ]
            multi = [
                item
                for item in items
                if item["is_fraud"] and item["sophistication"] == "multi"
            ]
            legit_scores = [
                simulate_score(item["evidences"], variant) for item in legit
            ]
            naive_scores = [
                simulate_score(item["evidences"], variant) for item in naive
            ]
            multi_scores = [
                simulate_score(item["evidences"], variant) for item in multi
            ]
            lines.append(
                f"| {variant} | {path_name} | "
                f"{_rate(sum(score >= 70 for score in legit_scores), len(legit))} | "
                f"{_rate(sum(score >= 40 for score in legit_scores), len(legit))} | "
                f"{_rate(sum(score >= 40 for score in naive_scores), len(naive))} | "
                f"{_rate(sum(score >= 70 for score in naive_scores), len(naive))} | "
                f"{_rate(sum(score >= 40 for score in multi_scores), len(multi))} | "
                f"{_rate(sum(score >= 70 for score in multi_scores), len(multi))} |"
            )
            for item in items:
                if not item["is_fraud"]:
                    continue
                score = simulate_score(item["evidences"], variant)
                confusion[
                    (variant, item["path"], item["intended_band"], classify(score, variant))
                ] += 1

    lines.extend(
        [
            "",
            "## Matriz de confusão por variante",
            "",
            "| Variante | Caminho | Intenção | LOW | MEDIUM | HIGH |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for variant in VARIANTS:
        paths = sorted({key[1] for key in confusion if key[0] == variant})
        for path_name in paths:
            for intended in ("LOW", "MEDIUM", "HIGH"):
                lines.append(
                    f"| {variant} | {path_name} | {intended} | "
                    f"{confusion.get((variant, path_name, intended, 'LOW'), 0)} | "
                    f"{confusion.get((variant, path_name, intended, 'MEDIUM'), 0)} | "
                    f"{confusion.get((variant, path_name, intended, 'HIGH'), 0)} |"
                )
    lines.append("")
    return lines


def build_report(dump_path: Path, title: str) -> str:
    dump = _load(dump_path)
    lines = [
        f"# {title}",
        "",
        "Recalcula o score fusionado a partir do `evidence_dump` com a fórmula do "
        "FusionEngine: peso da severidade × multiplicador da fonte × confiança, "
        "pisos de 1 e 3 críticos, fator 1,2 para 2+ críticos e limite 100.",
        "",
    ]
    lines.extend(_summary(dump))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--title",
        default="Simulação de política — variantes sobre o dump",
    )
    args = parser.parse_args()
    report = build_report(Path(args.dump), args.title)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
