import json
from pathlib import Path

from app.synthetic.holdout import (
    EXPERT_TYPES,
    SUPERVISED_TYPES,
    build_holdout,
)


def _build(out: Path, **kwargs):
    return build_holdout(
        out,
        legit_count=4,
        per_supervised=1,
        per_expert=1,
        ocr_per_type=1,
        ocr_legit_per_language=1,
        render_native=False,
        render_ocr=False,
        **kwargs,
    )


def test_holdout_composition_and_ocr_sample_are_pre_registered(tmp_path):
    manifest = _build(tmp_path / "holdout")

    assert manifest["n_total"] == 4 + len(SUPERVISED_TYPES) + len(EXPERT_TYPES)
    assert manifest["composition"] == {
        "legit": 4,
        "supervised_fraud": 14,
        "expert_fraud": 3,
        "total_fraud": 17,
    }
    assert manifest["ocr_config"]["sample"] == 14 + 3 + 3
    assert manifest["ocr_config"]["primary"] == 14 + 3
    assert manifest["ocr_config"]["experts"] == 3
    assert manifest["intersection"]["old_ids"] == 0
    assert len(manifest["lineage_hashes"]) == manifest["n_total"]
    assert len(manifest["records_sha256"]) == 64


def test_holdout_generation_is_deterministic_without_rendering(tmp_path):
    first = _build(tmp_path / "first", generator_commit="test")
    second = _build(tmp_path / "second", generator_commit="test")

    assert first["records_sha256"] == second["records_sha256"]
    assert first["ocr_config"]["sample_ids_sha256"] == second["ocr_config"][
        "sample_ids_sha256"
    ]


def test_holdout_records_are_not_in_train_or_validation(tmp_path):
    _build(tmp_path / "holdout", generator_commit="test")
    records = [
        json.loads(line)
        for line in (tmp_path / "holdout" / "records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert all(record["split"] == "holdout" for record in records)
    assert len({record["id"] for record in records}) == len(records)
