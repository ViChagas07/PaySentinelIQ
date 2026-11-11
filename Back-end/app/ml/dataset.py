from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.ml.features import FEATURE_NAMES, vectorize

EXPERTS = {"B6", "B7", "P4"}
SPLITS = ("train", "val", "test_iid", "test_shift")


@dataclass
class Dataset:
    X: np.ndarray
    y: np.ndarray
    meta: list[dict[str, Any]]
    feature_names: list[str]

    def split(self, name: str) -> "Dataset":
        indices = [
            index for index, item in enumerate(self.meta) if item["split"] == name
        ]
        return Dataset(
            X=self.X[indices],
            y=self.y[indices],
            meta=[self.meta[index] for index in indices],
            feature_names=self.feature_names,
        )


def load_rows(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def is_expert(row: dict[str, Any]) -> bool:
    return bool(set(row.get("tamper_types") or []) & EXPERTS)


def label_for(row: dict[str, Any]) -> int | None:
    if is_expert(row):
        return None
    return 1 if row.get("is_fraud") else 0


def build_dataset(
    dump_path: str | Path,
    *,
    path_names: tuple[str, ...] = ("A_native",),
    reference_date: date | None = None,
) -> Dataset:
    rows = [
        row
        for row in load_rows(dump_path)
        if row.get("path") in path_names and not is_expert(row)
    ]
    X = np.vstack(
        [vectorize(row, reference_date=reference_date) for row in rows]
    )
    y = np.array([label_for(row) for row in rows], dtype=np.int8)
    meta = [
        {
            "document_id": row["document_id"],
            "split": row["split"],
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
        for row in rows
    ]
    assert_no_document_leakage(meta)
    return Dataset(X=X, y=y, meta=meta, feature_names=list(FEATURE_NAMES))


def build_external_ocr_dataset(
    dump_path: str | Path,
    *,
    reference_date: date | None = None,
) -> Dataset:
    rows = [row for row in load_rows(dump_path) if row.get("path") != "A_native"]
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if is_expert(row):
            continue
        key = (row["document_id"], row["path"])
        current = best.get(key)
        if current is None or float(row.get("score", 0.0)) > float(
            current.get("score", 0.0)
        ):
            best[key] = row
    selected = list(best.values())
    X = np.vstack(
        [vectorize(row, reference_date=reference_date) for row in selected]
    )
    y = np.array([label_for(row) for row in selected], dtype=np.int8)
    meta = [
        {
            "document_id": row["document_id"],
            "split": row["split"],
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


def assert_no_document_leakage(meta: list[dict[str, Any]]) -> None:
    by_split: dict[str, set[str]] = {split: set() for split in SPLITS}
    for item in meta:
        by_split.setdefault(item["split"], set()).add(item["document_id"])
    splits = list(by_split)
    for index, first in enumerate(splits):
        for second in splits[index + 1 :]:
            overlap = by_split[first] & by_split[second]
            if overlap:
                raise AssertionError(
                    f"Document leakage between {first} and {second}: "
                    f"{sorted(overlap)[:5]}"
                )
