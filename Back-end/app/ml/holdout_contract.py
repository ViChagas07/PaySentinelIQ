from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import subprocess
from types import MappingProxyType
from typing import Any, Callable, Mapping

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


@dataclass(frozen=True)
class HoldoutConfig:
    schema_version: str
    schema_sha256: str
    artifact_path: str
    artifact_sha256: str
    artifact_threshold: float
    artifact_model: str
    artifact_c: float
    dataset_path: str
    dataset_version: str
    reference_date: str
    dataset_seed: int
    dataset_n_total: int
    dataset_manifest_sha256: str
    dataset_records_sha256: str
    dataset_files_sha256: str
    dataset_lineage_hashes_sha256: str
    intersection_old_ids: int
    intersection_old_entities: int
    ocr_sample: int
    ocr_primary: int
    ocr_experts: int
    ocr_variants: tuple[str, ...]
    features_count: int
    features_names_sha256: str
    features_implementation_sha256: str
    deterministic_threshold: float
    fusion_threshold: float
    logistic_threshold: float
    evaluator_sha256: str
    commits: Mapping[str, str]
    environment: Mapping[str, str]


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


def validate_seal(seal: Any) -> HoldoutConfig:
    """Validate the canonical seal and return an immutable configuration."""
    if not isinstance(seal, dict):
        raise SealValidationError("selo: esperava objeto JSON")
    version = _require(seal, "schema_version", str)
    if version != SCHEMA_VERSION:
        raise SealValidationError(
            f"schema_version: desconhecido {version!r}; "
            f"esperado {SCHEMA_VERSION!r}"
        )
    schema_sha = _require_hex(seal, "schema_sha256")
    _require(seal, "status", str)
    _require(seal, "sealed_at", str)
    artifact_sha = _require_hex(seal, "artifact.sha256")
    artifact_path = _require(seal, "artifact.path", str)
    artifact_threshold = _require(
        seal, "artifact.threshold", (int, float)
    )
    artifact_model = _require(seal, "artifact.model", str)
    artifact_c = _require(seal, "artifact.C", (int, float))
    manifest_sha = _require_hex(seal, "dataset.manifest_sha256")
    records_sha = _require_hex(seal, "dataset.records_sha256")
    files_sha = _require_hex(seal, "dataset.files_sha256")
    lineage_sha = _require_hex(seal, "dataset.lineage_hashes_sha256")
    dataset_path = _require(seal, "dataset.path", str)
    dataset_version = _require(seal, "dataset.version", str)
    reference_date = _require(seal, "dataset.reference_date", str)
    dataset_seed = _require(seal, "dataset.seed", int)
    dataset_n_total = _require(seal, "dataset.n_total", int)
    old_ids = _require(seal, "dataset.intersection.old_ids", int)
    old_entities = _require(
        seal, "dataset.intersection.old_entities", int
    )
    if old_ids != 0:
        raise SealValidationError("dataset.intersection.old_ids deve ser 0")
    if old_entities != 0:
        raise SealValidationError(
            "dataset.intersection.old_entities deve ser 0"
        )
    ocr_sample = _require(seal, "ocr.sample", int)
    ocr_primary = _require(seal, "ocr.primary", int)
    ocr_experts = _require(seal, "ocr.experts", int)
    variants = _require(seal, "ocr.variants", list)
    if not all(isinstance(item, str) for item in variants):
        raise SealValidationError("ocr.variants: esperava lista de strings")
    features_count = _require(seal, "features.count", int)
    features_names = _require_hex(seal, "features.names_sha256")
    features_impl = _require_hex(
        seal, "features.implementation_sha256"
    )
    deterministic = _require(
        seal, "baselines.deterministic_threshold", (int, float)
    )
    fusion = _require(
        seal, "baselines.fusion_threshold", (int, float)
    )
    logistic = _require(
        seal, "baselines.logistic_threshold", (int, float)
    )
    evaluator_sha = _require_hex(
        seal, "baselines.evaluator_sha256"
    )
    commits = MappingProxyType(
        {
            name: _require(seal, f"commits.{name}", str)
            for name in (
                "generator",
                "evaluator",
                "protocol",
                "extractor",
                "model_code",
            )
        }
    )
    environment = MappingProxyType(
        {
            name: _require(seal, f"environment.{name}", str)
            for name in (
                "python",
                "scikit_learn",
                "numpy",
                "pymupdf",
                "pillow",
                "joblib",
            )
        }
    )
    return HoldoutConfig(
        schema_version=version,
        schema_sha256=schema_sha,
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha,
        artifact_threshold=float(artifact_threshold),
        artifact_model=artifact_model,
        artifact_c=float(artifact_c),
        dataset_path=dataset_path,
        dataset_version=dataset_version,
        reference_date=reference_date,
        dataset_seed=dataset_seed,
        dataset_n_total=dataset_n_total,
        dataset_manifest_sha256=manifest_sha,
        dataset_records_sha256=records_sha,
        dataset_files_sha256=files_sha,
        dataset_lineage_hashes_sha256=lineage_sha,
        intersection_old_ids=old_ids,
        intersection_old_entities=old_entities,
        ocr_sample=ocr_sample,
        ocr_primary=ocr_primary,
        ocr_experts=ocr_experts,
        ocr_variants=tuple(variants),
        features_count=features_count,
        features_names_sha256=features_names,
        features_implementation_sha256=features_impl,
        deterministic_threshold=float(deterministic),
        fusion_threshold=float(fusion),
        logistic_threshold=float(logistic),
        evaluator_sha256=evaluator_sha,
        commits=commits,
        environment=environment,
    )


def load_config(seal_path: str | Path) -> HoldoutConfig:
    try:
        raw = json.loads(Path(seal_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SealValidationError(f"selo ilegível: {exc}") from exc
    return validate_seal(raw)


def verify_config(
    config: HoldoutConfig,
    model_path: str | Path,
    dataset_manifest_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    check_commits: bool = False,
    repo_root: str | Path | None = None,
) -> HoldoutConfig:
    schema_file = Path(schema_path) if schema_path else SCHEMA_PATH
    if not schema_file.exists():
        raise SealVerificationError(f"schema não encontrado: {schema_file}")
    if (
        hashlib.sha256(schema_file.read_bytes()).hexdigest()
        != config.schema_sha256
    ):
        raise SealVerificationError("hash do schema não corresponde ao selo")
    model_file = Path(model_path)
    if not model_file.exists():
        raise SealVerificationError(f"artefato não encontrado: {model_file}")
    if hashlib.sha256(model_file.read_bytes()).hexdigest() != config.artifact_sha256:
        raise SealVerificationError("hash do artefato não corresponde ao selo")
    manifest_file = Path(dataset_manifest_path)
    if not manifest_file.exists():
        raise SealVerificationError(
            f"manifest do dataset não encontrado: {manifest_file}"
        )
    if (
        hashlib.sha256(manifest_file.read_bytes()).hexdigest()
        != config.dataset_manifest_sha256
    ):
        raise SealVerificationError(
            "hash do manifest do dataset não corresponde ao selo"
        )
    from app.ml.features import FEATURE_NAMES

    features_hash = hashlib.sha256(
        json.dumps(FEATURE_NAMES, ensure_ascii=False).encode()
    ).hexdigest()
    if features_hash != config.features_names_sha256:
        raise SealVerificationError("hash da lista de features diverge")
    features_file = Path(__file__).resolve().parent / "features.py"
    if (
        hashlib.sha256(features_file.read_bytes()).hexdigest()
        != config.features_implementation_sha256
    ):
        raise SealVerificationError("hash de features.py diverge")
    evaluator_file = Path(__file__).resolve().parent / "evaluate_holdout.py"
    if (
        hashlib.sha256(evaluator_file.read_bytes()).hexdigest()
        != config.evaluator_sha256
    ):
        raise SealVerificationError("hash do avaliador diverge")
    if config.artifact_threshold != 0.809:
        raise SealVerificationError("threshold Logistic deve ser 0.809")
    if config.deterministic_threshold != 0.5:
        raise SealVerificationError("threshold Deterministic deve ser 0.5")
    if config.fusion_threshold != 0.4:
        raise SealVerificationError("threshold Fusion deve ser 0.4")
    if check_commits:
        verify_commits(config, repo_root=repo_root)
    return config


def verify_seal(
    seal: Any,
    model_path: str | Path,
    dataset_manifest_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    check_commits: bool = False,
    repo_root: str | Path | None = None,
) -> HoldoutConfig:
    """Validate a raw seal and verify its integrity; never loads a model."""
    config = validate_seal(seal)
    return verify_config(
        config,
        model_path,
        dataset_manifest_path,
        schema_path=schema_path,
        check_commits=check_commits,
        repo_root=repo_root,
    )


def verify_commits(
    config: HoldoutConfig,
    *,
    repo_root: str | Path | None = None,
) -> None:
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    for name in ("generator", "evaluator", "protocol", "extractor", "model_code"):
        commit = str(config.commits[name])
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
        commit = str(config.commits[name])
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
    seal_path: str | Path,
    model_path: str | Path,
    *,
    loader: Callable[[str | Path], Any],
    schema_path: str | Path | None = None,
    check_commits: bool = False,
    repo_root: str | Path | None = None,
) -> tuple[HoldoutConfig, Any]:
    """Read/validate the raw seal inside the contract; load only on success."""
    config = load_config(seal_path)
    manifest_path = Path(config.dataset_path) / "manifest.json"
    config = verify_config(
        config,
        model_path,
        manifest_path,
        schema_path=schema_path,
        check_commits=check_commits,
        repo_root=repo_root,
    )
    return config, loader(model_path)
