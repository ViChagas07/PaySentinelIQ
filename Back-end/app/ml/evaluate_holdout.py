# mypy: ignore-errors
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    brier_score_loss,
)

from app.ml.dataset import Dataset, is_expert
from app.ml.features import FEATURE_NAMES, vectorize

PRIMARY_PATHS = ("A_native", "B_ocr_clean", "C_ocr_degraded")
FP_CAPS = {
    "A_native": 0.05,
    "B_ocr_clean": 0.10,
    "C_ocr_degraded": 0.15,
}
MIN_POSITIVES = 30
MIN_NEGATIVES = 30
NON_INFERIORITY_MARGIN = 0.05
DETERMINISTIC_THRESHOLD = 0.5
FUSION_THRESHOLD = 0.4


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_seal(
    seal: dict[str, Any],
    model_path: Path,
    dataset_manifest_path: Path,
) -> None:
    if seal.get("status") != "sealed":
        raise ValueError("holdout seal is not marked sealed")
    if _hash_file(model_path) != seal["artifact_sha256"]:
        raise ValueError("artifact hash does not match the seal")
    if (
        _hash_file(dataset_manifest_path)
        != seal["dataset_manifest_sha256"]
    ):
        raise ValueError("dataset manifest hash does not match the seal")
    feature_hash = hashlib.sha256(
        json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
    ).hexdigest()
    if feature_hash != seal["feature_names_sha256"]:
        raise ValueError("feature list hash does not match the seal")
    if seal["threshold"] != 0.809:
        raise ValueError("unexpected threshold in seal")


def _material_scores(dataset: Dataset) -> np.ndarray:
    index = dataset.feature_names.index("evidence_confirmed_material")
    critical = dataset.feature_names.index("evidence_confirmed_critical")
    return np.minimum(
        1.0,
        np.maximum(dataset.X[:, index], dataset.X[:, critical]),
    )


def _fusion_scores(dataset: Dataset) -> np.ndarray:
    return np.array([item["score"] / 100.0 for item in dataset.meta])


def _aggregate_ocr(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row["path"] == "A_native" or is_expert(row):
            continue
        key = (row["document_id"], row["path"])
        current = best.get(key)
        if current is None or row["score"] > current["score"]:
            best[key] = row
    return list(best.values())


def _dataset_from_rows(
    rows: list[dict[str, Any]],
    reference_date: date,
) -> Dataset:
    selected = [row for row in rows if not is_expert(row)]
    X = np.vstack(
        [vectorize(row, reference_date=reference_date) for row in selected]
    )
    y = np.array(
        [1 if row["is_fraud"] else 0 for row in selected],
        dtype=np.int8,
    )
    meta = [
        {
            "document_id": row["document_id"],
            "split": row.get("split"),
            "language": row.get("language"),
            "layout": row.get("layout"),
            "document_type": row.get("document_type"),
            "is_fraud": bool(row.get("is_fraud")),
            "sophistication": row.get("sophistication"),
            "tamper_types": list(row.get("tamper_types") or []),
            "path": row.get("path"),
            "score": float(row.get("score", 0.0)),
            "risk_level": row.get("risk_level"),
        }
        for row in selected
    ]
    return Dataset(X=X, y=y, meta=meta, feature_names=list(FEATURE_NAMES))


def _metrics(
    y: np.ndarray,
    scores: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    predictions = (scores >= threshold).astype(int)
    matrix = confusion_matrix(y, predictions, labels=[0, 1]).tolist()
    return {
        "n": int(len(y)),
        "positives": int(y.sum()),
        "negatives": int((1 - y).sum()),
        "tp": int(matrix[1][1]),
        "fn": int(matrix[1][0]),
        "fp": int(matrix[0][1]),
        "tn": int(matrix[0][0]),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "pr_auc": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "brier": float(brier_score_loss(y, np.clip(scores, 0, 1))),
        "predictions": predictions,
    }


def wilson_upper(successes: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return float("nan")
    p = successes / n
    denominator = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return float((centre + margin) / denominator)


def bootstrap_ci(
    y: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    iterations: int = 2000,
    seed: int = 2026,
) -> dict[str, list[float]]:
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {
        "precision": [],
        "recall": [],
        "f1": [],
        "pr_auc": [],
        "roc_auc": [],
    }
    n = len(y)
    for _ in range(iterations):
        index = rng.integers(0, n, n)
        yb, sb = y[index], scores[index]
        if len(np.unique(yb)) < 2:
            continue
        pred = (sb >= threshold).astype(int)
        values["precision"].append(
            precision_score(yb, pred, zero_division=0)
        )
        values["recall"].append(recall_score(yb, pred, zero_division=0))
        values["f1"].append(f1_score(yb, pred, zero_division=0))
        values["pr_auc"].append(average_precision_score(yb, sb))
        values["roc_auc"].append(roc_auc_score(yb, sb))
    return {
        name: [
            float(np.quantile(items, 0.025)),
            float(np.quantile(items, 0.975)),
        ]
        for name, items in values.items()
        if items
    }


def _group_metrics(
    dataset: Dataset,
    predictions: np.ndarray,
) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {
        "language": {},
        "layout": {},
        "document_type": {},
    }
    for dimension, key in (
        ("language", "language"),
        ("layout", "layout"),
        ("document_type", "document_type"),
    ):
        for item, prediction in zip(
            dataset.meta, predictions, strict=True
        ):
            group = str(item.get(key))
            bucket = result[dimension].setdefault(
                group,
                {"tp": 0, "fn": 0, "fp": 0, "tn": 0},
            )
            if item["is_fraud"]:
                bucket["tp" if prediction else "fn"] += 1
            else:
                bucket["fp" if prediction else "tn"] += 1
        for bucket in result[dimension].values():
            positives = bucket["tp"] + bucket["fn"]
            negatives = bucket["fp"] + bucket["tn"]
            bucket["recall"] = (
                bucket["tp"] / positives if positives else float("nan")
            )
            bucket["indicative"] = (
                positives < 10 or negatives < 10
            )
    return result


def _recall_category(
    dataset: Dataset,
    predictions: np.ndarray,
    category: str,
) -> tuple[int, int]:
    mask = np.array(
        [
            bool(item["is_fraud"])
            and item.get("sophistication") == category
            for item in dataset.meta
        ]
    )
    return int(predictions[mask].sum()), int(mask.sum())


def evaluate(
    native_rows: list[dict[str, Any]],
    ocr_rows: list[dict[str, Any]],
    model,
    reference_date: date,
    threshold: float,
) -> dict[str, Any]:
    native = _dataset_from_rows(
        [row for row in native_rows if row["path"] == "A_native"],
        reference_date,
    )
    cohorts = {"A_native": native}
    for path_name in ("B_ocr_clean", "C_ocr_degraded"):
        rows = [
            row
            for row in _aggregate_ocr(ocr_rows)
            if row["path"] == path_name
        ]
        cohorts[path_name] = _dataset_from_rows(rows, reference_date)

    results: dict[str, Any] = {}
    for path_name, dataset in cohorts.items():
        scores = model.predict_proba(dataset.X)[:, 1]
        deterministic = _metrics(
            dataset.y,
            _material_scores(dataset),
            DETERMINISTIC_THRESHOLD,
        )
        fusion = _metrics(
            dataset.y,
            _fusion_scores(dataset),
            FUSION_THRESHOLD,
        )
        logistic = _metrics(dataset.y, scores, threshold)
        naive_tp, naive_n = _recall_category(
            dataset, logistic["predictions"], "naive"
        )
        multi_tp, multi_n = _recall_category(
            dataset, logistic["predictions"], "multi"
        )
        det_naive_tp, _ = _recall_category(
            dataset, deterministic["predictions"], "naive"
        )
        det_multi_tp, _ = _recall_category(
            dataset, deterministic["predictions"], "multi"
        )
        fus_naive_tp, _ = _recall_category(
            dataset, fusion["predictions"], "naive"
        )
        fus_multi_tp, _ = _recall_category(
            dataset, fusion["predictions"], "multi"
        )
        fp_rate = logistic["fp"] / logistic["negatives"] if logistic["negatives"] else float("nan")
        results[path_name] = {
            "n": logistic["n"],
            "positives": logistic["positives"],
            "negatives": logistic["negatives"],
            "logistic": {
                key: value
                for key, value in logistic.items()
                if key != "predictions"
            },
            "deterministic": {
                key: value
                for key, value in deterministic.items()
                if key != "predictions"
            },
            "fusion": {
                key: value
                for key, value in fusion.items()
                if key != "predictions"
            },
            "naive": {
                "tp": naive_tp,
                "n": naive_n,
                "recall": naive_tp / naive_n if naive_n else float("nan"),
                "deterministic_recall": det_naive_tp / naive_n
                if naive_n
                else float("nan"),
                "fusion_recall": fus_naive_tp / naive_n
                if naive_n
                else float("nan"),
            },
            "multi": {
                "tp": multi_tp,
                "n": multi_n,
                "recall": multi_tp / multi_n if multi_n else float("nan"),
                "deterministic_recall": det_multi_tp / multi_n
                if multi_n
                else float("nan"),
                "fusion_recall": fus_multi_tp / multi_n
                if multi_n
                else float("nan"),
            },
            "fp_rate": fp_rate,
            "fp_wilson_upper": wilson_upper(
                logistic["fp"], logistic["negatives"]
            ),
            "ci": bootstrap_ci(dataset.y, scores, threshold),
            "groups": _group_metrics(
                dataset, logistic["predictions"]
            ),
        }

    criteria: dict[str, Any] = {}
    for path_name, result in results.items():
        checks: dict[str, bool] = {}
        reasons: list[str] = []
        enough = (
            result["positives"] >= MIN_POSITIVES
            and result["negatives"] >= MIN_NEGATIVES
        )
        if not enough:
            checks["sample_size"] = False
            reasons.append("N insuficiente: estrato inconclusivo")
        else:
            checks["sample_size"] = True
        for baseline in ("deterministic", "fusion"):
            base = result[baseline]
            checks[f"pr_auc_gt_{baseline}"] = (
                result["logistic"]["pr_auc"] > base["pr_auc"]
            )
            checks[f"f1_gt_{baseline}"] = (
                result["logistic"]["f1"] > base["f1"]
            )
            if not checks[f"pr_auc_gt_{baseline}"]:
                reasons.append(f"PR-AUC não supera {baseline}")
            if not checks[f"f1_gt_{baseline}"]:
                reasons.append(f"F1 não supera {baseline}")
        for category in ("naive", "multi"):
            values = result[category]
            if values["n"] == 0:
                checks[f"{category}_non_inferior"] = False
                reasons.append(f"{category}: sem amostra")
                continue
            checks[f"{category}_non_inferior"] = bool(
                values["recall"]
                >= values["deterministic_recall"] - NON_INFERIORITY_MARGIN
                and values["recall"]
                >= values["fusion_recall"] - NON_INFERIORITY_MARGIN
            )
            if not checks[f"{category}_non_inferior"]:
                reasons.append(f"{category}: margem de não inferioridade violada")
        checks["fp_cap"] = bool(
            result["fp_wilson_upper"] <= FP_CAPS[path_name]
        )
        if not checks["fp_cap"]:
            reasons.append("limite superior de FP acima do cap")
        criteria[path_name] = {
            "passed": all(checks.values()),
            "checks": checks,
            "reasons": reasons,
        }
    return {"cohorts": results, "criteria": criteria}


def build_report(result: dict[str, Any], seal: dict[str, Any]) -> str:
    lines = [
        "# Resultado do holdout — NÃO EXECUTADO NESTE CHECKPOINT",
        "",
        f"Artefato: `{seal['artifact_sha256']}`; threshold: {seal['threshold']}.",
        "",
        "| Path | N | Pos | Neg | PR-AUC | ROC-AUC | F1 | Recall | TP | FN | FP | TN | FP Wilson 95% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for path_name in PRIMARY_PATHS:
        item = result["cohorts"][path_name]
        logistic = item["logistic"]
        lines.append(
            f"| {path_name} | {item['n']} | {item['positives']} | "
            f"{item['negatives']} | {logistic['pr_auc']:.3f} | "
            f"{logistic['roc_auc']:.3f} | {logistic['f1']:.3f} | "
            f"{logistic['recall']:.3f} | {logistic['tp']} | "
            f"{logistic['fn']} | {logistic['fp']} | {logistic['tn']} | "
            f"{item['fp_wilson_upper']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Critérios",
            "",
            "| Path | Passou | Checks | Motivos |",
            "|---|---|---|---|",
        ]
    )
    for path_name in PRIMARY_PATHS:
        criterion = result["criteria"][path_name]
        checks = ", ".join(
            f"{name}={value}" for name, value in criterion["checks"].items()
        )
        lines.append(
            f"| {path_name} | {criterion['passed']} | {checks} | "
            f"{'; '.join(criterion['reasons'])} |"
        )
    lines.extend(
        [
            "",
            "## ICs bootstrap por linhagem/documento",
            "",
            "| Path | Métrica | IC 95% |",
            "|---|---|---|",
        ]
    )
    for path_name in PRIMARY_PATHS:
        for metric, interval in result["cohorts"][path_name]["ci"].items():
            lines.append(
                f"| {path_name} | {metric} | "
                f"[{interval[0]:.3f}; {interval[1]:.3f}] |"
            )
    lines.extend(
        [
            "",
            "## Grupos (N, TP/FN, FP/TN)",
            "",
            "| Path | Dimensão | Grupo | TP | FN | FP | TN | Recall | Indicativo |",
            "|---|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for path_name in PRIMARY_PATHS:
        for dimension, groups in result["cohorts"][path_name][
            "groups"
        ].items():
            for group, values in groups.items():
                lines.append(
                    f"| {path_name} | {dimension} | {group} | "
                    f"{values['tp']} | {values['fn']} | {values['fp']} | "
                    f"{values['tn']} | {values['recall']:.3f} | "
                    f"{values['indicative']} |"
                )
    lines.extend(
        [
            "",
            "O resultado não deve ser produzido antes do selo commitado. "
            "Qualquer falha encerra a promoção do candidato nesta rodada.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", required=True)
    parser.add_argument("--seal", default="../docs/eval/holdout_seal.json")
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", default="../docs/eval/holdout_result.md")
    args = parser.parse_args()
    seal = json.loads(Path(args.seal).read_text(encoding="utf-8"))
    model_path = Path(args.model)
    verify_seal(seal, model_path, Path(seal["dataset_manifest_path"]))
    rows = [
        json.loads(line)
        for line in Path(args.dump).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    reference_date = date.fromisoformat(seal["reference_date"])
    model = joblib.load(model_path)
    result = evaluate(
        [row for row in rows if row["path"] == "A_native"],
        [row for row in rows if row["path"] != "A_native"],
        model,
        reference_date,
        seal["threshold"],
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_report(result, seal), encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
