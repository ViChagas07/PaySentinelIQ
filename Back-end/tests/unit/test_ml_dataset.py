import json

from app.ml.dataset import build_dataset, build_external_ocr_dataset


def _write_rows(path, rows):
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _row(document_id, split, *, fraud=False, tamper=None, path="A_native", score=0):
    return {
        "document_id": document_id,
        "path": path,
        "split": split,
        "language": "pt",
        "layout": "A",
        "document_type": "boleto",
        "is_fraud": fraud,
        "sophistication": "naive" if fraud else None,
        "tamper_types": [tamper] if tamper else [],
        "expected_codes_any_of": [],
        "score": score,
        "risk_level": "LOW",
        "extracted_fields": {
            "linha_digitavel": "0019" + "0" * 43,
            "valor_nominal": 100.0,
            "data_vencimento": "20/01/2027",
        },
        "evidences": [],
        "warnings": [],
        "errors": [],
    }


def test_dataset_excludes_experts_and_keeps_splits_disjoint(tmp_path):
    dump = tmp_path / "dump.jsonl"
    _write_rows(
        dump,
        [
            _row("a", "train"),
            _row("b", "train", fraud=True, tamper="B1"),
            _row("c", "test_iid", fraud=True, tamper="B6"),
            _row("d", "test_shift", fraud=True, tamper="P4"),
            _row("e", "test_shift", fraud=True, tamper="P8"),
        ],
    )

    dataset = build_dataset(dump)

    assert dataset.y.tolist() == [0, 1, 1]
    assert [item["document_id"] for item in dataset.meta] == ["a", "b", "e"]
    by_split = {}
    for item in dataset.meta:
        by_split.setdefault(item["split"], set()).add(item["document_id"])
    assert not (by_split["train"] & by_split["test_shift"])


def test_external_ocr_aggregates_variants_per_document(tmp_path):
    dump = tmp_path / "ocr.jsonl"
    rows = []
    for variant, score in (("scanned_clean", 10), ("scanned_rot", 30)):
        row = _row(
            "a",
            "test_iid",
            path="B_ocr_clean",
            score=score,
        )
        row["variant"] = variant
        rows.append(row)
    rows.append(_row("b", "test_iid", path="C_ocr_degraded", score=5))
    _write_rows(dump, rows)

    dataset = build_external_ocr_dataset(dump)

    assert len(dataset.meta) == 2
    first = next(item for item in dataset.meta if item["document_id"] == "a")
    assert first["score"] == 30
