from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess
from typing import Any, Callable

SCHEMA_VERSION = "holdout-seal/2.0"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "eval"
    / "holdout_seal.schema.json"
)
HEX64 = 64


class SealValidationError(ValueError):
    """Controlled schema validation failure."""


class SealVerificationError(ValueError):
    """Controlled integrity/configuration failure after schema validation."""


def _require(
    value: Any,
    path: str,
    expected: type | tuple[type, ...],
) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, dict):
            raise SealValidationError(
                f"{path}: esperava objeto, encontrou {type(current).__name__}"
            )
        if part not in current:
            raise SealValidationError(f"campo ausente: {path}")
        current = current[part]
    if expected is int and isinstance(current, bool):
        raise SealValidationError(f"{path}: esperava inteiro")
    if not isinstance(current, expected):
        names = (
            expected.__name__
            if isinstance(expected, type)
            else "/".join(item.__name__ for item in expected)
        )
        raise SealValidationError(
            f"{path}: esperava {names}, encontrou {type(current).__name__}"
        )
    return current


def _require_hex(value: Any, path: str) -> str:
    text = _require(value, path, str)
    if len(text) != HEX64 or any(
        char not in "0123456789abcdef" for char in text
    ):
        raise SealValidationError(f"{path}: SHA-256 inválido")
    return str(text)


def validate_seal(seal: Any) -> dict[str, Any]:
    """Validate the canonical seal contract before any field access."""
    if not isinstance(seal, dict):
        raise SealValidationError("selo: esperava objeto JSON")
    version = _require(seal, "schema_version", str)
    if version != SCHEMA_VERSION:
        raise SealValidationError(
            f"schema_version: desconhecido {version!r}; "
            f"esperado {SCHEMA_VERSION!r}"
        )
    _require_hex(seal, "schema_sha256")
    _require(seal, "status", str)
    _require(seal, "sealed_at", str)
    _require_hex(seal, "artifact.sha256")
    _require(seal, "artifact.path", str)
    _require(seal, "artifact.threshold", (int, float))
    _require(seal, "artifact.model", str)
    _require(seal, "artifact.C", (int, float))
    _require_hex(seal, "dataset.manifest_sha256")
    _require_hex(seal, "dataset.records_sha256")
    _require_hex(seal, "dataset.files_sha256")
    _require_hex(seal, "dataset.lineage_hashes_sha256")
    _require(seal, "dataset.path", str)
    _require(seal, "dataset.version", str)
    _require(seal, "dataset.reference_date", str)
    _require(seal, "dataset.seed", int)
    _require(seal, "dataset.n_total", int)
    _require(seal, "dataset.composition", dict)
    _require(seal, "dataset.intersection", dict)
    _require(seal, "dataset.intersection.old_ids", int)
    _require(seal, "dataset.intersection.old_entities", int)
    _require(seal, "ocr.sample", int)
    _require(seal, "ocr.primary", int)
    _require(seal, "ocr.experts", int)
    _require(seal, "ocr.variants", list)
    _require(seal, "features.count", int)
    _require_hex(seal, "features.names_sha256")
    _require_hex(seal, "features.implementation_sha256")
    _require(seal, "baselines.deterministic_threshold", (int, float))
    _require(seal, "baselines.fusion_threshold", (int, float))
    _require(seal, "baselines.logistic_threshold", (int, float))
    _require_hex(seal, "baselines.evaluator_sha256")
    _require(seal, "commits.generator", str)
    _require(seal, "commits.evaluator", str)
    _require(seal, "commits.protocol", str)
    _require(seal, "commits.extractor", str)
    _require(seal, "commits.model_code", str)
    _require(seal, "environment.python", str)
    _require(seal, "environment.scikit_learn", str)
    _require(seal, "environment.numpy", str)
    _require(seal, "environment.pymupdf", str)
    _require(seal, "environment.pillow", str)
    _require(seal, "environment.joblib", str)
    if seal["dataset"]["intersection"]["old_ids"] != 0:
        raise SealValidationError("dataset.intersection.old_ids deve ser 0")
    if seal["dataset"]["intersection"]["old_entities"] != 0:
        raise SealValidationError(
            "dataset.intersection.old_entities deve ser 0"
        )
    return seal


def verify_seal(
    seal: Any,
    model_path: str | Path,
    dataset_manifest_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    check_commits: bool = False,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate schema and integrity; never loads a model."""
    view = validate_seal(seal)
    schema_file = Path(schema_path) if schema_path else SCHEMA_PATH
    if not schema_file.exists():
        raise SealVerificationError(f"schema não encontrado: {schema_file}")
    schema_hash = hashlib.sha256(schema_file.read_bytes()).hexdigest()
    if schema_hash != view["schema_sha256"]:
        raise SealVerificationError("hash do schema não corresponde ao selo")
    model_file = Path(model_path)
    if not model_file.exists():
        raise SealVerificationError(f"artefato não encontrado: {model_file}")
    if hashlib.sha256(model_file.read_bytes()).hexdigest() != view["artifact"][
        "sha256"
    ]:
        raise SealVerificationError("hash do artefato não corresponde ao selo")
    manifest_file = Path(dataset_manifest_path)
    if not manifest_file.exists():
        raise SealVerificationError(
            f"manifest do dataset não encontrado: {manifest_file}"
        )
    if (
        hashlib.sha256(manifest_file.read_bytes()).hexdigest()
        != view["dataset"]["manifest_sha256"]
    ):
        raise SealVerificationError(
            "hash do manifest do dataset não corresponde ao selo"
        )
    from app.ml.features import FEATURE_NAMES

    features_hash = hashlib.sha256(
        json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
    ).hexdigest()
    if features_hash != view["features"]["names_sha256"]:
        raise SealVerificationError("hash da lista de features diverge")
    features_file = (
        Path(__file__).resolve().parent / "features.py"
    )
    if (
        hashlib.sha256(features_file.read_bytes()).hexdigest()
        != view["features"]["implementation_sha256"]
    ):
        raise SealVerificationError("hash de features.py diverge")
    if float(view["artifact"]["threshold"]) != 0.809:
        raise SealVerificationError("threshold Logistic deve ser 0.809")
    if float(view["baselines"]["deterministic_threshold"]) != 0.5:
        raise SealVerificationError("threshold Deterministic deve ser 0.5")
    if float(view["baselines"]["fusion_threshold"]) != 0.4:
        raise SealVerificationError("threshold Fusion deve ser 0.4")
    if check_commits:
        verify_commits(view, repo_root=repo_root)
    return view


def verify_commits(
    seal: dict[str, Any],
    *,
    repo_root: str | Path | None = None,
) -> None:
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    for name in ("generator", "evaluator", "protocol", "extractor", "model_code"):
        commit = str(seal["commits"][name])
        if len(commit) < 7:
            raise SealVerificationError(f"commit inválido: {name}")
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=root,
            capture_output=True,
        )
        if result.returncode != 0:
            raise SealVerificationError(
                f"commit selado não existe: {name}={commit}"
            )
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    for name in ("generator", "evaluator", "protocol"):
        commit = str(seal["commits"][name])
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, head],
            cwd=root,
            capture_output=True,
        )
        if ancestor.returncode != 0:
            raise SealVerificationError(
                f"commit {name} não é ancestral do HEAD atual"
            )


def preflight_and_load(
    seal: Any,
    model_path: str | Path,
    dataset_manifest_path: str | Path,
    *,
    loader: Callable[[str | Path], Any],
    schema_path: str | Path | None = None,
    check_commits: bool = False,
    repo_root: str | Path | None = None,
) -> tuple[dict[str, Any], Any]:
    """Preflight first; only then call the injected model loader."""
    view = verify_seal(
        seal,
        model_path,
        dataset_manifest_path,
        schema_path=schema_path,
        check_commits=check_commits,
        repo_root=repo_root,
    )
    return view, loader(model_path)
