# mypy: ignore-errors
from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import time
import unicodedata
from typing import Any

from app.core.contracts.pipeline_context import PipelineContext
from app.services.extraction.prelude import run_ocr_prelude
from app.services.ocr.base import OCRProvider, OCRResult
from app.services.ocr.native_text_provider import NativeTextFirstOCRProvider
from app.services.ocr.remote_provider import RemoteOCRProvider
from app.services.pipeline.canonical_pipeline import CanonicalPipeline
from app.services.pipeline.stages.crewai_stage import CrewAIStage
from app.synthetic.records import SyntheticDocument
from app.synthetic.render import render_variant

BOLETO_FIELDS = (
    "linha_digitavel",
    "cnpj",
    "valor_nominal",
    "data_vencimento",
    "beneficiario",
    "codigo_banco",
)
PAYSLIP_FIELDS = (
    "cnpj",
    "cpf",
    "salario_bruto",
    "total_descontos",
    "salario_liquido",
    "inss",
    "irrf",
    "fgts",
    "periodo",
    "nome_funcionario",
)


@dataclass
class Observation:
    path: str
    variant: str
    item: dict
    result: object
    context: PipelineContext
    seconds: float
    evidence_stages: dict[str, str]
    extracted_text: str


class _ForbiddenOCRProvider(OCRProvider):
    """Provider used by path A: OCR must never be called for native PDFs."""

    async def extract_text(self, file_path: str) -> OCRResult:
        raise AssertionError(
            "OCR was invoked on a native-text PDF; the native layer must win"
        )

    async def health_check(self) -> bool:
        return False

    def get_info(self) -> dict[str, str]:
        return {"provider": "forbidden"}


def _fold(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in text if not unicodedata.combining(char)
    ).lower().strip()


def _digits(value) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _date(value):
    if not value:
        return None
    text = str(value)
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        try:
            return datetime.strptime(text, "%d/%m/%Y").date()
        except ValueError:
            return None


def _compare(item: dict, extracted: dict, field: str) -> bool | None:
    kind = item["doc_kind"]
    fields = item["fields"]
    if kind == "boleto":
        if field == "linha_digitavel":
            return _digits(extracted.get("linha_digitavel")) == _digits(
                fields.get("linha_digitavel")
            )
        if field == "cnpj":
            return _digits(extracted.get("cnpj")) == _digits(
                fields.get("beneficiario_cnpj")
            )
        if field == "valor_nominal":
            return _decimal(extracted.get("valor_nominal")) == Decimal(
                fields["valor_nominal"]
            )
        if field == "data_vencimento":
            return _date(extracted.get("data_vencimento")) == _date(
                fields.get("data_vencimento")
            )
        if field == "beneficiario":
            return _fold(str(extracted.get("beneficiario", ""))) == _fold(
                fields["beneficiario"]
            )
        if field == "codigo_banco":
            return _digits(extracted.get("codigo_banco")) == _digits(
                fields.get("codigo_banco")
            )
    else:
        if field == "cnpj":
            return _digits(extracted.get("cnpj")) == _digits(
                fields.get("cnpj_empregador")
            )
        if field == "cpf":
            return _digits(extracted.get("cpf")) == _digits(
                fields.get("cpf_funcionario")
            )
        if field == "nome_funcionario":
            return _fold(
                str(extracted.get("nome_funcionario", ""))
            ) == _fold(fields["nome_funcionario"])
        if field == "periodo":
            return str(extracted.get("periodo", "")) == fields["periodo"]
        return _decimal(extracted.get(field)) == Decimal(fields[field])
    return None


def _to_document(item: dict) -> SyntheticDocument:
    return SyntheticDocument(
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


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _instrument_stages(pipeline: CanonicalPipeline) -> dict[str, str]:
    holder = {"stage": "unknown"}
    for stage in pipeline._stages:
        original = stage.execute

        def wrapped(context, _stage=stage, _original=original):
            holder["stage"] = _stage.name
            return _original(context)

        stage.execute = wrapped  # type: ignore[method-assign]
    return holder


def _capture_evidence_stages(
    context: PipelineContext,
    holder: dict[str, str],
) -> dict[str, str]:
    stages: dict[str, str] = {}
    original_single = context.add_evidence

    def add_single(evidence) -> None:
        had = any(item.code == evidence.code for item in context.evidences)
        original_single(evidence)
        if not had and any(
            item.code == evidence.code for item in context.evidences
        ):
            stages.setdefault(evidence.code, holder["stage"])

    def add_many(evidences) -> None:
        for evidence in evidences:
            add_single(evidence)

    context.add_evidence = add_single  # type: ignore[method-assign]
    context.add_evidences = add_many  # type: ignore[method-assign]
    return stages


def _evidence_dump(
    observation: Observation,
) -> dict[str, Any]:
    item = observation.item
    ctx = observation.context
    result = observation.result
    return {
        "document_id": item["id"],
        "path": observation.path,
        "variant": observation.variant,
        "document_type": item["doc_kind"],
        "language": item["language"],
        "layout": item["layout"],
        "split": item["split"],
        "is_fraud": item["is_fraud"],
        "tamper_types": item["tamper_types"],
        "sophistication": item["sophistication"],
        "intended_band": item["intended_band"],
        "expected_codes_any_of": item["expected_codes_any_of"],
        "gabarito_fields": _json_safe(item["fields"]),
        "extracted_fields": _json_safe(ctx.extracted_fields),
        "extracted_text": observation.extracted_text,
        "evidences": [
            {
                **evidence.to_dict(),
                "metadata": _json_safe(evidence.metadata),
                "stage": observation.evidence_stages.get(
                    evidence.code, "unknown"
                ),
            }
            for evidence in ctx.evidences
        ],
        "score": float(result.risk_score),
        "risk_level": str(result.risk_level),
        "warnings": list(ctx.warnings),
        "errors": list(ctx.errors),
        "seconds": observation.seconds,
    }


async def _native_observation(
    item: dict,
    pipeline: CanonicalPipeline,
    provider: OCRProvider,
    temp_dir: Path,
    holder: dict[str, str],
) -> Observation:
    document = _to_document(item)
    path = temp_dir / f"{item['id']}_native.pdf"
    render_variant(document, "native", path)
    started = time.perf_counter()
    ctx = PipelineContext(
        document_type=item["doc_kind"],
        file_bytes=path.read_bytes(),
        filename=path.name,
        mime_type="application/pdf",
    )
    stages = _capture_evidence_stages(ctx, holder)
    await run_ocr_prelude(ctx, provider=provider)
    result = await asyncio.to_thread(pipeline.execute, ctx)
    return Observation(
        path="A_native",
        variant="native",
        item=item,
        result=result,
        context=ctx,
        seconds=time.perf_counter() - started,
        evidence_stages=stages,
        extracted_text=ctx.extracted_text,
    )


async def _ocr_observation(
    item: dict,
    variant: str,
    path: Path,
    pipeline: CanonicalPipeline,
    provider: RemoteOCRProvider,
    group: str,
    holder: dict[str, str],
) -> Observation:
    started = time.perf_counter()
    ocr_result = await provider.extract_text(str(path))
    ctx = PipelineContext(
        document_type=item["doc_kind"],
        file_bytes=path.read_bytes(),
        filename=path.name,
        mime_type=(
            "image/png" if path.suffix.lower() == ".png" else "application/pdf"
        ),
        extracted_text=ocr_result.text,
        extraction_method=ocr_result.provider,
        page_count=ocr_result.page_count,
        ocr_confidence=min(100.0, ocr_result.confidence * 100),
        metadata={
            "ocr": {
                "status": "completed",
                "provider": ocr_result.provider,
            },
            "ocr_prelude": True,
        },
    )
    stages = _capture_evidence_stages(ctx, holder)
    result = await asyncio.to_thread(pipeline.execute, ctx)
    return Observation(
        path=group,
        variant=variant,
        item=item,
        result=result,
        context=ctx,
        seconds=time.perf_counter() - started,
        evidence_stages=stages,
        extracted_text=ctx.extracted_text,
    )


def _rate(hits: int, total: int) -> str:
    return f"{hits}/{total} ({100 * hits / total:.1f}%)" if total else "0/0"


def _aggregate(
    observations: list[Observation],
) -> dict:
    extraction: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    by_field: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    by_language: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    by_layout: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    by_kind: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    digit: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    times: dict[str, list[float]] = defaultdict(list)
    false_positive: dict[str, dict] = defaultdict(
        lambda: {
            "legit": 0,
            "high": 0,
            "medium": 0,
            "codes": Counter(),
            "critical": Counter(),
        }
    )
    detection: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    confusion: dict[tuple[str, str, str], int] = Counter()
    expert: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    forensic: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for obs in observations:
        item = obs.item
        result = obs.result
        ctx = obs.context
        extracted = ctx.extracted_fields
        codes = [evidence.code for evidence in ctx.evidences]
        times[obs.path].append(obs.seconds)
        fields = BOLETO_FIELDS if item["doc_kind"] == "boleto" else PAYSLIP_FIELDS
        for field in fields:
            match = _compare(item, extracted, field)
            category = "text" if field in {"beneficiario", "nome_funcionario"} else "digits"
            for bucket in (
                extraction[(obs.path, item["language"], item["layout"], item["doc_kind"], field)],
                by_field[(obs.path, field)],
                by_language[(obs.path, item["language"])],
                by_layout[(obs.path, item["layout"])],
                by_kind[(obs.path, item["doc_kind"])],
                digit[(obs.path, category)],
            ):
                bucket[1] += 1
                if match:
                    bucket[0] += 1

        if not item["is_fraud"]:
            fp = false_positive[obs.path]
            fp["legit"] += 1
            if result.risk_score >= 70:
                fp["high"] += 1
            if result.risk_score >= 40:
                fp["medium"] += 1
            fp["codes"].update(codes)
            fp["critical"].update(
                evidence.code
                for evidence in ctx.evidences
                if evidence.severity.value == "critical"
            )
        else:
            for tamper in item["tamper_types"]:
                detection[(obs.path, tamper)][1] += 1
                if set(codes) & set(item["expected_codes_any_of"]):
                    detection[(obs.path, tamper)][0] += 1
            confusion[(obs.path, item["intended_band"], str(result.risk_level))] += 1
            if item["sophistication"] == "expert":
                for tamper in item["tamper_types"]:
                    expert[(obs.path, tamper)][1] += 1
                    if set(codes) & set(item["expected_codes_any_of"]):
                        expert[(obs.path, tamper)][0] += 1
            if set(item["tamper_types"]) & {"B8", "P9"}:
                forensic[obs.path][1] += 1
                if any(
                    any(word in code.upper() for word in ("PDF", "FORENS", "EDIT"))
                    for code in codes
                ):
                    forensic[obs.path][0] += 1

    return {
        "extraction": extraction,
        "by_field": by_field,
        "by_language": by_language,
        "by_layout": by_layout,
        "by_kind": by_kind,
        "digit": digit,
        "times": times,
        "false_positive": false_positive,
        "detection": detection,
        "confusion": confusion,
        "expert": expert,
        "forensic": forensic,
    }


def _fix_line(line: str) -> str:
    try:
        return line.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return line


def _write_report(
    path: Path,
    manifest: dict,
    aggregate: dict,
    native_count: int,
    title: str,
) -> None:
    lines = [
        f"# {title}",
        "",
        f"Dataset seed **{manifest['seed']}**, {manifest['n_total']} documentos, "
        f"{manifest['render']} renderizados; native avaliado em {native_count}.",
        "",
        "Todos os documentos são fictícios. Nenhum limiar de aprovação foi usado.",
        "",
        "## Precisão de extração por caminho (campos comparados)",
        "",
        "| Caminho | Acertos |",
        "|---|---:|",
    ]
    for path_name in sorted(
        {key[0] for key in aggregate["by_field"]}
    ):
        total = sum(
            value[1]
            for key, value in aggregate["by_field"].items()
            if key[0] == path_name
        )
        hits = sum(
            value[0]
            for key, value in aggregate["by_field"].items()
            if key[0] == path_name
        )
        lines.append(f"| {path_name} | {_rate(hits, total)} |")

    lines.extend(
        [
            "",
            "### Por campo",
            "",
            "| Caminho | Campo | Acertos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, field), value in sorted(aggregate["by_field"].items()):
        lines.append(
            f"| {path_name} | {field} | {_rate(value[0], value[1])} |"
        )
    lines.extend(
        [
            "",
            "### Por idioma",
            "",
            "| Caminho | Idioma | Acertos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, language), value in sorted(aggregate["by_language"].items()):
        lines.append(
            f"| {path_name} | {language} | {_rate(value[0], value[1])} |"
        )
    lines.extend(
        [
            "",
            "### Por layout",
            "",
            "| Caminho | Layout | Acertos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, layout), value in sorted(aggregate["by_layout"].items()):
        lines.append(f"| {path_name} | {layout} | {_rate(value[0], value[1])} |")
    lines.extend(
        [
            "",
            "### Por tipo de documento",
            "",
            "| Caminho | Tipo | Acertos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, kind), value in sorted(aggregate["by_kind"].items()):
        lines.append(f"| {path_name} | {kind} | {_rate(value[0], value[1])} |")

    lines.extend(
        [
            "",
            "### Dígitos vs texto em OCR",
            "",
            "| Caminho | Classe | Acertos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, category), value in sorted(aggregate["digit"].items()):
        lines.append(f"| {path_name} | {category} | {_rate(value[0], value[1])} |")

    lines.extend(
        [
            "",
            "## Falsos positivos em legítimos",
            "",
            "| Caminho | Legítimos | Score >= 70 | Score >= 40 | Top códigos | Críticos |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for path_name, fp in sorted(aggregate["false_positive"].items()):
        top = ", ".join(
            f"{code}:{count}" for code, count in fp["codes"].most_common(5)
        ) or "-"
        critical = ", ".join(
            f"{code}:{count}" for code, count in fp["critical"].most_common(5)
        ) or "-"
        lines.append(
            f"| {path_name} | {fp['legit']} | {fp['high']} | {fp['medium']} | "
            f"{top} | {critical} |"
        )

    lines.extend(
        [
            "",
            "## Detecção por adulteração",
            "",
            "| Caminho | Tipo | Detectado |",
            "|---|---|---:|",
        ]
    )
    for (path_name, tamper), value in sorted(aggregate["detection"].items()):
        lines.append(
            f"| {path_name} | {tamper} | {_rate(value[0], value[1])} |"
        )

    lines.extend(
        [
            "",
            "## Matriz de confusão da banda final",
            "",
            "| Caminho | Intenção | LOW | MEDIUM | HIGH |",
            "|---|---|---:|---:|---:|",
        ]
    )
    paths = sorted({key[0] for key in aggregate["confusion"]})
    for path_name in paths:
        for intended in ("LOW", "MEDIUM", "HIGH"):
            lines.append(
                f"| {path_name} | {intended} | "
                f"{aggregate['confusion'].get((path_name, intended, 'LOW'), 0)} | "
                f"{aggregate['confusion'].get((path_name, intended, 'MEDIUM'), 0)} | "
                f"{aggregate['confusion'].get((path_name, intended, 'HIGH'), 0)} |"
            )

    lines.extend(
        [
            "",
            "## Expert — cobertura atual (esperado próximo de zero)",
            "",
            "| Caminho | Tipo | Detectado |",
            "|---|---|---:|",
        ]
    )
    for (path_name, tamper), value in sorted(aggregate["expert"].items()):
        lines.append(f"| {path_name} | {tamper} | {_rate(value[0], value[1])} |")
    lines.extend(
        [
            "",
            "## PDF editado (B8/P9) — sinais forenses",
            "",
            "| Caminho | PDFs editados | Sinal forense |",
            "|---|---:|---:|",
        ]
    )
    for path_name, value in sorted(aggregate["forensic"].items()):
        lines.append(f"| {path_name} | {value[1]} | {value[0]} |")
    lines.extend(
        [
            "",
            "## Tempo médio por documento",
            "",
            "| Caminho | Segundos/documento |",
            "|---|---:|",
        ]
    )
    for path_name, values in sorted(aggregate["times"].items()):
        lines.append(
            f"| {path_name} | {sum(values) / len(values):.3f} |"
        )
    lines.extend(
        [
            "",
            "## Limitações",
            "",
            "- Os documentos legítimos são consistentes por construção: o gerador usa as "
            "mesmas fórmulas econômicas do domínio, portanto a taxa de falso positivo mede "
            "principalmente o ruído das regras sobre dados sintéticos.",
            "- Os resultados valem para este golden set sintético; não são uma estimativa "
            "de produção.",
            "- O caminho A executa a mesma sequência do router: `run_ocr_prelude` com "
            "provider nativo-primeiro e `pipeline.execute` em thread; agentes de IA são "
            "desligados localmente no script.",
            "- B6/B7/P4 são ataques especializados; a ausência de detecção é esperada.",
            "- B8/P9 não têm detector forense dedicado nesta fase.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(_fix_line(line) for line in lines),
        encoding="utf-8",
    )


async def _evaluate(args: argparse.Namespace) -> None:
    root = Path(args.out)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (root / "records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    CrewAIStage._execute = lambda self, ctx: None
    pipeline = CanonicalPipeline()
    holder = _instrument_stages(pipeline)
    observations: list[Observation] = []

    native_provider = NativeTextFirstOCRProvider(
        primary=_ForbiddenOCRProvider(),
        dpi=200,
        max_pages=10,
        min_native_chars=50,
    )

    selected_native = records[: args.native_limit]
    with __import__("tempfile").TemporaryDirectory(prefix="psi_eval_native_") as temp:
        temp_dir = Path(temp)
        for index, item in enumerate(selected_native):
            observations.append(
                await _native_observation(
                    item, pipeline, native_provider, temp_dir, holder
                )
            )
            if index and index % 100 == 0:
                print(f"native {index}/{len(selected_native)}")

    rendered = manifest.get("files", {})
    selected = [
        item
        for item in records
        if item["id"] in rendered
    ][: args.ocr_limit]
    if selected:
        provider = RemoteOCRProvider(
            url=args.service_url,
            timeout=120,
            engine="tesseract",
        )

        for item in selected:
            variants = rendered[item["id"]]
            for group, names in (
                ("B_ocr_clean", ("scanned_clean", "image_png")),
                ("C_ocr_degraded", ("scanned_rot", "scanned_blur")),
            ):
                for variant in names:
                    file_info = variants.get(variant)
                    if not file_info:
                        continue
                    observations.append(
                        await _ocr_observation(
                            item,
                            variant,
                            Path(file_info),
                            pipeline,
                            provider,
                            group,
                            holder,
                        )
                    )

    dump_path = (
        Path(args.dump)
        if args.dump
        else root / "eval" / "evidence_dump.jsonl"
    )
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    with dump_path.open("w", encoding="utf-8", newline="\n") as handle:
        for observation in observations:
            handle.write(
                json.dumps(
                    _evidence_dump(observation),
                    ensure_ascii=False,
                )
                + "\n"
            )

    aggregate = _aggregate(observations)
    _write_report(
        Path(args.report),
        manifest,
        aggregate,
        min(len(records), args.native_limit),
        args.title,
    )
    print(
        f"report={args.report} dump={dump_path} "
        f"observations={len(observations)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../data/synthetic")
    parser.add_argument(
        "--report",
        default="docs/eval/synthetic_baseline.md",
    )
    parser.add_argument(
        "--title",
        default="Baseline sintético — extração, regras e score",
    )
    parser.add_argument("--dump", default="")
    parser.add_argument("--native-limit", type=int, default=1000)
    parser.add_argument("--ocr-limit", type=int, default=60)
    parser.add_argument(
        "--service-url",
        default="http://127.0.0.1:8010",
    )
    args = parser.parse_args()
    asyncio.run(_evaluate(args))


if __name__ == "__main__":
    main()
