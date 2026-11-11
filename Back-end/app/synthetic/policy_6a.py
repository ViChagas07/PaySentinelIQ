from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from app.synthetic.policy_sim import SEVERITY_WEIGHTS, SOURCE_MULTIPLIERS

FACT_GROUPS = {
    "BOLETO_OVERDUE": "temporal",
    "BOLETO_VENCIDO": "temporal",
    "BOLETO_SEVERELY_OVERDUE": "temporal",
    "DOCUMENT_EXPIRED": "temporal",
    "BOLETO_DUE_DATE_MISMATCH": "temporal",
    "BOLETO_DUE_DATE_UNRESOLVABLE": "temporal",
    "BOLETO_AMOUNT_MISMATCH": "amount",
    "BOLETO_ROUND_AMOUNT": "amount",
    "VALOR_REDONDO_SUSPEITO": "amount",
    "ROUND_AMOUNT_SUSPICIOUS": "amount",
    "BANCO_INVALIDO": "bank",
    "BOLETO_BANK_MISMATCH": "bank",
    "LINHA_DIGITAVEL_FORMATO_INCORRETO": "linha",
    "DIGITO_VERIFICADOR_CAMPO1_INVALIDO": "linha",
    "DIGITO_VERIFICADOR_CAMPO2_INVALIDO": "linha",
    "DIGITO_VERIFICADOR_CAMPO3_INVALIDO": "linha",
    "BOLETO_BARCODE_MISMATCH": "barcode",
    "BOLETO_GENERAL_DV_INVALID": "barcode",
    "BOLETO_CNPJ_MISMATCH": "beneficiary",
    "CNPJ_INVALID_PATTERN": "beneficiary",
    "PAYSLIP_CNPJ_INVALID": "beneficiary",
    "PAYSLIP_CPF_INVALID": "beneficiary",
    "PAYSLIP_NET_MISMATCH": "payslip_net",
    "PAYSLIP_DEDUCTIONS_INCONSISTENT": "payslip_deductions",
    "PAYSLIP_BASE_EXCEEDS_GROSS": "payslip_deductions",
    "PAYSLIP_INSS_MISMATCH": "payslip_inss",
    "PAYSLIP_INSS_ABOVE_CEILING": "payslip_inss",
    "PAYSLIP_IRRF_MISMATCH": "payslip_irrf",
    "PAYSLIP_FGTS_MISMATCH": "payslip_fgts",
    "PAYSLIP_PERIOD_FUTURE": "period",
    "PAYSLIP_PERIOD_BEFORE_ADMISSION": "period",
    "PAYSLIP_TAX_TABLE_UNSUPPORTED": "period",
}

REQUIRED_BOLETO = ("linha_digitavel", "valor_nominal", "data_vencimento")
REQUIRED_PAYSLIP = (
    "salario_bruto",
    "salario_liquido",
    "total_descontos",
    "inss",
    "irrf",
    "fgts",
    "periodo",
)


def _load(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _is_uncertain(evidence: dict[str, Any]) -> bool:
    metadata = evidence.get("metadata") or {}
    return bool(metadata.get("ocr_uncertain"))


def _score(
    evidences: list[dict[str, Any]],
    variant: str,
) -> float:
    selected = evidences
    if variant == "V3":
        selected = [
            evidence
            for evidence in evidences
            if evidence["severity"] not in {"info", "low"}
        ]
    if not selected:
        return 0.0
    weights = dict(SEVERITY_WEIGHTS)
    if variant == "V2":
        weights["high"] = 30.0
    score = 0.0
    critical = 0
    for evidence in selected:
        severity = evidence["severity"]
        source = evidence["source"]
        confidence = float(evidence.get("confidence", 1.0))
        contribution = (
            weights.get(severity, 2.0)
            * SOURCE_MULTIPLIERS.get(source, 1.0)
            * confidence
        )
        if (
            variant == "V4"
            and source == "deterministic"
            and not _is_uncertain(evidence)
        ):
            contribution *= 1.5
        score += round(contribution, 2)
        if severity == "critical":
            critical += 1
    if critical >= 1:
        score = max(score, 70.0)
    if critical >= 3:
        score = max(score, 90.0)
    if critical >= 2:
        score = min(score * 1.2, 100.0)
    return round(min(score, 100.0), 1)


def _required_fields(item: dict[str, Any]) -> tuple[str, ...]:
    return (
        REQUIRED_BOLETO
        if item["document_type"] == "boleto"
        else REQUIRED_PAYSLIP
    )


def _missing_fields(item: dict[str, Any]) -> list[str]:
    extracted = item["extracted_fields"]
    missing = []
    for field in _required_fields(item):
        value = extracted.get(field)
        if value in (None, "", []):
            missing.append(field)
    if extracted.get("data_vencimento_ambiguous"):
        missing.append("data_vencimento_ambiguous")
    if extracted.get("data_vencimento_locale_inconsistent"):
        missing.append("data_vencimento_locale_inconsistent")
    return missing


def v5_decision(item: dict[str, Any]) -> dict[str, Any]:
    confirmed_material: dict[str, str] = {}
    uncertain_material: list[str] = []
    for evidence in item["evidences"]:
        group = FACT_GROUPS.get(evidence["code"], "other")
        severity = evidence["severity"]
        if _is_uncertain(evidence):
            if severity in {"high", "critical"}:
                uncertain_material.append(evidence["code"])
            continue
        if severity in {"high", "critical"}:
            current = confirmed_material.get(group)
            if current is None or (
                severity == "critical" and current != "critical"
            ):
                confirmed_material[group] = severity

    confirmed_critical = [
        group
        for group, severity in confirmed_material.items()
        if severity == "critical"
    ]
    confirmed_high = [
        group
        for group, severity in confirmed_material.items()
        if severity == "high"
    ]
    confirmed_medium_groups = {
        FACT_GROUPS.get(evidence["code"], "other")
        for evidence in item["evidences"]
        if not _is_uncertain(evidence)
        and evidence["severity"] == "medium"
    }
    missing = _missing_fields(item)

    if confirmed_critical or len(confirmed_high) >= 2:
        decision = "HIGH"
    elif confirmed_high or uncertain_material or len(confirmed_medium_groups) >= 2:
        decision = "MEDIUM"
    else:
        decision = "LOW"

    needs_review = bool(
        missing
        or (uncertain_material and not confirmed_critical)
        or (decision == "LOW" and item["path"] != "A_native" and not confirmed_high)
    )

    return {
        "decision": decision,
        "needs_review": needs_review,
        "confirmed_critical": sorted(confirmed_critical),
        "confirmed_high": sorted(confirmed_high),
        "uncertain_material": sorted(uncertain_material),
        "missing_fields": missing,
    }


def _aggregate(rows: list[dict[str, Any]], path_name: str) -> list[dict[str, Any]]:
    selected = [row for row in rows if row["path"] == path_name]
    if path_name == "A_native":
        return selected
    best: dict[str, dict[str, Any]] = {}
    for row in selected:
        current = best.get(row["document_id"])
        if current is None or row["score"] > current["score"]:
            best[row["document_id"]] = row
    return list(best.values())


def _rate(hits: int, total: int) -> str:
    return f"{100 * hits / total:.1f}%" if total else "-"


def build_report(
    rows: list[dict[str, Any]],
    native_note: str,
    ocr_note: str,
) -> str:
    paths = ("A_native", "B_ocr_clean", "C_ocr_degraded")
    lines = [
        "# 6A.4 — Políticas em shadow (V0, V2, V4, V5)",
        "",
        native_note,
        ocr_note,
        "",
        "Nenhuma variante foi ativada. `risk_level`, FusionEngine e API "
        "permanecem inalterados.",
        "",
        "## N por caminho",
        "",
        "| Caminho | N | Legítimos | Adulterados naive/multi |",
        "|---|---:|---:|---:|",
    ]
    for path_name in paths:
        selected = _aggregate(rows, path_name)
        lines.append(
            f"| {path_name} | {len(selected)} | "
            f"{sum(1 for row in selected if not row['is_fraud'])} | "
            f"{sum(1 for row in selected if row['is_fraud'] and row['sophistication'] in {'naive', 'multi'})} |"
        )

    lines.extend(
        [
            "",
            "## Score e decisão por variante",
            "",
            "| Variante | Caminho | Legítimos >=70 | Legítimos >=40 | "
            "Recall naive >=40 | Recall naive >=70 | Recall multi >=40 | "
            "Recall multi >=70 | needs_review | Dados insuficientes |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for variant in ("V0", "V2", "V4"):
        for path_name in paths:
            items = _aggregate(rows, path_name)
            legit = [item for item in items if not item["is_fraud"]]
            naive = [
                item
                for item in items
                if item["is_fraud"]
                and item["sophistication"] in {"naive", "multi"}
            ]
            multi = [
                item
                for item in items
                if item["is_fraud"] and item["sophistication"] == "multi"
            ]
            scores = {item["document_id"]: _score(item["evidences"], variant) for item in items}
            v5 = {item["document_id"]: v5_decision(item) for item in items}
            need = sum(
                v5[item["document_id"]]["needs_review"] for item in items
            )
            insufficient = sum(
                bool(v5[item["document_id"]]["missing_fields"]) for item in items
            )
            lines.append(
                f"| {variant} | {path_name} | "
                f"{sum(scores[item['document_id']] >= 70 for item in legit)}/{len(legit)} "
                f"({_rate(sum(scores[item['document_id']] >= 70 for item in legit), len(legit))}) | "
                f"{sum(scores[item['document_id']] >= 40 for item in legit)}/{len(legit)} "
                f"({_rate(sum(scores[item['document_id']] >= 40 for item in legit), len(legit))}) | "
                f"{sum(scores[item['document_id']] >= 40 for item in naive)}/{len(naive)} "
                f"({_rate(sum(scores[item['document_id']] >= 40 for item in naive), len(naive))}) | "
                f"{sum(scores[item['document_id']] >= 70 for item in naive)}/{len(naive)} "
                f"({_rate(sum(scores[item['document_id']] >= 70 for item in naive), len(naive))}) | "
                f"{sum(scores[item['document_id']] >= 40 for item in multi)}/{len(multi)} "
                f"({_rate(sum(scores[item['document_id']] >= 40 for item in multi), len(multi))}) | "
                f"{sum(scores[item['document_id']] >= 70 for item in multi)}/{len(multi)} "
                f"({_rate(sum(scores[item['document_id']] >= 70 for item in multi), len(multi))}) | "
                f"{need}/{len(items)} | {insufficient}/{len(items)} |"
            )

    lines.extend(
        [
            "",
            "## V5 — decisão explícita (shadow)",
            "",
            "| Caminho | N | HIGH | MEDIUM | LOW | needs_review | Dados insuficientes |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for path_name in paths:
        items = _aggregate(rows, path_name)
        decisions = [v5_decision(item) for item in items]
        lines.append(
            f"| {path_name} | {len(items)} | "
            f"{sum(item['decision'] == 'HIGH' for item in decisions)} | "
            f"{sum(item['decision'] == 'MEDIUM' for item in decisions)} | "
            f"{sum(item['decision'] == 'LOW' for item in decisions)} | "
            f"{sum(item['needs_review'] for item in decisions)} | "
            f"{sum(bool(item['missing_fields']) for item in decisions)} |"
        )

    lines.extend(
        [
            "",
            "### V5 — recall e falsos positivos",
            "",
            "| Caminho | FP MEDIUM+ | FP HIGH | Recall naive MEDIUM+ | Recall naive HIGH | "
            "Recall multi MEDIUM+ | Recall multi HIGH |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for path_name in paths:
        items = _aggregate(rows, path_name)
        legit = [item for item in items if not item["is_fraud"]]
        naive = [
            item
            for item in items
            if item["is_fraud"] and item["sophistication"] in {"naive", "multi"}
        ]
        multi = [
            item
            for item in items
            if item["is_fraud"] and item["sophistication"] == "multi"
        ]

        def count(items_: list[dict[str, Any]], minimum: str) -> int:
            allowed = {"HIGH"} if minimum == "HIGH" else {"HIGH", "MEDIUM"}
            return sum(
                v5_decision(item)["decision"] in allowed for item in items_
            )

        lines.append(
            f"| {path_name} | {count(legit, 'MEDIUM')}/{len(legit)} "
            f"({_rate(count(legit, 'MEDIUM'), len(legit))}) | "
            f"{count(legit, 'HIGH')}/{len(legit)} "
            f"({_rate(count(legit, 'HIGH'), len(legit))}) | "
            f"{count(naive, 'MEDIUM')}/{len(naive)} "
            f"({_rate(count(naive, 'MEDIUM'), len(naive))}) | "
            f"{count(naive, 'HIGH')}/{len(naive)} "
            f"({_rate(count(naive, 'HIGH'), len(naive))}) | "
            f"{count(multi, 'MEDIUM')}/{len(multi)} "
            f"({_rate(count(multi, 'MEDIUM'), len(multi))}) | "
            f"{count(multi, 'HIGH')}/{len(multi)} "
            f"({_rate(count(multi, 'HIGH'), len(multi))}) |"
        )

    reasons: Counter[str] = Counter()
    aggregated = [
        item for path_name in paths for item in _aggregate(rows, path_name)
    ]
    for item in aggregated:
        decision = v5_decision(item)
        if decision["needs_review"]:
            if decision["missing_fields"]:
                reasons["dados_insuficientes"] += 1
            if decision["uncertain_material"]:
                reasons["ocr_incerto"] += 1
            if decision["decision"] == "LOW" and item["path"] != "A_native":
                reasons["ocr_sem_confirmacao"] += 1
    lines.extend(
        [
            "",
            "## Motivos de needs_review",
            "",
            "| Motivo | Ocorrências |",
            "|---|---:|",
            *[f"| {reason} | {count} |" for reason, count in reasons.items()],
            "",
            "## Limitações",
            "",
            "- V4 é uma variante de contribuição (+50% para determinística "
            "confirmada), não uma recomendação.",
            "- V5 é uma decisão por grupos de fato; info/low não confirmam "
            "adulteração e evidência OCR incerta favorece revisão.",
            "- Nenhuma variante foi ligada ao pipeline ou à API.",
            "- O conjunto atual é de desenvolvimento/avaliação; não é holdout.",
            "",
        ]
    )
    return "\n".join(lines)


def _combined_rows(
    native_dump: Path,
    ocr_dump: Path,
) -> list[dict[str, Any]]:
    native = [row for row in _load(native_dump) if row["path"] == "A_native"]
    ocr = [row for row in _load(ocr_dump) if row["path"] != "A_native"]
    return [*native, *ocr]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native",
        default="../data/synthetic/v2.1/eval/evidence_dump.jsonl",
    )
    parser.add_argument(
        "--ocr",
        default="../data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl",
    )
    parser.add_argument(
        "--out",
        default="docs/eval/6a4_policy_shadow.md",
    )
    args = parser.parse_args()
    rows = _combined_rows(Path(args.native), Path(args.ocr))
    report = build_report(
        rows,
        native_note=(
            "Native: dump completo v2.1 (1000 documentos). "
            "N=694 legítimos; adulterados naive/multi conforme dump."
        ),
        ocr_note=(
            "OCR: 6A.3, 112 documentos (40 legítimos), agregados por documento "
            "e path usando a melhor variante; não são 4 observações independentes."
        ),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out} rows={len(rows)}")


if __name__ == "__main__":
    main()
