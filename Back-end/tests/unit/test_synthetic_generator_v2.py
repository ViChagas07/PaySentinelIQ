from datetime import date
import json
from pathlib import Path

from app.synthetic.dataset import build_dataset
from app.synthetic.records import build_document
from app.synthetic.values import COMPANIES, LABELS


def test_values_have_no_mojibake_markers():
    source = Path(__file__).resolve().parents[2] / "app/synthetic/values.py"
    text = source.read_text(encoding="utf-8")

    assert "\u00c3" not in text
    assert "\u00c2" not in text
    assert "\ufffd" not in text
    assert "Competência" in text
    assert "Líquido a Receber" in text
    assert "Período" in text


def test_generator_text_and_fields_are_coherent():
    document = build_document(
        index=900,
        base_seed=42,
        doc_kind="boleto",
        language="pt",
        layout="D",
        label_set="set2",
        split="train",
        tamper_types=[],
        today=date(2026, 11, 11),
    )

    assert "Data Limite de Pagamento" in document.page_text
    assert "Montante do Título" in document.page_text
    assert "Data de Emissão" in document.page_text
    assert "\u00c3" not in document.page_text
    assert "\ufffd" not in document.page_text
    year, month, day = document.fields["data_vencimento"].split("-")
    assert f"{day}/{month}/{year}" in document.page_text


def test_dataset_manifest_has_version_seed_splits_and_hashes(tmp_path):
    manifest = build_dataset(
        tmp_path,
        seed=42,
        n_total=12,
        render=0,
        dataset_version="v2-test",
        generator_version="v2",
    )
    records = [
        json.loads(line)
        for line in (tmp_path / "records.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert manifest["dataset_version"] == "v2-test"
    assert manifest["generator_version"] == "v2"
    assert manifest["seed"] == 42
    assert manifest["n_total"] == len(records) == 12
    assert manifest["splits"] == {
        "train": 7,
        "val": 1,
        "test_iid": 1,
        "test_shift": 3,
    }
    assert set(manifest["split_hashes"]) == {
        "train",
        "val",
        "test_iid",
        "test_shift",
    }
    assert len(manifest["records_sha256"]) == 64
    assert all(len(value) == 64 for value in manifest["split_hashes"].values())
    assert len(COMPANIES["pt"]) > 0
    assert LABELS["contracheque"]["pt"]["set2"]["inss"] == "Previdência"
