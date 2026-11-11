from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
from typing import Any

from app.synthetic.holdout import (
    EXPERT_TYPES,
    HOLDOUT_TODAY,
    LANGUAGES,
    SUPERVISED_TYPES,
    _hash,
    _layout,
    _ocr_sample,
)
from app.synthetic.records import SyntheticDocument, build_document
from app.synthetic.render import render_variant

HOLDOUT_V4_SEED = 2028
DATASET_VERSION = "holdout-v4"
GENERATOR_VERSION = "v4"

COMPANIES = {
    "pt": (
        "Horizonte Verde Papelaria Ltda",
        "Ipê Azul Metais Ltda",
        "Jaguar Solar Software Ltda",
        "Kaizen Norte Facilities Ltda",
        "Lume Sereno Logística Ltda",
        "Mira Vale Consultoria Ltda",
    ),
    "es": (
        "Horizonte Verde Papeleria S.A.",
        "Ipe Azul Metales S.A.",
        "Jaguar Solar Software S.A.",
        "Kaizen Norte Facilities S.A.",
        "Lume Sereno Logistica S.A.",
        "Mira Valle Consultoria S.A.",
    ),
    "en": (
        "Green Horizon Stationery Inc.",
        "Blue Ipe Metals Inc.",
        "Solar Jaguar Software Inc.",
        "Kaizen North Facilities Inc.",
        "Serene Light Logistics Inc.",
        "Vale View Consulting Inc.",
    ),
}
PEOPLE = {
    "pt": (
        "Sofia Vale Horizonte",
        "Tadeu Ipe Azul",
        "Úrsula Jaguar Norte",
        "Vicente Lume Sereno",
        "Wanda Mira Vale",
        "Yara Horizonte Verde",
    ),
    "es": (
        "Sofia Valle Horizonte",
        "Tadeo Ipe Azul",
        "Ursula Jaguar Norte",
        "Vicente Lume Sereno",
        "Wanda Mira Valle",
        "Yara Horizonte Verde",
    ),
    "en": (
        "Sofia Green Horizonte",
        "Tadeo Blue Ipe",
        "Ursula Jaguar North",
        "Vicente Serene Light",
        "Wanda Vale View",
        "Yara Green Horizon",
    ),
}
ROLES = {
    "pt": ("Analista Horizonte", "Assistente Ipe", "Coordenador Jaguar"),
    "es": ("Analista Horizonte", "Asistente Ipe", "Coordinador Jaguar"),
    "en": ("Horizonte Analyst", "Ipe Assistant", "Jaguar Coordinator"),
}


def _document(
    index: int,
    kind: str,
    language: str,
    tamper: list[str],
) -> SyntheticDocument:
    layout, label_set = _layout(index)
    return build_document(
        index=index,
        base_seed=HOLDOUT_V4_SEED,
        doc_kind=kind,
        language=language,
        layout=layout,
        label_set=label_set,
        split="holdout",
        tamper_types=tamper,
        today=HOLDOUT_TODAY,
        company_pool=COMPANIES[language],
        person_pool=PEOPLE[language],
        role_pool=ROLES[language],
    )


def _records(
    legit_count: int,
    per_supervised: int,
    per_expert: int,
) -> list[SyntheticDocument]:
    records: list[SyntheticDocument] = []
    index = 0
    for position in range(legit_count):
        kind = "boleto" if position % 2 == 0 else "contracheque"
        records.append(_document(index, kind, LANGUAGES[index % 3], []))
        index += 1
    for tamper in SUPERVISED_TYPES:
        kind = "boleto" if tamper.startswith("B") else "contracheque"
        for _ in range(per_supervised):
            records.append(
                _document(index, kind, LANGUAGES[index % 3], [tamper])
            )
            index += 1
    for tamper in EXPERT_TYPES:
        kind = "boleto" if tamper.startswith("B") else "contracheque"
        for _ in range(per_expert):
            records.append(
                _document(index, kind, LANGUAGES[index % 3], [tamper])
            )
            index += 1
    return records


def _old_ids_and_entities() -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    entities: set[str] = set()
    base = Path("../data/synthetic")
    versions = ("v1", "v2", "v2.1")
    for version in versions:
        path = base / version / "records.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            ids.add(record["id"])
            fields = record.get("fields") or {}
            for key in ("razao_social", "nome_funcionario", "beneficiario"):
                value = fields.get(key)
                if value:
                    entities.add(str(value).strip().lower())
    v3 = Path("../data/holdout/v3_seed2027/records.jsonl")
    if v3.exists():
        for line in v3.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            ids.add(record["id"])
            fields = record.get("fields") or {}
            for key in ("razao_social", "nome_funcionario", "beneficiario"):
                value = fields.get(key)
                if value:
                    entities.add(str(value).strip().lower())
    return ids, entities


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def build_holdout_v4(
    out_dir: str | Path,
    *,
    legit_count: int = 660,
    per_supervised: int = 20,
    per_expert: int = 20,
    ocr_per_type: int = 8,
    ocr_legit_per_language: int = 16,
    render_native: bool = True,
    render_ocr: bool = True,
    generator_commit: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    records = _records(legit_count, per_supervised, per_expert)
    records_path = root / "records.jsonl"
    with records_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    files: dict[str, dict[str, dict[str, str]]] = {}
    if render_native:
        for record in records:
            path = root / "files" / "native" / f"{record.id}.pdf"
            render_variant(record, "native", path)
            files.setdefault(record.id, {})["native"] = {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": _hash(path.read_bytes()),
            }

    sample = _ocr_sample(records, ocr_per_type, ocr_legit_per_language)
    if render_ocr:
        for record in sample:
            for variant in ("scanned_clean", "scanned_rot"):
                path = root / "files" / variant / f"{record.id}.pdf"
                render_variant(record, variant, path)
                files.setdefault(record.id, {})[variant] = {
                    "path": str(path.relative_to(root)).replace("\\", "/"),
                    "sha256": _hash(path.read_bytes()),
                }

    type_counts = Counter(
        tamper for record in records if record.is_fraud for tamper in record.tamper_types
    )
    sample_primary = [
        record for record in sample if not set(record.tamper_types) & set(EXPERT_TYPES)
    ]
    sample_experts = [
        record for record in sample if set(record.tamper_types) & set(EXPERT_TYPES)
    ]
    old_ids, old_entities = _old_ids_and_entities()
    holdout_ids = {record.id for record in records}
    holdout_entities = {
        str(record.fields.get(key)).strip().lower()
        for record in records
        for key in ("razao_social", "nome_funcionario", "beneficiario")
        if record.fields.get(key)
    }
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generator_version": GENERATOR_VERSION,
        "seed": HOLDOUT_V4_SEED,
        "reference_date": HOLDOUT_TODAY.isoformat(),
        "generated_on": HOLDOUT_TODAY.isoformat(),
        "generator_commit": generator_commit or _git_commit(),
        "status": "prepared; NOT evaluated",
        "n_total": len(records),
        "composition": {
            "legit": legit_count,
            "supervised_fraud": len(SUPERVISED_TYPES) * per_supervised,
            "expert_fraud": len(EXPERT_TYPES) * per_expert,
            "total_fraud": len(SUPERVISED_TYPES) * per_supervised
            + len(EXPERT_TYPES) * per_expert,
        },
        "tamper_types": dict(sorted(type_counts.items())),
        "per_supervised_type": per_supervised,
        "per_expert_type": per_expert,
        "splits": {"holdout": len(records)},
        "lineage_rule": "lineage_id = document_id; no reuse across versions",
        "lineage_hashes": {record.id: _hash(record.id) for record in records},
        "records_sha256": _hash(records_path.read_bytes()),
        "files": files,
        "ocr_config": {
            "selection_rule": (
                "top 8 by sha256(id:type:ocr) per type; "
                "16 legit per language by sha256(id:language:legit:ocr)"
            ),
            "variants": ["scanned_clean", "scanned_rot"],
            "sample": len(sample),
            "primary": len(sample_primary),
            "experts": len(sample_experts),
            "primary_ids_sha256": _hash(
                json.dumps(sorted(record.id for record in sample_primary))
            ),
            "sample_ids_sha256": _hash(
                json.dumps(sorted(record.id for record in sample))
            ),
        },
        "intersection": {
            "old_ids": len(holdout_ids & old_ids),
            "old_entities": len(holdout_entities & old_entities),
        },
        "policy": "sealed holdout; no model inference before seal",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../data/holdout/v4_seed2028")
    parser.add_argument("--generator-commit", default=None)
    args = parser.parse_args()
    manifest = build_holdout_v4(
        args.out,
        generator_commit=args.generator_commit,
    )
    print(json.dumps(manifest["composition"], ensure_ascii=False))
    print(
        f"records={manifest['n_total']} ocr_sample={manifest['ocr_config']['sample']} "
        f"out={args.out} records_sha256={manifest['records_sha256']}"
    )


if __name__ == "__main__":
    main()
