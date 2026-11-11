# mypy: ignore-errors
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
from typing import Any

import joblib
from sklearn.dummy import DummyClassifier

from app.ml.dataset import Dataset, build_dataset, build_external_ocr_dataset
from app.ml.evaluate import (
    build_logistic,
    calibration_table,
    choose_c,
    choose_threshold,
    fusion_score,
    isolation_experiment,
    material_score,
    metrics,
)
from app.ml.features import FORBIDDEN_FEATURE_TOKENS, FEATURE_NAMES


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _fmt(value: float) -> str:
    if value != value:
        return "-"
    return f"{value:.3f}"


def _metrics_row(
    split: str,
    model_name: str,
    result: dict[str, Any],
) -> str:
    return (
        f"| {split} | {model_name} | {result['n']} | "
        f"{_fmt(result['pr_auc'])} | {_fmt(result['roc_auc'])} | "
        f"{_fmt(result['precision_pos'])}/{_fmt(result['recall_pos'])}/"
        f"{_fmt(result['f1_pos'])} | "
        f"{_fmt(result['precision_neg'])}/{_fmt(result['recall_neg'])}/"
        f"{_fmt(result['f1_neg'])} | {_fmt(result['brier'])} | "
        f"{result['threshold']:.3f} |"
    )


def _baseline_results(
    train: Dataset,
    datasets: dict[str, Dataset],
    logistic_model,
    logistic_threshold: float,
) -> dict[str, dict[str, dict[str, Any]]]:
    dummy = DummyClassifier(strategy="prior", random_state=42)
    dummy.fit(train.X, train.y)
    results: dict[str, dict[str, dict[str, Any]]] = {}
    for split, dataset in datasets.items():
        dummy_scores = dummy.predict_proba(dataset.X)[:, 1]
        det_scores = material_score(dataset)
        fusion = fusion_score(dataset)
        logistic_scores = logistic_model.predict_proba(dataset.X)[:, 1]
        results[split] = {
            "Dummy": metrics(dataset.y, dummy_scores, 0.5, dataset.meta),
            "Deterministic": metrics(
                dataset.y, det_scores, 0.5, dataset.meta
            ),
            "Fusion": metrics(dataset.y, fusion, 0.4, dataset.meta),
            "Logistic": metrics(
                dataset.y, logistic_scores, logistic_threshold, dataset.meta
            ),
        }
        results[split]["Logistic"]["scores"] = logistic_scores
        results[split]["Deterministic"]["scores"] = det_scores
        results[split]["Fusion"]["scores"] = fusion
        results[split]["Dummy"]["scores"] = dummy_scores
    return results


def _fp_table(
    results: dict[str, dict[str, dict[str, Any]]],
    splits: tuple[str, ...],
) -> list[str]:
    lines = [
        "### Falsos positivos por caminho",
        "",
        "| Split | Modelo | Path | Legítimos | FP | Fraudes | Detectadas |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for split in splits:
        for model_name, result in results[split].items():
            for path_name, values in sorted(
                result.get("fp_by_path", {}).items()
            ):
                lines.append(
                    f"| {split} | {model_name} | {path_name} | "
                    f"{values['legit']} | {values['fp']} | "
                    f"{values['fraud']} | {values['detected']} |"
                )
    lines.append("")
    return lines


def _recall_table(
    results: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    lines = [
        "### Recall por classe",
        "",
        "| Split | Modelo | Classe | Detectadas | N | Recall |",
        "|---|---|---|---:|---:|---:|",
    ]
    for split in ("test_iid", "test_shift"):
        for model_name in ("Deterministic", "Fusion", "Logistic"):
            for label, values in sorted(
                results[split][model_name].get("recall_by_class", {}).items()
            ):
                lines.append(
                    f"| {split} | {model_name} | {label} | "
                    f"{values['detected']} | {values['total']} | "
                    f"{_fmt(values['detected'] / values['total'] if values['total'] else float('nan'))} |"
                )
    lines.append("")
    return lines


def _group_table(
    results: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    lines = [
        "### Logistic — recall por idioma, layout e tipo",
        "",
        "| Split | Dimensão | Grupo | Detectadas | N | Recall |",
        "|---|---|---|---:|---:|---:|",
    ]
    for split in ("test_iid", "test_shift"):
        for dimension, groups in results[split]["Logistic"].get(
            "by_group", {}
        ).items():
            for group, values in sorted(groups.items()):
                lines.append(
                    f"| {split} | {dimension} | {group} | "
                    f"{values['detected']:.0f} | {values['total']:.0f} | "
                    f"{_fmt(values['recall'])} |"
                )
    lines.append("")
    return lines


def _external_ocr_report(
    model,
    threshold: float,
    ocr: Dataset,
) -> tuple[list[str], dict[str, Any]]:
    lines = [
        "## Avaliação externa OCR (modelo treinado só em native)",
        "",
        "| Path | Modelo | N | Positivos | PR-AUC | ROC-AUC | Recall naive+multi | FP legítimos |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    summary: dict[str, Any] = {}
    for path_name in ("B_ocr_clean", "C_ocr_degraded"):
        indices = [
            index
            for index, item in enumerate(ocr.meta)
            if item["path"] == path_name
        ]
        subset = Dataset(
            X=ocr.X[indices],
            y=ocr.y[indices],
            meta=[ocr.meta[index] for index in indices],
            feature_names=ocr.feature_names,
        )
        scores = model.predict_proba(subset.X)[:, 1]
        result = metrics(subset.y, scores, threshold, subset.meta)
        det_scores = material_score(subset)
        det_result = metrics(subset.y, det_scores, 0.5, subset.meta)
        fusion_result = metrics(
            subset.y, fusion_score(subset), 0.4, subset.meta
        )
        summary[path_name] = {
            "logistic": {
                key: result[key]
                for key in result
                if key not in {"scores", "predictions"}
            },
            "deterministic": {
                key: det_result[key]
                for key in det_result
                if key not in {"scores", "predictions"}
            },
            "fusion": {
                key: fusion_result[key]
                for key in fusion_result
                if key not in {"scores", "predictions"}
            },
        }
        for name, value in (
            ("Logistic", result),
            ("Deterministic", det_result),
            ("Fusion", fusion_result),
        ):
            recall_class = value.get("recall_by_class", {})
            naive_multi = recall_class.get("naive", {"detected": 0, "total": 0})
            naive_multi_total = naive_multi["total"] + recall_class.get(
                "multi", {"total": 0}
            )["total"]
            naive_multi_detected = naive_multi["detected"] + recall_class.get(
                "multi", {"detected": 0}
            )["detected"]
            lines.append(
                f"| {path_name} | {name} | {value['n']} | {value['positives']} | "
                f"{_fmt(value['pr_auc'])} | {_fmt(value['roc_auc'])} | "
                f"{_fmt(naive_multi_detected / naive_multi_total if naive_multi_total else float('nan'))} | "
                f"{value['fp_by_path'].get(path_name, {}).get('fp', 0)} |"
            )
    lines.append("")
    return lines, summary


def build_report(
    native: Dataset,
    ocr: Dataset,
    results: dict[str, dict[str, dict[str, Any]]],
    c_scores: dict[float, float],
    chosen_c: float,
    threshold: float,
    calibration: list[dict[str, float]],
    isolation: dict[str, Any],
    external_lines: list[str],
    external_summary: dict[str, Any],
) -> str:
    counts = {
        split: (
            int((native.split(split).y == 0).sum()),
            int((native.split(split).y == 1).sum()),
        )
        for split in ("train", "val", "test_iid", "test_shift")
    }
    lines = [
        "# 6B — Baseline de scikit-learn (offline e shadow)",
        "",
        "Nenhum modelo foi integrado ao CanonicalPipeline, à API ou ao "
        "FusionEngine. O experimento é offline e shadow.",
        "",
        f"Dataset: v2.1 native; features={len(FEATURE_NAMES)}; "
        f"scikit-learn={__import__('sklearn').__version__}.",
        "",
        "## Dataset e rótulo",
        "",
        "- Positivos: naive/multi (B1-B5, B8, P1-P3, P5-P9).",
        "- Negativos: legítimos.",
        "- B6/B7/P4 excluídos do treino e da avaliação principal; avaliados "
        "separadamente em 6A.5.",
        "- N por split (legítimos/adulterados): "
        + ", ".join(
            f"{split}={counts[split][0]}/{counts[split][1]}"
            for split in ("train", "val", "test_iid", "test_shift")
        ),
        "- Variantes de um mesmo documento permanecem no mesmo split; o "
        "treino inicial usa somente native.",
        "",
        "## Seleção de modelo",
        "",
        "| C | Val PR-AUC |",
        "|---|---:|",
        *[f"| {C} | {_fmt(value)} |" for C, value in c_scores.items()],
        f"\nC escolhido: **{chosen_c}**; threshold escolhido na validação: "
        f"**{threshold:.3f}**.",
        "",
        "## Métricas por split",
        "",
        "| Split | Modelo | N | PR-AUC | ROC-AUC | Pos P/R/F1 | Neg P/R/F1 | Brier | Threshold |",
        "|---|---|---:|---:|---:|---|---|---:|---:|",
    ]
    for split in ("val", "test_iid", "test_shift"):
        for model_name in ("Dummy", "Deterministic", "Fusion", "Logistic"):
            lines.append(
                _metrics_row(split, model_name, results[split][model_name])
            )
    lines.extend(["", "## Detalhamento"])
    lines.extend(_fp_table(results, ("val", "test_iid", "test_shift")))
    lines.extend(_recall_table(results))
    lines.extend(_group_table(results))
    lines.extend(external_lines)
    lines.extend(
        [
            "## Calibração do Logistic (test_iid)",
            "",
            "| Bin | N | Probabilidade média | Taxa observada |",
            "|---|---:|---:|---:|",
            *[
                f"| {index + 1} | {row['n']:.0f} | "
                f"{row['predicted_mean']:.3f} | {row['observed_rate']:.3f} |"
                for index, row in enumerate(calibration)
            ],
            "",
            "## IsolationForest (experimento separado)",
            "",
            "- Treinado somente com legítimos de train; `contamination='auto'`; "
            "não é probabilidade de fraude.",
            f"- ROC-AUC test_iid: {_fmt(isolation['test_iid']['roc_auc'])}; "
            f"test_shift: {_fmt(isolation['test_shift']['roc_auc'])}.",
            f"- PR-AUC test_iid: {_fmt(isolation['test_iid']['pr_auc'])}; "
            f"test_shift: {_fmt(isolation['test_shift']['pr_auc'])}.",
            f"- Threshold p95 em legítimos de val: "
            f"{isolation['val_threshold_p95_legit']:.3f}.",
            f"- Recall no threshold p95: test_iid "
            f"{_fmt(isolation['test_iid'].get('recall_at_p95', float('nan')))}; "
            f"test_shift "
            f"{_fmt(isolation['test_shift'].get('recall_at_p95', float('nan')))}.",
            f"- Fraudes perdidas pelo Logistic e flagradas pela anomalia em "
            f"test_iid: {isolation['test_iid'].get('anomaly_flags_among_missed', 0)}"
            f"/{isolation['test_iid'].get('logistic_missed', 0)}.",
            "",
            "Conclusão: a anomalia não é usada para decisão; o resultado indica "
            "se acrescenta sinal além das regras/classificação.",
            "",
            "## Features e vazamento",
            "",
            f"- {len(FEATURE_NAMES)} features numéricas, listadas no manifesto.",
            "- Nenhum campo de `tamper_types`, `sophistication`, `intended_band`, "
            "`gabarito`, `seed`, `document_id`, texto bruto, nome ou empresa.",
            "- Imputação e escala dentro do Pipeline, ajustadas somente em train.",
            "- Testes de reprodutibilidade, ausência de vazamento, inferência com "
            "feature ausente/desconhecida e ausência de chamadas a LLM/rede.",
            "",
            "## Trade-offs e limitações",
            "",
            "- O conjunto é de desenvolvimento/avaliação; `test_iid`/`test_shift` "
            "não são holdout intocado.",
            "- O modelo é treinado somente em native; a avaliação OCR é domínio "
            "externo e tem N pequeno.",
            "- Probabilidades não são convertidas automaticamente em "
            "LOW/MEDIUM/HIGH.",
            "- B6/B7/P4 estão fora da cobertura e não entram no treino.",
            "- Se o ganho sobre as baselines não for consistente, o modelo não "
            "deve ser integrado.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dump",
        default="../data/synthetic/v2.1/eval/evidence_dump.jsonl",
    )
    parser.add_argument(
        "--ocr-dump",
        default="../data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl",
    )
    parser.add_argument(
        "--dataset-manifest",
        default="../data/synthetic/v2.1/manifest.json",
    )
    parser.add_argument(
        "--model",
        default="../data/ml/logistic_v2_1.joblib",
    )
    parser.add_argument(
        "--manifest",
        default="docs/eval/ml_manifest.json",
    )
    parser.add_argument(
        "--report",
        default="docs/eval/ml_baseline.md",
    )
    args = parser.parse_args()

    dataset_manifest = json.loads(
        Path(args.dataset_manifest).read_text(encoding="utf-8")
    )
    reference_date = date.fromisoformat(dataset_manifest["generated_on"])
    native = build_dataset(args.dump, reference_date=reference_date)
    train = native.split("train")
    val = native.split("val")
    test_iid = native.split("test_iid")
    test_shift = native.split("test_shift")
    ocr = build_external_ocr_dataset(
        args.ocr_dump,
        reference_date=reference_date,
    )

    chosen_c, c_scores = choose_c(train, val)
    model = build_logistic(C=chosen_c)
    model.fit(train.X, train.y)
    val_scores = model.predict_proba(val.X)[:, 1]
    threshold = choose_threshold(val.y, val_scores)
    datasets = {
        "train": train,
        "val": val,
        "test_iid": test_iid,
        "test_shift": test_shift,
    }
    results = _baseline_results(train, datasets, model, threshold)
    logistic_test_scores = results["test_iid"]["Logistic"]["scores"]
    predictions = (logistic_test_scores >= threshold).astype(int)
    isolation = isolation_experiment(
        train, val, test_iid, test_shift, predictions
    )
    calibration = calibration_table(
        test_iid.y,
        logistic_test_scores,
    )
    external_lines, external_summary = _external_ocr_report(
        model, threshold, ocr
    )

    report = build_report(
        native,
        ocr,
        results,
        c_scores,
        chosen_c,
        threshold,
        calibration,
        isolation,
        external_lines,
        external_summary,
    )

    model_path = Path(args.model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    manifest = {
        "phase": "6B",
        "dataset_version": dataset_manifest["dataset_version"],
        "dataset_records_sha256": dataset_manifest["records_sha256"],
        "code_commit": _git_commit(),
        "sklearn_version": __import__("sklearn").__version__,
        "feature_names": list(FEATURE_NAMES),
        "feature_types": ["float64"] * len(FEATURE_NAMES),
        "forbidden_tokens_absent": [
            token
            for token in FORBIDDEN_FEATURE_TOKENS
            if not any(token in name for name in FEATURE_NAMES)
        ],
        "model": "LogisticRegression",
        "model_params": {
            "C": chosen_c,
            "class_weight": "balanced",
            "max_iter": 2000,
            "random_state": 42,
            "preprocessing": ["SimpleImputer(median)", "StandardScaler"],
        },
        "calibration": "none (raw logistic probabilities)",
        "decision_threshold": threshold,
        "trained_on": "train native only",
        "trained_at": date.today().isoformat(),
        "metrics": {
            split: {
                name: {
                    key: value
                    for key, value in result.items()
                    if key not in {"predictions", "scores"}
                }
                for name, result in split_results.items()
            }
            for split, split_results in results.items()
        },
        "external_ocr": external_summary,
        "isolation_forest": isolation,
        "model_path": str(model_path),
        "policy": "evaluation only; not connected to API or FusionEngine",
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    sidecar = model_path.with_suffix(".manifest.json")
    sidecar.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"model={model_path} manifest={manifest_path} report={report_path} "
        f"C={chosen_c} threshold={threshold:.3f}"
    )


if __name__ == "__main__":
    main()
