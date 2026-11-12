import hashlib
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.evaluate_holdout import run_evaluation
from app.ml.features import FEATURE_NAMES
from app.ml.holdout_contract import SCHEMA_PATH, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[2]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _row(document_id, path, fraud, *, critical=False, score=0.0):
    evidence = []
    if critical:
        evidence.append(
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
        "split": "fixture",
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
        "evidences": evidence,
        "warnings": [],
        "errors": [],
    }


def _rows():
    rows = []
    for path_name in ("A_native", "B_ocr_clean", "C_ocr_degraded"):
        rows.append(
            _row(f"{path_name}-legit", path_name, False, score=0)
        )
        rows.append(
            _row(
                f"{path_name}-fraud",
                path_name,
                True,
                critical=True,
                score=80,
            )
        )
    return rows


def _seal(dataset_path: Path, artifact: Path, manifest: Path) -> dict:
    commit = _head()
    return {
        "schema_version": SCHEMA_VERSION,
        "schema_sha256": _hash(SCHEMA_PATH),
        "status": "sealed",
        "sealed_at": "2026-11-11T00:00:00+00:00",
        "artifact": {
            "path": str(artifact),
            "sha256": _hash(artifact),
            "threshold": 0.809,
            "model": "fixture",
            "C": 0.01,
        },
        "dataset": {
            "path": str(dataset_path),
            "version": "fixture",
            "reference_date": "2026-11-11",
            "seed": 1,
            "n_total": 6,
            "composition": {},
            "records_sha256": "0" * 64,
            "manifest_sha256": _hash(manifest),
            "files_sha256": "0" * 64,
            "lineage_hashes_sha256": "0" * 64,
            "intersection": {"old_ids": 0, "old_entities": 0},
        },
        "ocr": {"sample": 4, "primary": 4, "experts": 0, "variants": []},
        "features": {
            "count": len(FEATURE_NAMES),
            "names_sha256": hashlib.sha256(
                json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
            ).hexdigest(),
            "implementation_sha256": _hash(ROOT / "app/ml/features.py"),
        },
        "baselines": {
            "deterministic_threshold": 0.5,
            "fusion_threshold": 0.4,
            "logistic_threshold": 0.809,
            "evaluator_sha256": _hash(ROOT / "app/ml/evaluate_holdout.py"),
        },
        "commits": {
            "generator": commit,
            "evaluator": commit,
            "protocol": commit,
            "extractor": commit,
            "model_code": commit,
        },
        "environment": {
            "python": "3.11.9",
            "scikit_learn": "1.9.0",
            "numpy": "2.4.6",
            "pymupdf": "1.27.2.3",
            "pillow": "12.2.0",
            "joblib": "1.5.3",
        },
    }


def _fixture(tmp_path: Path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    manifest = dataset / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"fixture-model")
    dump = tmp_path / "dump.jsonl"
    dump.write_text(
        "\n".join(json.dumps(row) for row in _rows()) + "\n",
        encoding="utf-8",
    )
    seal = _seal(dataset, artifact, manifest)
    seal_path = tmp_path / "seal.json"
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    return seal, seal_path, artifact, dump


def test_run_evaluation_regression_v4_threshold_path(tmp_path):
    seal, seal_path, artifact, dump = _fixture(tmp_path)
    out = tmp_path / "result.md"
    json_out = tmp_path / "result.json"

    result = run_evaluation(
        dump,
        seal_path,
        artifact,
        out,
        json_out=json_out,
        loader=lambda _path: _ToyModel(),
    )

    assert result["threshold"] == 0.809
    assert out.exists() and json_out.exists()
    assert json.loads(json_out.read_text(encoding="utf-8"))["threshold"] == 0.809
    assert set(result["cohorts"]) == {
        "A_native",
        "B_ocr_clean",
        "C_ocr_degraded",
    }


class _ToyModel:
    def predict_proba(self, X):
        index = FEATURE_NAMES.index("evidence_confirmed_critical")
        scores = np.where(X[:, index] > 0, 0.95, 0.05)
        return np.column_stack([1 - scores, scores])


def test_real_cli_end_to_end_on_fixture(tmp_path):
    seal, seal_path, artifact, dump = _fixture(tmp_path)
    rng = np.random.default_rng(42)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=42),
    )
    model.fit(rng.normal(size=(20, len(FEATURE_NAMES))), [0, 1] * 10)
    model_path = tmp_path / "model.joblib"
    joblib.dump(model, model_path)
    seal["artifact"]["path"] = str(model_path)
    seal["artifact"]["sha256"] = _hash(model_path)
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    out = tmp_path / "cli_result.md"
    json_out = tmp_path / "cli_result.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.ml.evaluate_holdout",
            "--dump",
            str(dump),
            "--seal",
            str(seal_path),
            "--model",
            str(model_path),
            "--out",
            str(out),
            "--json-out",
            str(json_out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert out.exists() and json_out.exists()
    structured = json.loads(json_out.read_text(encoding="utf-8"))
    assert structured["threshold"] == 0.809
    for values in structured["cohorts"].values():
        logistic = values["logistic"]
        assert logistic["tp"] + logistic["fn"] == values["positives"]
        assert logistic["fp"] + logistic["tn"] == values["negatives"]


def test_no_direct_seal_dictionary_access_outside_contract():
    for path in (ROOT / "app/ml").glob("*.py"):
        if path.name == "holdout_contract.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert 'seal["' not in text
        assert "seal.get(" not in text
