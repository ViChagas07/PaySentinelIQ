import hashlib
import json

import joblib
import numpy as np
import pytest

from app.ml.evaluate_holdout import (
    evaluate,
    verify_seal,
    wilson_upper,
)
from app.ml.features import FEATURE_NAMES


class ToyModel:
    def predict_proba(self, X):
        index = FEATURE_NAMES.index("evidence_confirmed_critical")
        scores = np.where(X[:, index] > 0, 0.95, 0.05)
        return np.column_stack([1 - scores, scores])


def _row(document_id, path, fraud, *, critical=False, score=0.0):
    evidences = []
    if critical:
        evidences.append(
            {
                "code": "BOLETO_AMOUNT_MISMATCH",
                "severity": "critical",
                "source": "deterministic",
                "confidence": 1.0,
                "metadata": {},
            }
        )
    return {
        "document_id": document_id,
        "path": path,
        "split": "holdout",
        "language": "pt",
        "layout": "A",
        "document_type": "boleto",
        "is_fraud": fraud,
        "sophistication": "naive" if fraud else None,
        "tamper_types": ["B1"] if fraud else [],
        "expected_codes_any_of": ["BOLETO_AMOUNT_MISMATCH"],
        "score": score,
        "risk_level": "HIGH" if score >= 70 else "LOW",
        "extracted_fields": {
            "linha_digitavel": "0019" + "0" * 43,
            "valor_nominal": 100.0,
            "data_vencimento": "20/01/2027",
            "codigo_banco": "001",
        },
        "evidences": evidences,
        "warnings": [],
        "errors": [],
    }


def test_small_stratum_is_inconclusive():
    rows = [
        _row("a", "A_native", False, score=0),
        _row("b", "A_native", True, critical=True, score=80),
    ]
    ocr_rows = [
        _row("c", "B_ocr_clean", False, score=0),
        _row("d", "B_ocr_clean", True, critical=True, score=80),
        _row("e", "C_ocr_degraded", False, score=0),
        _row("f", "C_ocr_degraded", True, critical=True, score=80),
    ]

    result = evaluate(
        rows,
        ocr_rows,
        ToyModel(),
        __import__("datetime").date(2026, 11, 11),
        0.809,
    )

    assert result["criteria"]["A_native"]["checks"]["sample_size"] is False
    assert result["criteria"]["A_native"]["passed"] is False


def test_wilson_upper_for_zero_events():
    value = wilson_upper(0, 178)

    assert 0 < value < 0.05


def test_verify_seal_rejects_artifact_mismatch(tmp_path):
    model_path = tmp_path / "model.joblib"
    joblib.dump(ToyModel(), model_path)
    dataset_manifest = tmp_path / "manifest.json"
    dataset_manifest.write_text("{}", encoding="utf-8")
    seal = {
        "status": "sealed",
        "artifact_sha256": "0" * 64,
        "dataset_manifest_sha256": hashlib.sha256(
            dataset_manifest.read_bytes()
        ).hexdigest(),
        "feature_names_sha256": hashlib.sha256(
            json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
        ).hexdigest(),
        "threshold": 0.809,
    }

    with pytest.raises(ValueError, match="artifact hash"):
        verify_seal(seal, model_path, dataset_manifest)
