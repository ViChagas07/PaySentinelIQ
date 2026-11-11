from __future__ import annotations

from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import random

import fitz

from app.core.contracts.pipeline_context import PipelineContext
from app.services.validation.febraban import decode_linha_digitavel
from app.services.validation.payslip_rules import _cnpj_valid, _cpf_valid
from app.synthetic.dataset import build_dataset
from app.synthetic.febraban_builder import build_linha_digitavel
from app.synthetic.records import build_document
from app.synthetic.render import render_variant
from app.synthetic.values import (
    format_date,
    generate_cnpj,
    generate_cpf,
)

TODAY = date(2026, 11, 11)


def _doc(code: str):
    return build_document(
        index=7,
        base_seed=2026,
        doc_kind="boleto" if code.startswith("B") else "contracheque",
        language="pt",
        layout="B",
        label_set="set1",
        split="golden" if code in {"B8", "P9"} else "train",
        tamper_types=[code],
        today=TODAY,
    )


def test_generated_cnpj_cpf_and_lines_are_valid():
    rng = random.Random(77)
    for _ in range(200):
        assert _cnpj_valid(generate_cnpj(rng))
        assert _cpf_valid(generate_cpf(rng))

    for _index in range(1000):
        bank = rng.choice(("001", "033", "104", "237", "341", "260", "077"))
        free = "".join(str(rng.randrange(10)) for _ in range(25))
        line, _barcode = build_linha_digitavel(
            bank,
            "9",
            free,
            1000 + rng.randrange(0, 5000),
            rng.randrange(1, 1_000_000),
        )
        decoded = decode_linha_digitavel(line, today=TODAY)
        assert decoded["status"] == "ok"
        assert decoded["dv_geral_valido"] is True
        assert all(decoded["campo_dvs_validos"].values())

    line, _ = build_linha_digitavel(
        "001", "9", "1234567890123456789012345", 1000, 123456
    )
    bad = line[:32] + str((int(line[32]) + 1) % 10) + line[33:]
    assert decode_linha_digitavel(bad, today=TODAY)["dv_geral_valido"] is False


def test_english_dates_are_never_ambiguous_numeric():
    for index in range(200):
        record = build_document(
            index=index,
            base_seed=99,
            doc_kind="boleto",
            language="en",
            layout="B",
            label_set="set1",
            split="train",
            tamper_types=[],
            today=TODAY,
        )
        for key in ("data_vencimento", "data_documento"):
            value = date.fromisoformat(record.fields[key])
            rendered = format_date(value, "en")
            if "/" in rendered:
                month, day, _year = rendered.split("/")
                assert int(day) > 12
                assert 1 <= int(month) <= 12
        assert record.fields["number_style"] in {"us", "br"}


def test_tamper_catalog_matches_gabarito():
    b1 = _doc("B1")
    assert b1.fields["valor_nominal"] != b1.fields["valor_codificado"]

    b2 = _doc("B2")
    decoded = decode_linha_digitavel(b2.fields["linha_digitavel"], today=TODAY)
    assert b2.fields["data_vencimento"] != decoded["vencimento"]

    assert _doc("B3").fields["codigo_banco"] == "999"

    b4 = _doc("B4")
    assert not decode_linha_digitavel(
        b4.fields["linha_digitavel"], today=TODAY
    )["dv_geral_valido"]

    b5 = _doc("B5")
    assert Decimal(b5.fields["valor_nominal"]) != Decimal(
        decode_linha_digitavel(b5.fields["linha_digitavel"], today=TODAY)["valor"]
    )

    b6 = _doc("B6")
    assert Decimal(b6.fields["valor_nominal"]) == Decimal(
        decode_linha_digitavel(b6.fields["linha_digitavel"], today=TODAY)["valor"]
    )
    assert b6.expected_codes_any_of == []

    assert _doc("B7").expected_codes_any_of == []

    p1 = _doc("P1")
    assert Decimal(p1.fields["salario_liquido"]) != (
        Decimal(p1.fields["salario_bruto"])
        - Decimal(p1.fields["total_descontos"])
    )

    p2 = _doc("P2")
    assert p2.expected_codes_any_of == ["PAYSLIP_INSS_MISMATCH"]

    p3 = _doc("P3")
    assert Decimal(p3.fields["irrf"]) == 0

    assert _doc("P4").expected_codes_any_of == []
    assert not _cpf_valid(_doc("P5").fields["cpf_funcionario"])
    assert _doc("P6").fields["periodo"] == "12/2026"
    assert _doc("P7").expected_codes_any_of == ["PAYSLIP_FGTS_MISMATCH"]
    assert _doc("P8").expected_codes_any_of == [
        "PAYSLIP_DEDUCTIONS_INCONSISTENT"
    ]


def test_rendering_is_deterministic_and_has_synthetic_metadata(tmp_path):
    first = build_dataset(tmp_path / "a", seed=123, n_total=3, render=1)
    second = build_dataset(tmp_path / "b", seed=123, n_total=3, render=1)

    assert (tmp_path / "a" / "records.jsonl").read_bytes() == (
        tmp_path / "b" / "records.jsonl"
    ).read_bytes()
    assert first["file_hashes"] == second["file_hashes"]

    record = _doc("B1")
    native = tmp_path / "native.pdf"
    render_variant(record, "native", native)
    doc = fitz.open(str(native))
    text = "".join(page.get_text() for page in doc)
    assert "DOCUMENTO FICTICIO / SYNTHETIC SAMPLE" in text
    assert "synthetic" in doc.metadata.get("keywords", "").lower()
    doc.close()


def test_split_has_no_company_cnpj_leakage(tmp_path):
    build_dataset(tmp_path, seed=321, n_total=40, render=0)
    records = [
        json.loads(line)
        for line in (tmp_path / "records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    train = {
        item["fields"].get("beneficiario_cnpj")
        or item["fields"].get("cnpj_empregador")
        for item in records
        if item["split"] == "train"
    }
    tests = {
        item["fields"].get("beneficiario_cnpj")
        or item["fields"].get("cnpj_empregador")
        for item in records
        if item["split"].startswith("test")
    }
    assert not (train & tests)


def test_golden_native_expectations(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "resources" / "fraud_cases"
    manifest = json.loads(
        (root / "manifest.json").read_text(encoding="utf-8")
    )
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
    )
    from app.services.pipeline.canonical_pipeline import CanonicalPipeline

    pipeline = CanonicalPipeline()
    for item in manifest["documents"]:
        native = root / item["files"]["native"]["path"]
        ctx = PipelineContext(
            document_type=item["doc_kind"],
            file_bytes=native.read_bytes(),
            filename=native.name,
            mime_type="application/pdf",
        )
        result = pipeline.execute(ctx)
        codes = {evidence.code for evidence in ctx.evidences}
        if not item["is_fraud"]:
            assert result.risk_score < 70
            assert not any(
                evidence.severity.value == "critical"
                for evidence in ctx.evidences
            )
        elif item["sophistication"] in {"naive", "multi"}:
            assert codes & set(item["expected_codes_any_of"])


