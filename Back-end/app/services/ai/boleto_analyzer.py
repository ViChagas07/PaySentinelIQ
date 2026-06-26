# ============================================================
# PaySentinelIQ — 4-Stage Boleto Fraud Analysis Pipeline
# ============================================================
# CAUSA 2 FIX: Replaces single generic LLM analysis with a
# 4-stage pipeline that combines deterministic rules,
# LLM semantic analysis, FEBRABAN checksum validation,
# and weighted risk scoring.
#
# CRITICAL: Stage 1 (deterministic) runs BEFORE the LLM and
# carries 50% weight. Stage 2 (LLM semantic) carries 35%.
# Stage 3 (linha digitavel validation) carries 15%.
# This ensures the LLM cannot override hard mathematical
# evidence of fraud.
# ============================================================

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# Valid BACEN bank codes (ISPB registry)
# ────────────────────────────────────────────────────────────
BANCOS_VALIDOS: set[str] = {
    "001",  # Banco do Brasil
    "033",  # Santander
    "104",  # Caixa Econômica Federal
    "237",  # Bradesco
    "341",  # Itaú
    "356",  # Banco Real (merged into Santander)
    "389",  # Banco Mercantil do Brasil
    "399",  # HSBC (merged into Bradesco)
    "422",  # Banco Safra
    "453",  # Banco Rural
    "633",  # Banco Rendimento
    "652",  # Itaú Unibanco
    "745",  # Banco Citibank
    "748",  # Sicredi
    "756",  # Sicoob
    "077",  # Banco Inter
    "212",  # Banco Original
    "290",  # PagSeguro
    "318",  # Banco BMG
    "336",  # Banco C6
    "380",  # PicPay
    "383",  # Banco BS2
    "394",  # Banco Mercantil
    "197",  # Stone
    "403",  # Cora
    "412",  # Banco Capital
    "623",  # Banco PAN
    "655",  # Banco Votorantim
    "707",  # Banco Daycoval
    "739",  # Banco Cetelem
    "743",  # Banco Semear
    "746",  # Banco Modal
    "208",  # BTG Pactual
    "246",  # Banco ABC Brasil
    "254",  # Paraná Banco
    "260",  # Nu Pagamentos (Nubank)
    "265",  # Banco Fator
    "300",  # Banco de La Nacion Argentina
    "321",  # Banco Alfa
    "340",  # Banco XP
    "364",  # Geracao Futuro
    "370",  # Banco Mizuho
    "376",  # Banco J.P. Morgan
    "473",  # Banco Caixa Geral
    "505",  # Banco Credit Suisse
    "600",  # Banco Luso Brasileiro
    "604",  # Banco Industrial do Brasil
    "610",  # Banco VR
    "611",  # Banco Paulista
    "613",  # Banco Opportunity
}


def _validate_mod10(digits: str) -> bool:
    """Validate FEBRABAN modulo 10 check digit.

    Used for linha digitavel campo verification (standard BACEN algorithm).
    """
    if len(digits) < 2:
        return False
    payload, check_digit = digits[:-1], int(digits[-1])
    total = 0
    multiplier = 2
    for d in reversed(payload):
        product = int(d) * multiplier
        total += product // 10 + product % 10
        multiplier = 1 if multiplier == 2 else 2
    calculated = (10 - (total % 10)) % 10
    return calculated == check_digit


# ────────────────────────────────────────────────────────────
# STAGE 1: Deterministic Structural Validation
# ────────────────────────────────────────────────────────────

def _stage1_structural_validation(pdf_text: str) -> tuple[list[str], float]:
    """Deterministic boleto validation rules — NO LLM, pure Python.

    Checks bank code, overdue dates, illegal fees, invalid CNPJ patterns.
    These are mathematical/regulatory certainties that don't need AI.
    """
    structural_flags: list[str] = []
    score = 0.0

    # ── 1a. Bank code validation ──
    # Look for the first 3 digits of a linha digitavel pattern
    banco_match = re.search(r"\b(\d{3})\d\.", pdf_text)
    if banco_match:
        codigo_banco = banco_match.group(1)
        if codigo_banco not in BANCOS_VALIDOS:
            structural_flags.append(
                f"BANCO_INVALIDO: código {codigo_banco} não existe no BACEN"
            )
            score += 35  # CRITICAL weight
            logger.warning("Invalid bank code detected: %s", codigo_banco)

    # Also try looking for "Banco" label near a 3-digit code
    banco_label_match = re.search(
        r"(?:banco|c[oó]digo\s*(?:do\s*)?banco)\s*:?\s*(\d{3})",
        pdf_text,
        re.IGNORECASE,
    )
    if banco_label_match:
        codigo_label = banco_label_match.group(1)
        if codigo_label not in BANCOS_VALIDOS:
            flag = f"BANCO_INVALIDO: código {codigo_label} rotulado não existe no BACEN"
            if flag not in structural_flags:
                structural_flags.append(flag)
                score += 35

    # ── 1b. Overdue detection ──
    date_patterns = re.findall(r"\b(\d{2})/(\d{2})/(\d{4})\b", pdf_text)
    today = date.today()
    for d, m, y in date_patterns:
        try:
            doc_date = date(int(y), int(m), int(d))
            days_overdue = (today - doc_date).days
            if days_overdue > 365:
                structural_flags.append(
                    f"BOLETO_VENCIDO: vencimento {d}/{m}/{y} "
                    f"({days_overdue} dias atrás — mais de 1 ano)"
                )
                score += 30
            elif days_overdue > 30:
                structural_flags.append(
                    f"BOLETO_VENCIDO: vencimento {d}/{m}/{y} "
                    f"({days_overdue} dias atrás)"
                )
                score += 20
        except ValueError:
            pass

    # ── 1c. Illegal fees ──
    # Multa > 2% ao dia (legal limit: 2% total)
    multa_match = re.search(
        r"multa[^\d]*(\d+[\.,]?\d*)\s*%\s*(ao\s*dia|por\s*dia)",
        pdf_text,
        re.IGNORECASE,
    )
    if multa_match:
        try:
            pct = float(multa_match.group(1).replace(",", "."))
            if pct > 2.0:
                structural_flags.append(
                    f"MULTA_ILEGAL: {pct}% ao dia (limite legal: 2% total)"
                )
                score += 25
        except ValueError:
            pass

    # Juros > 1% ao mês (legal limit: 1% ao mês)
    juros_match = re.search(
        r"juros[^\d]*(\d+[\.,]?\d*)\s*%\s*(ao\s*m[eê]s|por\s*m[eê]s)",
        pdf_text,
        re.IGNORECASE,
    )
    if juros_match:
        try:
            pct = float(juros_match.group(1).replace(",", "."))
            if pct > 1.0:
                structural_flags.append(
                    f"JUROS_ABUSIVOS: {pct}% ao mês (limite legal: 1% ao mês)"
                )
                score += 20
        except ValueError:
            pass

    # ── 1d. Invalid CNPJ patterns ──
    cnpj_matches = re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", pdf_text)
    known_invalid_cnpjs = {
        "00000000000000",
        "11111111111111",
        "22222222222222",
        "33333333333333",
        "44444444444444",
        "55555555555555",
        "66666666666666",
        "77777777777777",
        "88888888888888",
        "99999999999999",
        "00000010000199",  # Common fake pattern
        "00000000000199",  # 00.000.000/0001-99 variant
        "12345678901234",  # Sequential
        "01234567890123",  # Sequential variant
    }
    for cnpj in cnpj_matches:
        digits = re.sub(r"\D", "", cnpj)
        if digits in known_invalid_cnpjs:
            structural_flags.append(f"CNPJ_INVALIDO: {cnpj} (padrão inválido)")
            score += 30

    # Also check for raw 14-digit numbers that look like invalid CNPJs
    raw_14 = re.findall(r"\b(\d{14})\b", pdf_text)
    for digits in raw_14:
        if digits in known_invalid_cnpjs:
            # Check if this 14-digit string isn't already covered by formatted CNPJ
            if not any(digits in re.sub(r"\D", "", c) for c in cnpj_matches):
                structural_flags.append(
                    f"CNPJ_INVALIDO: {digits} (14 dígitos — padrão inválido)"
                )
                score += 30

    # ── 1e. Suspiciously round amounts ──
    amount_matches = re.findall(
        r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})", pdf_text
    )
    for amt_str in amount_matches:
        try:
            clean = amt_str.replace(".", "").replace(",", ".")
            value = float(clean)
            # Very round numbers (e.g., R$ 500,00) are suspicious
            if value >= 100 and value % 100 == 0:
                structural_flags.append(
                    f"VALOR_REDONDO_SUSPEITO: R$ {amt_str}"
                )
                score += 10
                break  # One is enough
        except ValueError:
            pass

    return structural_flags, min(score, 100.0)


# ────────────────────────────────────────────────────────────
# STAGE 2: LLM Semantic Analysis
# ────────────────────────────────────────────────────────────

def _build_stage2_prompt(pdf_text: str, structural_flags: list[str]) -> str:
    """Build the skeptical LLM prompt for boleto semantic analysis."""
    flags_text = (
        "\n".join(f"  - {f}" for f in structural_flags)
        if structural_flags
        else "Nenhum detectado ainda"
    )

    return f"""Você é um especialista em detecção de fraude em boletos bancários brasileiros,
operado pelo PaySentinelIQ. Seu viés padrão é CÉTICO: quando houver dúvida,
classifique como SUSPEITO.

CONTEXTO CRÍTICO:
- Fraudes em boletos causam perdas financeiras reais e irreversíveis
- Um FALSO NEGATIVO (deixar passar fraude) é MUITO MAIS GRAVE que um falso positivo
- Portanto: em caso de dúvida, classifique como HIGH RISK

INDICADORES DE ALTA SUSPEITA (trate como CRÍTICO):
- Banco com código não reconhecido ou inexistente
- CNPJ do beneficiário com padrão inválido (todos dígitos iguais, zeros, etc.)
- Data de vencimento passada há mais de 30 dias
- Linha digitável com dígitos verificadores incorretos
- Multa superior a 2% do valor ou juros superiores a 1% ao mês
- Razão social do beneficiário genérica (ex: "Soluções Rápidas", "Digital LTDA")
- Valores muito redondos sem discriminação de serviço
- Cobranças de taxas sem respaldo legal (taxa de emissão, taxa administrativa)
- Código de barras que não corresponde à linha digitável
- Ausência de informações do cedente (endereço, contato oficial)

REGRA DE CLASSIFICAÇÃO:
- SE DETECTAR 2 OU MAIS DESTES INDICADORES: classifique como HIGH RISK (score >= 75)
- SE DETECTAR 1 INDICADOR CRÍTICO (banco inválido, CNPJ inválido, linha inválida):
  classifique como HIGH RISK independente de outros fatores

TEXTO DO BOLETO:
{pdf_text}

INDICADORES JÁ DETECTADOS AUTOMATICAMENTE (não repita estes):
{flags_text}

ANALISE especificamente:
1. Nome/razão social do beneficiário (empresa fantasma? nome genérico suspeito?)
2. Endereço ou ausência de endereço completo
3. Coerência entre cedente, banco e carteira
4. Campo de instruções contendo cobranças não previstas em lei
5. Valor do documento (número redondo suspeito? muito alto sem justificativa?)
6. Autenticidade do nosso número e carteira
7. Qualquer texto que pareça pressionar ou enganar o pagador
8. Presença de QR Code Pix adulterado ou inconsistente

RESPONDA SOMENTE em JSON válido, sem texto antes ou depois:
{{
  "indicadores_semanticos": ["lista", "de", "indicadores", "encontrados"],
  "score_semantico": <número de 0 a 100 indicando suspeita>,
  "analise_beneficiario": "<análise do beneficiário>",
  "elementos_suspeitos": ["elemento1", "elemento2"],
  "confianca": <número de 0 a 1>
}}"""


async def _stage2_semantic_analysis(
    pdf_text: str, structural_flags: list[str], llm_generate_fn: Any
) -> dict[str, Any]:
    """Run LLM semantic analysis on the boleto text."""
    try:
        prompt = _build_stage2_prompt(pdf_text, structural_flags)
        raw_response = await llm_generate_fn(prompt)

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {}

        # Validate and sanitize
        score = result.get("score_semantico", 0)
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            score = 0

        return {
            "indicadores_semanticos": result.get("indicadores_semanticos", []),
            "score_semantico": float(score),
            "analise_beneficiario": result.get("analise_beneficiario", ""),
            "elementos_suspeitos": result.get("elementos_suspeitos", []),
            "confianca": result.get("confianca", 0.8),
        }
    except Exception as e:
        logger.warning("Stage 2 LLM semantic analysis failed: %s", e)
        return {
            "indicadores_semanticos": [],
            "score_semantico": 0,
            "analise_beneficiario": "LLM analysis unavailable",
            "elementos_suspeitos": [],
            "confianca": 0.0,
        }


# ────────────────────────────────────────────────────────────
# STAGE 3: Linha Digitavel FEBRABAN Validation
# ────────────────────────────────────────────────────────────

def _stage3_linha_digitavel_validation(pdf_text: str) -> tuple[list[str], float]:
    """Validate linha digitavel using BACEN modulo 10 algorithm."""
    linha_flags: list[str] = []
    score = 0.0

    # Pattern: 5.5 6.6 6.6 D 14 — standard FEBRABAN formatted linha digitavel
    linha_pattern = re.search(
        r"(\d{5}\.\d{5})\s+(\d{6}\.\d{6})\s+(\d{6}\.\d{6})\s+(\d)\s+(\d{14})",
        pdf_text,
    )

    if linha_pattern:
        # Validate campo 1 (modulo 10)
        campo1 = re.sub(r"\D", "", linha_pattern.group(1))
        if campo1 and not _validate_mod10(campo1):
            linha_flags.append("DIGITO_VERIFICADOR_CAMPO1_INVALIDO")
            score += 30
            logger.warning("Linha digitavel campo 1 modulo 10 validation FAILED")

        # Validate campo 2 (modulo 10)
        campo2 = re.sub(r"\D", "", linha_pattern.group(2))
        if campo2 and not _validate_mod10(campo2):
            linha_flags.append("DIGITO_VERIFICADOR_CAMPO2_INVALIDO")
            score += 30

        # Validate campo 3 (modulo 10)
        campo3 = re.sub(r"\D", "", linha_pattern.group(3))
        if campo3 and not _validate_mod10(campo3):
            linha_flags.append("DIGITO_VERIFICADOR_CAMPO3_INVALIDO")
            score += 30
    else:
        # Check if there's a partially-formatted linha digitavel
        if re.search(r"\d{5}[\s\.]\d{5}", pdf_text):
            linha_flags.append("LINHA_DIGITAVEL_FORMATO_INCORRETO")
            score += 25

    return linha_flags, min(score, 100.0)


# ────────────────────────────────────────────────────────────
# STAGE 4: Final Scoring and Classification
# ────────────────────────────────────────────────────────────

def _stage4_final_scoring(
    structural_score: float,
    semantic_score: float,
    linha_score: float,
    structural_flags: list[str],
    semantic_result: dict[str, Any],
    linha_flags: list[str],
) -> dict[str, Any]:
    """Combine all stage scores with calibrated weights into final risk assessment."""

    # Weighted scoring:
    # - 50%: deterministic structural rules (mathematical certainty)
    # - 35%: LLM semantic analysis
    # - 15%: linha digitavel validation
    score_final = min(
        (structural_score * 0.50) + (semantic_score * 0.35) + (linha_score * 0.15),
        100.0,
    )

    all_flags = (
        structural_flags
        + semantic_result.get("indicadores_semanticos", [])
        + semantic_result.get("elementos_suspeitos", [])
        + linha_flags
    )

    # Classification with calibrated thresholds
    if score_final >= 70:
        risk_level = "HIGH"
        is_fraudulent = True
        recommendation = (
            "REJEITAR: Alta probabilidade de fraude. Não efetue o pagamento. "
            "Escale para o time de compliance imediatamente."
        )
    elif score_final >= 40:
        risk_level = "MEDIUM"
        is_fraudulent = False
        recommendation = (
            "REVISAR: Anomalias detectadas. Requisitar confirmação do "
            "beneficiário e validar dados cadastrais antes de pagar."
        )
    else:
        risk_level = "LOW"
        is_fraudulent = False
        recommendation = (
            "APROVADO: Nenhum indicador crítico de fraude detectado. "
            "Verificar manualmente em caso de valor elevado."
        )

    return {
        "risk_score": round(score_final),
        "risk_level": risk_level,
        "fraud_probability": round(score_final / 100, 4),
        "is_fraudulent": is_fraudulent,
        "confidence_score": semantic_result.get("confianca", 0.8),
        "fraud_indicators": all_flags,
        "total_indicators": len(all_flags),
        "pipeline_stages": 4,
        "recommendation": recommendation,
        "stage_details": {
            "etapa_1_estrutural": {
                "flags": structural_flags,
                "score_parcial": structural_score,
            },
            "etapa_2_semantica": semantic_result,
            "etapa_3_linha_digitavel": {
                "flags": linha_flags,
                "score_parcial": linha_score,
            },
        },
    }


# ────────────────────────────────────────────────────────────
# MAIN PIPELINE ENTRY POINT
# ────────────────────────────────────────────────────────────

async def analyze_boleto_pipeline(
    pdf_text: str,
    llm_generate_fn: Any | None = None,
) -> dict[str, Any]:
    """4-stage boleto fraud analysis pipeline.

    This replaces the previous single-generic-LLM-call approach that
    produced false negatives (Risco 6/100 for 9 fraud indicators).

    Stage weights:
        Stage 1 (Deterministic): 50% — mathematical/regulatory certainty
        Stage 2 (LLM Semantic):   35% — AI pattern recognition
        Stage 3 (Linha Digitavel): 15% — FEBRABAN checksum validation

    Args:
        pdf_text: Extracted text from the boleto PDF.
        llm_generate_fn: Async function(prompt: str) -> str for LLM calls.
                         If None, Stage 2 is skipped and scored as 0.

    Returns:
        Dict with risk_score, risk_level, fraud_indicators, etc.
    """
    logger.info("Starting 4-stage boleto fraud analysis pipeline")

    # ── Stage 1: Deterministic Structural Validation ──
    logger.info("[Stage 1/4] Deterministic Structural Validation")
    structural_flags, structural_score = _stage1_structural_validation(pdf_text)
    logger.info(
        "Stage 1 complete: flags=%d score=%.1f",
        len(structural_flags),
        structural_score,
    )

    # ── Stage 2: LLM Semantic Analysis ──
    logger.info("[Stage 2/4] LLM Semantic Analysis")
    if llm_generate_fn is not None:
        semantic_result = await _stage2_semantic_analysis(
            pdf_text, structural_flags, llm_generate_fn
        )
    else:
        logger.warning("No LLM function provided — skipping semantic analysis")
        semantic_result = {
            "indicadores_semanticos": [],
            "score_semantico": 0,
            "analise_beneficiario": "LLM não disponível",
            "elementos_suspeitos": [],
            "confianca": 0.0,
        }
    semantic_score = semantic_result.get("score_semantico", 0)
    logger.info(
        "Stage 2 complete: indicators=%d score=%.1f",
        len(semantic_result.get("indicadores_semanticos", [])),
        semantic_score,
    )

    # ── Stage 3: Linha Digitavel Validation ──
    logger.info("[Stage 3/4] FEBRABAN Linha Digitavel Validation")
    linha_flags, linha_score = _stage3_linha_digitavel_validation(pdf_text)
    logger.info("Stage 3 complete: flags=%d score=%.1f", len(linha_flags), linha_score)

    # ── Stage 4: Final Scoring ──
    logger.info("[Stage 4/4] Final Risk Scoring")
    result = _stage4_final_scoring(
        structural_score=structural_score,
        semantic_score=semantic_score,
        linha_score=linha_score,
        structural_flags=structural_flags,
        semantic_result=semantic_result,
        linha_flags=linha_flags,
    )

    logger.info(
        "Boleto pipeline complete: risk=%.0f/100 level=%s indicators=%d",
        result["risk_score"],
        result["risk_level"],
        result["total_indicators"],
    )

    return result
