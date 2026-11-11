from types import SimpleNamespace

import numpy as np

from app.ml.evaluate_holdout import evaluate, wilson_upper
from app.ml.features import FEATURE_NAMES


def _config():
    return SimpleNamespace(
        reference_date="2026-11-11",
        artifact_threshold=0.809,
        deterministic_threshold=0.5,
        fusion_threshold=0.4,
    )


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

    result = evaluate(rows, ocr_rows, ToyModel(), _config())

    assert result["criteria"]["A_native"]["checks"]["sample_size"] is False
    assert result["criteria"]["A_native"]["passed"] is False
    for path_name in ("A_native", "B_ocr_clean", "C_ocr_degraded"):
        cohort = result["cohorts"][path_name]
        logistic = cohort["logistic"]
        assert logistic["tp"] + logistic["fn"] == cohort["positives"]
        assert logistic["fp"] + logistic["tn"] == cohort["negatives"]


def test_wilson_upper_for_zero_events():
    value = wilson_upper(0, 178)

    assert 0 < value < 0.05
