# ============================================================
# PaySentinelIQ — Document Extraction Service
# Parses OCR text to extract structured fields (CNPJ, CPF,
# amounts, dates, barcode, etc.) using regex patterns.
# ============================================================

from __future__ import annotations

import re
import logging
from typing import Any

from app.services.ocr.models import ExtractionResult, ExtractedField

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """Extracts structured data from raw OCR text using regex pattern matching.

    Handles Brazilian document formats:
    - CNPJ: XX.XXX.XXX/XXXX-XX
    - CPF: XXX.XXX.XXX-XX
    - Monetary values: R$ X.XXX,XX
    - Dates: DD/MM/YYYY
    - Barcodes: FEBRABAN 44-digit format
    - Bank codes: 3-digit codes
    """

    # ── Regex Patterns ──

    CNPJ_PATTERN = re.compile(
        r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b"
        r"|\b(\d{14})\b"  # Raw 14 digits
    )

    CPF_PATTERN = re.compile(
        r"\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b"
        r"|\b(\d{11})\b"  # Raw 11 digits (less reliable)
    )

    # Monetary values: R$ 1.234,56 or 1.234,56 or R$1.234,56
    AMOUNT_PATTERN = re.compile(
        r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})"
    )

    # Dates: DD/MM/YYYY or DD/MM/YY
    DATE_PATTERN = re.compile(
        r"\b(\d{2}/\d{2}/\d{4})\b"
    )

    # FEBRABAN barcode (44 digits, may have spaces/dots)
    BARCODE_PATTERN = re.compile(
        r"\b(\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14})\b"  # Formatted
        r"|\b(\d{47,48})\b"  # Raw barcode (47-48 chars with separators)
    )

    # Linha digitável (47-48 chars, may have dots and spaces)
    LINHA_DIGITAVEL_PATTERN = re.compile(
        r"\b(\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14})\b"
        r"|\b(\d{11}\.\d{1}\s\d{11}\.\d{1}\s\d{11}\.\d{1}\s\d{11}\.\d{1})\b"
        r"|\b(\d{47})\b"
    )

    # Bank code (3 digits, often near "Banco" or "Código")
    BANK_CODE_PATTERN = re.compile(
        r"(?:banco|c[oó]digo\s*(?:do\s*)?banco)\s*:?\s*(\d{3})",
        re.IGNORECASE,
    )

    # Access key (NF-e / CT-e — 44 digits)
    CHAVE_ACESSO_PATTERN = re.compile(
        r"\b(\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4})\b"
        r"|\b(\d{44})\b"
    )

    # PIX key patterns
    PIX_CPF_PATTERN = re.compile(r"\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b")
    PIX_CNPJ_PATTERN = re.compile(r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b")
    PIX_EMAIL_PATTERN = re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b")
    PIX_PHONE_PATTERN = re.compile(r"\b(\+\d{2}\s?\d{2}\s?\d{4,5}-\d{4})\b")

    def extract(self, ocr_text: str) -> ExtractionResult:
        """Extract structured data from OCR text.

        Args:
            ocr_text: Raw text output from OCR engine.

        Returns:
            ExtractionResult with all identified fields.
        """
        result = ExtractionResult()
        fields_found = 0
        total_confidence = 0.0

        # ── CNPJ ──
        cnpj_match = self.CNPJ_PATTERN.search(ocr_text)
        if cnpj_match:
            cnpj_value = cnpj_match.group(1) or cnpj_match.group(2) or ""
            result.cnpj = cnpj_value
            result.raw_fields.append(ExtractedField("cnpj", cnpj_value))
            fields_found += 1
            total_confidence += 0.9  # CNPJ pattern is reliable

        # ── CPF ──
        cpf_match = self.CPF_PATTERN.search(ocr_text)
        if cpf_match:
            cpf_value = cpf_match.group(1) or cpf_match.group(2) or ""
            if not result.cnpj or cpf_value != result.cnpj:  # Don't confuse CPF with CNPJ
                result.cpf = cpf_value
                result.raw_fields.append(ExtractedField("cpf", cpf_value))
                fields_found += 1
                total_confidence += 0.85

        # ── Monetary amounts ──
        amounts = self.AMOUNT_PATTERN.findall(ocr_text)
        if amounts:
            parsed_amounts = []
            for amt_str in amounts:
                try:
                    # Convert Brazilian format: 1.234,56 → 1234.56
                    clean = amt_str.replace(".", "").replace(",", ".")
                    value = float(clean)
                    parsed_amounts.append(value)
                except (ValueError, TypeError):
                    continue
            result.amounts = parsed_amounts

            if parsed_amounts:
                # Heuristic: largest amount is usually gross salary/boleto value
                result.salario_bruto = max(parsed_amounts) if len(parsed_amounts) > 0 else None
                fields_found += 1
                total_confidence += 0.8

        # ── Dates ──
        dates = self.DATE_PATTERN.findall(ocr_text)
        if dates:
            result.dates = list(dates)
            result.data_emissao = dates[0] if dates else None
            result.data_vencimento = dates[-1] if len(dates) > 1 else dates[0] if dates else None
            fields_found += 1
            total_confidence += 0.9

        # ── Barcode / Linha digitável ──
        barcode_match = self.BARCODE_PATTERN.search(ocr_text)
        if barcode_match:
            barcode_value = barcode_match.group(1) or barcode_match.group(2) or ""
            result.codigo_barras = barcode_value

        linha_match = self.LINHA_DIGITAVEL_PATTERN.search(ocr_text)
        if linha_match:
            linha_value = linha_match.group(1) or linha_match.group(2) or linha_match.group(3) or ""
            result.linha_digitavel = linha_value
            result.raw_fields.append(ExtractedField("linha_digitavel", linha_value))
            fields_found += 1
            total_confidence += 0.95

        # ── Bank code ──
        bank_match = self.BANK_CODE_PATTERN.search(ocr_text)
        if bank_match:
            result.codigo_banco = bank_match.group(1)
            result.raw_fields.append(ExtractedField("codigo_banco", bank_match.group(1)))

        # ── Access key (NF-e) ──
        chave_match = self.CHAVE_ACESSO_PATTERN.search(ocr_text)
        if chave_match:
            result.chave_acesso = chave_match.group(1) or chave_match.group(2) or ""
            result.raw_fields.append(ExtractedField("chave_acesso", result.chave_acesso))

        # ── PIX key ──
        for pattern, key_type in [
            (self.PIX_EMAIL_PATTERN, "email"),
            (self.PIX_PHONE_PATTERN, "phone"),
            (self.PIX_CPF_PATTERN, "cpf"),
            (self.PIX_CNPJ_PATTERN, "cnpj"),
        ]:
            pix_match = pattern.search(ocr_text)
            if pix_match:
                result.pix_key = pix_match.group(0)
                result.raw_fields.append(ExtractedField(f"pix_{key_type}", pix_match.group(0)))
                break

        # ── Calculate overall confidence ──
        if fields_found > 0:
            result.extraction_confidence = round(total_confidence / max(fields_found, 1), 4)

        logger.info(
            "Extraction complete: fields=%d cnpj=%s dates=%d amounts=%d confidence=%.2f",
            fields_found,
            result.cnpj or "none",
            len(result.dates),
            len(result.amounts),
            result.extraction_confidence,
        )

        return result

    def enrich_context(
        self,
        extraction: ExtractionResult,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Enrich an existing context dict with extracted fields.

        Only fills in fields that are NOT already present in the context.
        """
        mapping = {
            "cnpj": extraction.cnpj,
            "cpf": extraction.cpf,
            "salario_bruto": extraction.salario_bruto,
            "salario_liquido": extraction.salario_liquido,
            "data_emissao": extraction.data_emissao,
            "data_vencimento": extraction.data_vencimento,
            "linha_digitavel": extraction.linha_digitavel,
            "codigo_barras": extraction.codigo_barras,
            "codigo_banco": extraction.codigo_banco,
            "pix_key": extraction.pix_key,
            "chave_acesso": extraction.chave_acesso,
        }

        for key, value in mapping.items():
            if value and not context.get(key):
                context[key] = value

        return context
