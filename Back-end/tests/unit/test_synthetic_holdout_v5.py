import json

from app.synthetic.holdout_v5 import (
    DATASET_VERSION,
    HOLDOUT_V5_SEED,
    build_holdout_v5,
)


def _build(out, **kwargs):
    return build_holdout_v5(
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


def test_v5_composition_sample_and_identity(tmp_path):
    manifest = _build(tmp_path / "v5", generator_commit="test")

    assert manifest["dataset_version"] == DATASET_VERSION
    assert manifest["seed"] == HOLDOUT_V5_SEED
    assert manifest["n_total"] == 21
    assert manifest["composition"]["total_fraud"] == 17
    assert manifest["ocr_config"]["sample"] == 20
    assert manifest["ocr_config"]["primary"] == 17
    assert manifest["ocr_config"]["experts"] == 3
    assert manifest["intersection"] == {"old_ids": 0, "old_entities": 0}
    records = [
        json.loads(line)
        for line in (tmp_path / "v5" / "records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert all(record["id"].startswith("syn-2029-") for record in records)
    assert all(record["split"] == "holdout" for record in records)


def test_v5_generation_is_deterministic(tmp_path):
    first = _build(tmp_path / "a", generator_commit="test")
    second = _build(tmp_path / "b", generator_commit="test")

    assert first["records_sha256"] == second["records_sha256"]
    assert first["lineage_hashes"] == second["lineage_hashes"]
