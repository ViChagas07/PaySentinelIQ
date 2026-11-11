import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.ml.features import FEATURE_NAMES
from app.ml.holdout_contract import (
    SCHEMA_PATH,
    SCHEMA_VERSION,
    SealValidationError,
    SealVerificationError,
    preflight_and_load,
    validate_seal,
    verify_commits,
    verify_seal,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seal(tmp_path: Path, *, artifact: Path, manifest: Path) -> dict:
    features_hash = hashlib.sha256(
        json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
    ).hexdigest()
    features_file = (
        Path(__file__).resolve().parents[2] / "app/ml/features.py"
    )
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
            "path": str(tmp_path),
            "version": "fixture",
            "reference_date": "2026-11-11",
            "seed": 1,
            "n_total": 1,
            "composition": {},
            "records_sha256": "0" * 64,
            "manifest_sha256": _hash(manifest),
            "files_sha256": "0" * 64,
            "lineage_hashes_sha256": "0" * 64,
            "intersection": {"old_ids": 0, "old_entities": 0},
        },
        "ocr": {
            "sample": 0,
            "primary": 0,
            "experts": 0,
            "variants": [],
        },
        "features": {
            "count": len(FEATURE_NAMES),
            "names_sha256": features_hash,
            "implementation_sha256": _hash(features_file),
        },
        "baselines": {
            "deterministic_threshold": 0.5,
            "fusion_threshold": 0.4,
            "logistic_threshold": 0.809,
            "evaluator_sha256": _hash(
                Path(__file__).resolve().parents[2]
                / "app/ml/evaluate_holdout.py"
            ),
        },
        "commits": {
            "generator": "deadbeef",
            "evaluator": "deadbeef",
            "protocol": "deadbeef",
            "extractor": "deadbeef",
            "model_code": "deadbeef",
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
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"frozen")
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    return _seal(tmp_path, artifact=artifact, manifest=manifest), artifact, manifest


def test_valid_canonical_seal_is_accepted_without_model_loading(tmp_path):
    seal, artifact, manifest = _fixture(tmp_path)
    called = {"loader": False}

    def loader(_path):
        called["loader"] = True
        return object()

    view, model = preflight_and_load(
        seal,
        artifact,
        manifest,
        loader=loader,
    )

    assert view["schema_version"] == SCHEMA_VERSION
    assert called["loader"] is True
    assert model is not None


def test_old_flat_schema_is_rejected_controlled():
    with pytest.raises(SealValidationError, match="schema_version"):
        validate_seal({"artifact_sha256": "0" * 64})


def test_missing_and_wrong_type_fields_are_rejected(tmp_path):
    seal, artifact, manifest = _fixture(tmp_path)
    missing = copy.deepcopy(seal)
    del missing["artifact"]["sha256"]
    with pytest.raises(SealValidationError, match="artifact.sha256"):
        validate_seal(missing)

    wrong = copy.deepcopy(seal)
    wrong["dataset"]["n_total"] = "1000"
    with pytest.raises(SealValidationError, match="dataset.n_total"):
        validate_seal(wrong)


def test_hash_and_threshold_divergences_are_rejected(tmp_path):
    seal, artifact, manifest = _fixture(tmp_path)
    artifact.write_bytes(b"changed")
    with pytest.raises(SealVerificationError, match="artefato"):
        verify_seal(seal, artifact, manifest)

    second = tmp_path / "second"
    second.mkdir()
    seal, artifact, manifest = _fixture(second)
    seal["artifact"]["threshold"] = 0.8
    with pytest.raises(SealVerificationError, match="threshold"):
        verify_seal(seal, artifact, manifest)


def test_commit_divergence_is_rejected_without_model(tmp_path):
    seal, _artifact, _manifest = _fixture(tmp_path)

    with pytest.raises(SealVerificationError, match="commit"):
        verify_commits(seal, repo_root=tmp_path)


def test_preflight_failure_never_calls_loader(tmp_path):
    seal, artifact, manifest = _fixture(tmp_path)
    seal["artifact"]["sha256"] = "0" * 64
    called = {"loader": False}

    def loader(_path):
        called["loader"] = True
        raise AssertionError("loader must not be called")

    with pytest.raises(SealVerificationError):
        preflight_and_load(
            seal,
            artifact,
            manifest,
            loader=loader,
        )
    assert called["loader"] is False
