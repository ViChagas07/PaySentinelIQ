# mypy: ignore-errors
from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.dataset import Dataset


def build_logistic(C: float = 1.0) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=C,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def build_isolation_forest() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                IsolationForest(
                    n_estimators=200,
                    contamination="auto",
                    random_state=42,
                ),
            ),
        ]
    )


def material_score(dataset: Dataset) -> np.ndarray:
    index = dataset.feature_names.index("evidence_confirmed_material")
    critical = dataset.feature_names.index("evidence_confirmed_critical")
    return np.minimum(
        1.0,
        np.maximum(dataset.X[:, index], dataset.X[:, critical]),
    )


def fusion_score(dataset: Dataset) -> np.ndarray:
    return np.array([item["score"] / 100.0 for item in dataset.meta])


def metrics(
    y: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    meta: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    predictions = (scores >= threshold).astype(int)
    result: dict[str, Any] = {
        "n": int(len(y)),
        "positives": int(y.sum()),
        "negatives": int((1 - y).sum()),
        "threshold": float(threshold),
        "pr_auc": _safe(average_precision_score, y, scores),
        "roc_auc": _safe(roc_auc_score, y, scores),
        "brier": _safe(brier_score_loss, y, np.clip(scores, 0.0, 1.0)),
        "precision_pos": _safe(precision_score, y, predictions, pos_label=1, zero_division=0),
        "recall_pos": _safe(recall_score, y, predictions, pos_label=1, zero_division=0),
        "f1_pos": _safe(f1_score, y, predictions, pos_label=1, zero_division=0),
        "precision_neg": _safe(precision_score, y, predictions, pos_label=0, zero_division=0),
        "recall_neg": _safe(recall_score, y, predictions, pos_label=0, zero_division=0),
        "f1_neg": _safe(f1_score, y, predictions, pos_label=0, zero_division=0),
        "predictions": predictions,
        "scores": scores,
    }
    matrix = confusion_matrix(y, predictions, labels=[0, 1]).tolist()
    result["confusion"] = matrix
    if meta is not None:
        result["fp_by_path"] = _fp_by_path(meta, predictions)
        result["recall_by_class"] = _recall_by_class(meta, predictions)
        result["by_group"] = _by_group(meta, predictions)
    return result


def _safe(function, *args, **kwargs) -> float:
    try:
        value = function(*args, **kwargs)
    except ValueError:
        return float("nan")
    if value is None:
        return float("nan")
    return float(value)


def _fp_by_path(
    meta: list[dict[str, Any]],
    predictions: np.ndarray,
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = defaultdict(
        lambda: {"legit": 0, "fp": 0, "fraud": 0, "detected": 0}
    )
    for item, prediction in zip(meta, predictions, strict=True):
        bucket = result[str(item.get("path"))]
        if item["is_fraud"]:
            bucket["fraud"] += 1
            bucket["detected"] += int(prediction)
        else:
            bucket["legit"] += 1
            bucket["fp"] += int(prediction)
    return dict(result)


def _recall_by_class(
    meta: list[dict[str, Any]],
    predictions: np.ndarray,
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "detected": 0}
    )
    for item, prediction in zip(meta, predictions, strict=True):
        if not item["is_fraud"]:
            continue
        label = str(item.get("sophistication") or "unknown")
        result[label]["total"] += 1
        result[label]["detected"] += int(prediction)
    return dict(result)


def _by_group(
    meta: list[dict[str, Any]],
    predictions: np.ndarray,
) -> dict[str, dict[str, dict[str, float]]]:
    groups: dict[str, dict[str, list[int]]] = {
        "language": defaultdict(lambda: [0, 0]),
        "layout": defaultdict(lambda: [0, 0]),
        "document_type": defaultdict(lambda: [0, 0]),
    }
    for item, prediction in zip(meta, predictions, strict=True):
        if item["is_fraud"]:
            for name, key in (
                ("language", item.get("language")),
                ("layout", item.get("layout")),
                ("document_type", item.get("document_type")),
            ):
                bucket = groups[name][str(key)]
                bucket[1] += 1
                bucket[0] += int(prediction)
    return {
        name: {
            key: {
                "detected": values[0],
                "total": values[1],
                "recall": values[0] / values[1] if values[1] else float("nan"),
            }
            for key, values in group.items()
        }
        for name, group in groups.items()
    }


def choose_threshold(y: np.ndarray, scores: np.ndarray) -> float:
    candidates = np.unique(np.round(scores, 4))
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in candidates:
        value = _safe(
            f1_score,
            y,
            (scores >= threshold).astype(int),
            pos_label=1,
            zero_division=0,
        )
        if value > best_f1:
            best_f1 = value
            best_threshold = float(threshold)
    return best_threshold


def choose_c(
    train: Dataset,
    val: Dataset,
) -> tuple[float, dict[float, float]]:
    scores: dict[float, float] = {}
    best_c = 1.0
    best_auc = -1.0
    for C in (0.01, 0.1, 1.0, 10.0):
        model = build_logistic(C=C)
        model.fit(train.X, train.y)
        score = model.predict_proba(val.X)[:, 1]
        auc = _safe(average_precision_score, val.y, score)
        scores[C] = auc
        if auc > best_auc:
            best_auc = auc
            best_c = C
    return best_c, scores


def calibration_table(
    y: np.ndarray,
    scores: np.ndarray,
    bins: int = 10,
) -> list[dict[str, float]]:
    if len(scores) == 0:
        return []
    order = np.argsort(scores)
    chunks = np.array_split(order, min(bins, len(order)))
    table = []
    for chunk in chunks:
        if len(chunk) == 0:
            continue
        table.append(
            {
                "n": float(len(chunk)),
                "predicted_mean": float(np.mean(scores[chunk])),
                "observed_rate": float(np.mean(y[chunk])),
            }
        )
    return table


def isolation_experiment(
    train: Dataset,
    val: Dataset,
    test_iid: Dataset,
    test_shift: Dataset,
    logistic_predictions: np.ndarray,
) -> dict[str, Any]:
    legitimate = train.X[train.y == 0]
    model = build_isolation_forest()
    model.fit(legitimate)
    result: dict[str, Any] = {
        "train_legit": int(len(legitimate)),
        "contamination": "auto",
        "random_state": 42,
    }
    for name, dataset in (
        ("val", val),
        ("test_iid", test_iid),
        ("test_shift", test_shift),
    ):
        scores = -model.score_samples(dataset.X)
        result[name] = {
            "n": int(len(dataset.y)),
            "positives": int(dataset.y.sum()),
            "roc_auc": _safe(roc_auc_score, dataset.y, scores),
            "pr_auc": _safe(average_precision_score, dataset.y, scores),
            "legit_mean": float(np.mean(scores[dataset.y == 0]))
            if (dataset.y == 0).any()
            else float("nan"),
            "fraud_mean": float(np.mean(scores[dataset.y == 1]))
            if (dataset.y == 1).any()
            else float("nan"),
        }
        if name == "val":
            threshold = float(np.quantile(scores[dataset.y == 0], 0.95))
            result["val_threshold_p95_legit"] = threshold
        else:
            threshold = float(result.get("val_threshold_p95_legit", 0.0))
            predictions = (scores >= threshold).astype(int)
            result[name]["recall_at_p95"] = _safe(
                recall_score, dataset.y, predictions, pos_label=1
            )
            result[name]["fp_rate_at_p95"] = float(
                np.mean(predictions[dataset.y == 0])
            ) if (dataset.y == 0).any() else float("nan")
            if name == "test_iid":
                missed = (dataset.y == 1) & (logistic_predictions == 0)
                if missed.any():
                    result[name]["logistic_missed"] = int(missed.sum())
                    result[name]["anomaly_flags_among_missed"] = int(
                        predictions[missed].sum()
                    )
    return result
