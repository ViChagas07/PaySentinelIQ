from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from typing import Any

from app.core.contracts.evidence import Evidence, Severity
from app.services.scoring.fusion_engine import FusionEngine

DATE_CODES = {
    "BOLETO_OVERDUE",
    "BOLETO_SEVERELY_OVERDUE",
    "BOLETO_VENCIDO",
    "DOCUMENT_EXPIRED",
}
BANK_CODES = {"BANCO_INVALIDO", "BANK_CODE_INVALID", "BOLETO_BANK_MISMATCH"}
LINHA_CODES = {
    "LINHA_DIGITAVEL_FORMATO_INCORRETO",
    "DIGITO_VERIFICADOR_CAMPO1_INVALIDO",
    "DIGITO_VERIFICADOR_CAMPO2_INVALIDO",
    "DIGITO_VERIFICADOR_CAMPO3_INVALIDO",
}
ROUND_CODES = {
    "VALOR_REDONDO_SUSPEITO",
    "BOLETO_ROUND_AMOUNT",
    "ROUND_AMOUNT_SUSPICIOUS",
}

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

FIELD_BY_CODE = {
    "BOLETO_AMOUNT_MISMATCH": ("valor_nominal", "boleto"),
    "BOLETO_DUE_DATE_MISMATCH": ("data_vencimento", "boleto"),
    "BOLETO_BANK_MISMATCH": ("codigo_banco", "boleto"),
    "BOLETO_BARCODE_MISMATCH": ("codigo_barras", "boleto"),
    "BOLETO_GENERAL_DV_INVALID": ("linha_digitavel", "boleto"),
    "BOLETO_DUE_DATE_UNRESOLVABLE": ("linha_digitavel", "boleto"),
    "BOLETO_OVERDUE": ("data_vencimento", "boleto"),
    "BOLETO_SEVERELY_OVERDUE": ("data_vencimento", "boleto"),
    "BOLETO_VENCIDO": ("data_vencimento", "boleto"),
    "BOLETO_ROUND_AMOUNT": ("valor_nominal", "boleto"),
    "ROUND_AMOUNT_SUSPICIOUS": ("valor_nominal", "boleto"),
    "VALOR_REDONDO_SUSPEITO": ("valor_nominal", "boleto"),
    "BANCO_INVALIDO": ("codigo_banco", "boleto"),
    "LINHA_DIGITAVEL_FORMATO_INCORRETO": ("linha_digitavel", "boleto"),
    "DIGITO_VERIFICADOR_CAMPO1_INVALIDO": ("linha_digitavel", "boleto"),
    "DIGITO_VERIFICADOR_CAMPO2_INVALIDO": ("linha_digitavel", "boleto"),
    "DIGITO_VERIFICADOR_CAMPO3_INVALIDO": ("linha_digitavel", "boleto"),
    "PAYSLIP_NET_MISMATCH": ("salario_liquido", "payslip"),
    "PAYSLIP_DEDUCTIONS_INCONSISTENT": ("total_descontos", "payslip"),
    "PAYSLIP_INSS_ABOVE_CEILING": ("inss", "payslip"),
    "PAYSLIP_INSS_MISMATCH": ("inss", "payslip"),
    "PAYSLIP_IRRF_MISMATCH": ("irrf", "payslip"),
    "PAYSLIP_FGTS_MISMATCH": ("fgts", "payslip"),
    "PAYSLIP_BASE_EXCEEDS_GROSS": ("base_inss", "payslip"),
    "PAYSLIP_CPF_INVALID": ("cpf", "payslip"),
    "PAYSLIP_CNPJ_INVALID": ("cnpj", "payslip"),
    "PAYSLIP_PERIOD_FUTURE": ("periodo", "payslip"),
    "PAYSLIP_PERIOD_BEFORE_ADMISSION": ("periodo", "payslip"),
}

GABARITO_KEY = {
    "codigo_banco": "codigo_banco",
    "valor_nominal": "valor_nominal",
    "data_vencimento": "data_vencimento",
    "linha_digitavel": "linha_digitavel",
    "codigo_barras": "codigo_barras",
    "cnpj": "beneficiario_cnpj",
    "cpf": "cpf_funcionario",
    "salario_liquido": "salario_liquido",
    "total_descontos": "total_descontos",
    "inss": "inss",
    "irrf": "irrf",
    "fgts": "fgts",
    "base_inss": "base_inss",
    "periodo": "periodo",
}


def _fold(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"\s+", " ", text).strip().lower()


def _digits(value: Any) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _severity(value: str) -> Severity:
    try:
        return Severity(value)
    except ValueError:
        return Severity.INFO


def _evidence(item: dict) -> Evidence:
    return Evidence(
        code=item.get("code", "UNKNOWN"),
        description=item.get("description", ""),
        severity=_severity(item.get("severity", "info")),
        source=__import__(
            "app.core.contracts.evidence", fromlist=["EvidenceSource"]
        ).EvidenceSource(item.get("source", "heuristic")),
        confidence=float(item.get("confidence", 1.0)),
        category=item.get("category", ""),
        rule_reference=item.get("rule_reference", ""),
        metadata=item.get("metadata") or {},
    )


def _fuse(evidences: list[Evidence]) -> float:
    return float(FusionEngine().fuse(evidences)["final_score"])


def _category_for_codes(codes: set[str]) -> str:
    if any(code.startswith("OCR_") for code in codes):
        return "OCR_QUALITY"
    if codes & DATE_CODES:
        return "DATE_OVERDUE"
    if codes & BANK_CODES:
        return "BANK"
    if codes & LINHA_CODES:
        return "LINHA_FORMAT"
    if codes & ROUND_CODES:
        return "ROUND_AMOUNT"
    if any(code.startswith("PAYSLIP_") for code in codes):
        return "RULE_PAYSLIP"
    if any(code.startswith("BOLETO_") for code in codes):
        return "RULE_BOLETO"
    return "OTHER"


def _decisive_set(
    evidences: list[Evidence],
) -> tuple[list[Evidence], float]:
    if not evidences:
        return [], 0.0
    current = list(evidences)
    score = _fuse(current)
    if score < 70:
        return [], score
    fusion = FusionEngine()
    contributions = fusion._calculate_contributions(current)
    ranked = sorted(
        zip(current, contributions),
        key=lambda pair: pair[1].contribution,
        reverse=True,
    )
    removed: list[Evidence] = []
    for evidence, _contribution in ranked:
        current = [item for item in current if item is not evidence]
        removed.append(evidence)
        score = _fuse(current)
        if score < 70:
            break
    return removed, score


def _normalized(value: Any, kind: str) -> str:
    if kind in {"valor_nominal", "salario_liquido", "total_descontos", "inss",
                "irrf", "fgts", "base_inss", "base_irrf", "base_fgts"}:
        try:
            return f"{float(str(value).replace(',', '.')):.2f}"
        except (TypeError, ValueError):
            return _fold(value)
    if kind in {"linha_digitavel", "codigo_barras", "codigo_banco", "cnpj", "cpf"}:
        return _digits(value)
    if kind == "data_vencimento":
        text = str(value or "")
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match:
            return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"
        return text.strip()
    return _fold(value)


def _cause(
    code: str,
    item: dict,
) -> tuple[str, str, str]:
    mapping = FIELD_BY_CODE.get(code)
    if mapping is None:
        return "OUTRO", "", ""
    field, kind = mapping
    extracted = item["extracted_fields"]
    gabarito = item["gabarito_fields"]
    value = extracted.get(field)
    if value in (None, "", [], {}):
        return "AUSENTE", field, ""
    if field == "codigo_banco" and code == "BANCO_INVALIDO":
        value = extracted.get("codigo_banco") or _digits(
            extracted.get("linha_digitavel")
        )[:3]
    expected_key = GABARITO_KEY.get(field, field)
    if field == "cnpj":
        expected_key = (
            "beneficiario_cnpj"
            if item["document_type"] == "boleto"
            else "cnpj_empregador"
        )
    if field == "periodo":
        expected = str(gabarito.get(expected_key, "")).strip()
    else:
        expected = gabarito.get(expected_key, "")
    if _normalized(value, field) == _normalized(expected, field):
        return "DIVERGENCIA_REAL", field, f"{value!r} vs {expected!r}"
    return "ERRADO", field, f"{value!r} vs {expected!r}"


def _bank_candidates(text: str) -> set[str]:
    candidates: set[str] = set()
    for line in text.splitlines()[:15]:
        candidates.update(
            match.group(1)
            for match in re.finditer(r"\b(\d{3})\s*-\s*\d\b", line)
        )
    candidates.update(
        match.group(1)
        for match in re.finditer(
            r"(?:banco|c[oó]digo\s*(?:do\s*)?banco)\s*:?\s*(\d{3})",
            "\n".join(text.splitlines()[:15]),
            re.IGNORECASE,
        )
    )
    return candidates


def _legit_by_path(dump: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in dump:
        if not item["is_fraud"]:
            grouped[item["path"]].append(item)
    return grouped


def _table_codes(
    legit: dict[str, list[dict]],
) -> list[str]:
    lines = [
        "## a) Códigos de evidência disparados em documentos legítimos",
        "",
        "| Caminho | Código | Documentos | Taxa sobre legítimos | Severidade máxima | Estágio |",
        "|---|---|---:|---:|---|---|",
    ]
    for path_name in sorted(legit):
        items = legit[path_name]
        total = len(items)
        code_docs: Counter[str] = Counter()
        code_severity: dict[str, str] = {}
        code_stage: dict[str, str] = {}
        for item in items:
            for evidence in item["evidences"]:
                code = evidence["code"]
                code_docs[code] += 1
                severity = evidence.get("severity", "info")
                if SEVERITY_ORDER.index(severity) > SEVERITY_ORDER.index(
                    code_severity.get(code, "info")
                ):
                    code_severity[code] = severity
                code_stage.setdefault(code, evidence.get("stage", "unknown"))
        for code, count in sorted(
            code_docs.items(), key=lambda pair: (-pair[1], pair[0])
        ):
            lines.append(
                f"| {path_name} | {code} | {count} | "
                f"{100 * count / total:.1f}% | {code_severity[code]} | "
                f"{code_stage[code]} |"
            )
    lines.append("")
    return lines


def _table_decisive(
    legit: dict[str, list[dict]],
) -> list[str]:
    lines = [
        "## b) Conjunto decisivo dos legítimos com score >= 70",
        "",
        "| Caminho | Documento | Score | Conjunto mínimo decisivo | Categoria |",
        "|---|---|---:|---|---|",
    ]
    category_counts: Counter[tuple[str, str]] = Counter()
    by_language: Counter[tuple[str, str, str]] = Counter()
    by_layout: Counter[tuple[str, str, str]] = Counter()
    by_kind: Counter[tuple[str, str, str]] = Counter()
    for path_name in sorted(legit):
        for item in legit[path_name]:
            if item["score"] < 70:
                continue
            evidences = [_evidence(raw) for raw in item["evidences"]]
            removed, after = _decisive_set(evidences)
            removed_codes = {evidence.code for evidence in removed}
            category = _category_for_codes(removed_codes)
            category_counts[(path_name, category)] += 1
            by_language[(path_name, item["language"], category)] += 1
            by_layout[(path_name, item["layout"], category)] += 1
            by_kind[(path_name, item["document_type"], category)] += 1
            lines.append(
                f"| {path_name} | {item['document_id']} | {item['score']:.1f} | "
                f"{', '.join(sorted(removed_codes)) or '-'} | {category} |"
            )
    lines.extend(
        [
            "",
            "### Contagem por categoria",
            "",
            "| Caminho | Categoria | Legítimos |",
            "|---|---|---:|",
        ]
    )
    for (path_name, category), count in sorted(category_counts.items()):
        lines.append(f"| {path_name} | {category} | {count} |")
    for title, counter in (
        ("por idioma", by_language),
        ("por layout", by_layout),
        ("por tipo de documento", by_kind),
    ):
        lines.extend(
            [
                "",
                f"### Contagem {title}",
                "",
                "| Caminho | Dimensão | Categoria | Legítimos |",
                "|---|---|---|---:|",
            ]
        )
        for (path_name, dimension, category), count in sorted(counter.items()):
            lines.append(
                f"| {path_name} | {dimension} | {category} | {count} |"
            )
    lines.append("")
    return lines


def _table_new_rules(
    legit: dict[str, list[dict]],
) -> list[str]:
    lines = [
        "## c) Causa das evidências BOLETO_* e PAYSLIP_* em legítimos",
        "",
        "| Caminho | Código | Causa | Evidências | Exemplos (ids) | Detalhe |",
        "|---|---|---|---:|---|---|",
    ]
    for path_name in sorted(legit):
        by_code: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        for item in legit[path_name]:
            for evidence in item["evidences"]:
                code = evidence["code"]
                if not (
                    code.startswith("BOLETO_") or code.startswith("PAYSLIP_")
                ):
                    continue
                cause, field, detail = _cause(code, item)
                by_code[code].append((item["document_id"], cause, detail))
        for code in sorted(by_code):
            entries = by_code[code]
            cause_counts = Counter(cause for _id, cause, _detail in entries)
            unique_ids = list(
                dict.fromkeys(
                    document_id for document_id, _cause_name, _detail in entries
                )
            )
            examples = ", ".join(unique_ids[:3])
            detail = entries[0][2]
            lines.append(
                f"| {path_name} | {code} | "
                f"{', '.join(f'{name}:{count}' for name, count in sorted(cause_counts.items()))} | "
                f"{len(entries)} | {examples} | {detail} |"
            )
    lines.append("")
    return lines


def _bank_coverage(
    legit: dict[str, list[dict]],
) -> list[str]:
    lines = [
        "## d) Cobertura do código de banco impresso em boletos legítimos",
        "",
        "| Caminho | Boletos legítimos | Com candidato impresso | Com candidato distinto da linha | % dos boletos |",
        "|---|---:|---:|---:|---:|",
    ]
    for path_name in sorted(legit):
        boletos = [
            item for item in legit[path_name]
            if item["document_type"] == "boleto"
        ]
        with_candidates = 0
        distinct = 0
        for item in boletos:
            candidates = _bank_candidates(item.get("extracted_text", ""))
            if candidates:
                with_candidates += 1
            encoded = _digits(item["gabarito_fields"].get("linha_digitavel"))[:3]
            if any(candidate != encoded for candidate in candidates):
                distinct += 1
        total = len(boletos)
        lines.append(
            f"| {path_name} | {total} | {with_candidates} | {distinct} | "
            f"{(100 * distinct / total if total else 0):.1f}% |"
        )
    lines.append("")
    return lines


def build_report(dump_path: Path, title: str) -> str:
    dump = [
        json.loads(line)
        for line in dump_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    legit = _legit_by_path(dump)
    lines = [
        f"# {title}",
        "",
        "Análise somente leitura sobre o dump de evidências da medição "
        "correspondente.",
        "",
        "Categorias de causa raiz: OCR_QUALITY, DATE_OVERDUE, BANK, "
        "LINHA_FORMAT, RULE_BOLETO, RULE_PAYSLIP, ROUND_AMOUNT, OTHER.",
        "",
    ]
    lines.extend(_table_codes(legit))
    lines.extend(_table_decisive(legit))
    lines.extend(_table_new_rules(legit))
    lines.extend(_bank_coverage(legit))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--title",
        default="Atribuição de falsos positivos (antes da Fase 5B)",
    )
    args = parser.parse_args()
    report = build_report(Path(args.dump), args.title)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out}")


if __name__ == "__main__":
    main()
