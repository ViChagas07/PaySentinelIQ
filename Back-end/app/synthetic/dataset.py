from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import random
from typing import Any

from app.synthetic.records import SyntheticDocument, build_document
from app.synthetic.render import render_all, render_variant

LANGUAGES = ("pt", "es", "en")
LAYOUTS = ("A", "B", "C")
BOLETO_NAIVE = ("B1", "B2", "B3", "B4", "B5", "B8")
BOLETO_EXPERT = ("B6", "B7")
PAYSLIP_NAIVE = ("P1", "P2", "P3", "P5", "P6", "P7", "P8", "P9")
PAYSLIP_EXPERT = ("P4",)


def _language(rng: random.Random, allowed: tuple[str, ...]) -> str:
    return rng.choices(
        allowed,
        weights=[0.5, 0.25, 0.25],
        k=1,
    )[0]


def _company_cnpj(record: SyntheticDocument) -> str:
    if record.doc_kind == "boleto":
        return record.fields["beneficiario_cnpj"]
    return record.fields["cnpj_empregador"]


def _tamper_codes(
    rng: random.Random,
    doc_kind: str,
) -> list[str]:
    if rng.random() >= 0.30:
        return []
    naive = BOLETO_NAIVE if doc_kind == "boleto" else PAYSLIP_NAIVE
    expert = BOLETO_EXPERT if doc_kind == "boleto" else PAYSLIP_EXPERT
    roll = rng.random()
    if roll < 0.70:
        return [rng.choice(naive)]
    if roll < 0.90:
        return rng.sample(naive, 2)
    return [rng.choice(expert)]


def _make_record(
    *,
    index: int,
    base_seed: int,
    split: str,
    rng: random.Random,
    today: date,
    shift: bool,
) -> SyntheticDocument:
    doc_kind = "boleto" if rng.random() < 0.5 else "contracheque"
    language = _language(rng, LANGUAGES)
    if split == "test_shift":
        layout = "D"
        label_set = "set2"
    else:
        layout = rng.choice(LAYOUTS)
        label_set = "set1"
    codes = _tamper_codes(rng, doc_kind)
    return build_document(
        index=index,
        base_seed=base_seed,
        doc_kind=doc_kind,
        language=language,
        layout=layout,
        label_set=label_set,
        split=split,
        tamper_types=codes,
        today=today,
        shift=shift,
    )


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_dataset(
    out_dir: str | Path,
    *,
    seed: int = 42,
    n_total: int = 1000,
    render: int = 60,
    langs: tuple[str, ...] = LANGUAGES,
) -> dict[str, Any]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    today = date.today()
    train_count = int(n_total * 0.60)
    val_count = int(n_total * 0.15)
    iid_count = int(n_total * 0.15)
    shift_count = n_total - train_count - val_count - iid_count

    records: list[SyntheticDocument] = []
    train_cnpjs: set[str] = set()
    index = 0
    for split, count, shift in (
        ("train", train_count, False),
        ("val", val_count, False),
        ("test_iid", iid_count, False),
        ("test_shift", shift_count, True),
    ):
        for _ in range(count):
            record = _make_record(
                index=index,
                base_seed=seed,
                split=split,
                rng=rng,
                today=today,
                shift=shift,
            )
            if split != "train":
                retries = 0
                while _company_cnpj(record) in train_cnpjs and retries < 20:
                    retries += 1
                    index += 10000
                    record = _make_record(
                        index=index,
                        base_seed=seed,
                        split=split,
                        rng=rng,
                        today=today,
                        shift=shift,
                    )
                if _company_cnpj(record) in train_cnpjs:
                    raise RuntimeError("Could not avoid CNPJ leakage")
            else:
                train_cnpjs.add(_company_cnpj(record))
            records.append(record)
            index += 1

    records_path = root / "records.jsonl"
    with records_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    rendered_documents: dict[str, dict[str, Any]] = {}
    if render > 0:
        step = max(1, len(records) // render)
        selected = records[::step][:render]
        for record in selected:
            paths = render_all(record, root / "files")
            rendered_documents[record.id] = paths

    manifest = {
        "seed": seed,
        "n_total": len(records),
        "render": len(rendered_documents),
        "langs": list(langs),
        "splits": {
            "train": train_count,
            "val": val_count,
            "test_iid": iid_count,
            "test_shift": shift_count,
        },
        "records_sha256": _hash_file(records_path),
        "files": {
            document_id: {
                variant: item["path"]
                for variant, item in variants.items()
            }
            for document_id, variants in rendered_documents.items()
        },
        "file_hashes": {
            document_id: {
                variant: item["sha256"]
                for variant, item in variants.items()
            }
            for document_id, variants in rendered_documents.items()
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def build_golden(
    out_dir: str | Path,
    *,
    seed: int = 2026,
) -> dict[str, Any]:
    root = Path(out_dir)
    legitimate_dir = root / "legitimate"
    fraudulent_dir = root / "fraudulent"
    legitimate_dir.mkdir(parents=True, exist_ok=True)
    fraudulent_dir.mkdir(parents=True, exist_ok=True)
    for directory in (legitimate_dir, fraudulent_dir):
        for old_file in directory.glob("syn-*"):
            old_file.unlink(missing_ok=True)
    today = date(2026, 11, 11)

    legitimate: list[SyntheticDocument] = []
    for index in range(18):
        kind = "boleto" if index < 9 else "contracheque"
        language = LANGUAGES[index % 3]
        record = build_document(
            index=index,
            base_seed=seed,
            doc_kind=kind,
            language=language,
            layout=LAYOUTS[index % 3],
            label_set="set1",
            split="golden",
            tamper_types=[],
            today=today,
        )
        legitimate.append(record)

    past_due_specs = (
        (200, "pt", "A", today - timedelta(days=45)),
        (201, "es", "B", today - timedelta(days=90)),
        (202, "en", "C", today - timedelta(days=180)),
        (203, "pt", "A", today - timedelta(days=420)),
    )
    for index, language, layout, due_date in past_due_specs:
        legitimate.append(
            build_document(
                index=index,
                base_seed=seed,
                doc_kind="boleto",
                language=language,
                layout=layout,
                label_set="set1",
                split="golden",
                tamper_types=[],
                today=today,
                due_date=due_date,
            )
        )
    for index, language, layout, bank in (
        (204, "pt", "B", "260"),
        (205, "es", "C", "077"),
    ):
        legitimate.append(
            build_document(
                index=index,
                base_seed=seed,
                doc_kind="boleto",
                language=language,
                layout=layout,
                label_set="set1",
                split="golden",
                tamper_types=[],
                today=today,
                bank=bank,
            )
        )

    fraud_types = [
        ["B1"],
        ["B2"],
        ["B3"],
        ["B4"],
        ["B5"],
        ["B6"],
        ["B7"],
        ["B8"],
        ["P1"],
        ["P2"],
        ["P3"],
        ["P4"],
        ["P5"],
        ["P6"],
        ["P7"],
        ["P8"],
        ["P9"],
        ["B1", "B2"],
    ]
    fraudulent: list[SyntheticDocument] = []
    for index, codes in enumerate(fraud_types):
        kind = "boleto" if codes[0].startswith("B") else "contracheque"
        record = build_document(
            index=100 + index,
            base_seed=seed,
            doc_kind=kind,
            language=LANGUAGES[index % 3],
            layout=LAYOUTS[index % 3],
            label_set="set1",
            split="golden",
            tamper_types=codes,
            today=today,
        )
        fraudulent.append(record)

    documents: list[dict[str, Any]] = []
    scanned_variants = {
        legitimate[0].id: ["scanned_clean"],
        legitimate[9].id: ["scanned_clean"],
        legitimate[11].id: ["scanned_clean"],
        legitimate[10].id: ["scanned_rot"],
        legitimate[18].id: ["scanned_clean"],
        legitimate[19].id: ["scanned_clean"],
        legitimate[20].id: ["scanned_rot"],
    }
    for record, target in [
        *((item, legitimate_dir) for item in legitimate),
        *((item, fraudulent_dir) for item in fraudulent),
    ]:
        files = {}
        variants = ["native", *scanned_variants.get(record.id, [])]
        for variant in variants:
            suffix = ".pdf"
            path = target / f"{record.id}_{variant}{suffix}"
            render_variant(record, variant, path)
            files[variant] = {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": _hash_file(path),
            }
        entry = record.to_dict()
        entry["files"] = files
        documents.append(entry)

    manifest = {
        "seed": seed,
        "count": len(documents),
        "documents": documents,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_golden_readme(root, documents)
    return manifest


def _write_golden_readme(
    root: Path,
    documents: list[dict[str, Any]],
) -> None:
    lines = [
        "# Golden set sintÃ©tico â€” PaySentinelIQ",
        "",
        "Documentos 100% fictÃ­cios, gerados por `app/synthetic`.",
        "Cada item possui a variante `native`; itens legÃ­timos possuem tambÃ©m "
        "`scanned_clean` ou `scanned_rot`.",
        "",
        "| ID | Tipo | Idioma | Layout | AdulteraÃ§Ã£o | Esperado | Banda |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in documents:
        tamper = ", ".join(item["tamper_types"]) or "nenhuma"
        expected = ", ".join(item["expected_codes_any_of"]) or "nenhum"
        lines.append(
            f"| {item['id']} | {item['doc_kind']} | {item['language']} | "
            f"{item['layout']} | {tamper} | {expected} | "
            f"{item['intended_band']} |"
        )
    lines.extend(
        [
            "",
            "Arquivos em `legitimate/` e `fraudulent/`; hashes em `manifest.json`.",
            "",
        ]
    )
    (root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def render_existing(
    out_dir: str | Path,
    *,
    seed: int = 42,
    render: int = 60,
) -> dict[str, Any]:
    root = Path(out_dir)
    records_path = root / "records.jsonl"
    if not records_path.exists():
        return build_dataset(root, seed=seed, render=render)
    records = [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rendered: dict[str, Any] = {}
    for item in records[:render]:
        record = SyntheticDocument(
            id=item["id"],
            seed=item["seed"],
            doc_kind=item["doc_kind"],
            language=item["language"],
            layout=item["layout"],
            label_set=item["label_set"],
            split=item["split"],
            is_fraud=item["is_fraud"],
            tamper_types=item["tamper_types"],
            sophistication=item["sophistication"],
            detectable_by=item["detectable_by"],
            expected_codes_any_of=item["expected_codes_any_of"],
            intended_band=item["intended_band"],
            fields=item["fields"],
            lines=item["page_text"].splitlines(),
            page_text=item["page_text"],
        )
        rendered[record.id] = render_all(record, root / "files")
    return rendered

