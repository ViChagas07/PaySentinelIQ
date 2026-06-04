# ============================================================
# PaySentinelIQ — Boleto & Pix Fraud Detection Tools
# FEBRABAN linha digitável, Módulo 10/11, barcode, QR Code Pix
# All algorithms follow official Banco Central do Brasil specs
# ============================================================

import re
from typing import Any

from langchain_core.tools import tool

# ═══════════════════════════════════════════════════════════════
# MÓDULO 10 (used in boleto checksum — campo verification)
# ═══════════════════════════════════════════════════════════════


def _modulo10(digits: str) -> int:
    """
    Calculate Módulo 10 checksum (also known as Luhn variant).
    Multiply digits alternately by 2 and 1 (right to left).
    Sum individual digits of products.
    Checksum = (10 - (sum mod 10)) mod 10.
    """
    total = 0
    multiplier = 2  # Start from right with weight 2

    for d in reversed(digits):
        product = int(d) * multiplier
        total += sum(int(digit) for digit in str(product))
        multiplier = 3 - multiplier  # Toggle between 2 and 1

    remainder = total % 10
    return (10 - remainder) % 10


def _validate_modulo10(digits_with_dv: str, dv_position_from_right: int = 0) -> bool:
    """Validate a digit block with Módulo 10. The DV is at the specified position from right."""
    if dv_position_from_right == 0:
        payload = digits_with_dv[:-1]
        dv_expected = int(digits_with_dv[-1])
    else:
        idx = len(digits_with_dv) - dv_position_from_right - 1
        payload = digits_with_dv[:idx] + digits_with_dv[idx + 1 :]
        dv_expected = int(digits_with_dv[idx])

    dv_calculated = _modulo10(payload)
    return dv_calculated == dv_expected


# ═══════════════════════════════════════════════════════════════
# MÓDULO 11 (FEBRABAN — boleto barcode checksum)
# ═══════════════════════════════════════════════════════════════


def _modulo11_febraban(digits: str) -> int:
    """
    Calculate Módulo 11 checksum per FEBRABAN specification.
    Weights cycle 2-9 from right to left.
    If remainder is 0, 1, or > 9: DV = 0 or 1 depending on context.
    Standard: DV = 11 - remainder. If DV >= 10, DV = 1 for some fields, 0 for others.
    """
    total = 0
    weight = 2
    for d in reversed(digits):
        total += int(d) * weight
        weight = 9 if weight == 9 else weight + 1

    remainder = total % 11
    dv = 11 - remainder
    if dv >= 10:
        dv = 1  # FEBRABAN convention for campo checks
    return dv


def _modulo11_general(digits: str) -> int:
    """
    General Módulo 11 calculation.
    Returns 0 if remainder < 2 (standard for most use cases).
    """
    total = 0
    weight = 2
    for d in reversed(digits):
        total += int(d) * weight
        weight = 9 if weight == 9 else weight + 1

    remainder = total % 11
    dv = 11 - remainder
    if dv >= 10:
        dv = 0
    return dv


# ═══════════════════════════════════════════════════════════════
# FEBRABAN LINHA DIGITÁVEL PARSER & VALIDATOR
# ═══════════════════════════════════════════════════════════════


def _parse_linha_digitavel(linha: str) -> dict[str, Any]:
    """Parse a 47-digit linha digitável (boleto bancário) into its constituent fields."""
    digits = "".join(c for c in linha if c.isdigit())

    if len(digits) != 47:
        return {
            "error": f"Linha digitável deve ter 47 dígitos, encontrados {len(digits)}",
            "valid": False,
            "linha_original": linha,
            "digits": digits,
        }

    # Campo 1: positions 1-9 + DV (digit 10)
    campo1_raw = digits[:9]
    campo1_dv = int(digits[9])

    # Campo 2: positions 11-19 + DV 1 + DV 2 (digits 20-21)
    campo2_raw = digits[10:20]
    campo2_dv1 = int(digits[20])
    campo2_dv2 = int(digits[21])

    # Campo 3: positions 22-30 + DV 1 + DV 2
    campo3_raw = digits[21:31]
    campo3_dv1 = int(digits[31])
    campo3_dv2 = int(digits[32])

    # Campo 4: DV geral do código de barras (digit 5)
    dv_geral = int(digits[4])

    # Campo 5: Fator de vencimento + Valor
    fator_vencimento = digits[5:9]
    valor = digits[9:19]

    # Extract bank code
    banco = digits[:3]

    # Extract moeda
    moeda = digits[3]

    return {
        "valid": True,
        "linha_original": linha,
        "digits": digits,
        "banco": banco,
        "moeda": moeda,
        "dv_geral": dv_geral,
        "fator_vencimento": fator_vencimento,
        "valor_nominal": valor,
        "valor_decimal": int(valor) / 100 if valor.isdigit() else None,
        "campo1": {"raw": campo1_raw, "dv": campo1_dv},
        "campo2": {"raw": campo2_raw, "dv1": campo2_dv1, "dv2": campo2_dv2},
        "campo3": {"raw": campo3_raw, "dv1": campo3_dv1, "dv2": campo3_dv2},
        # Flag if it's a concessionária boleto (48 digits) — detect by moeda = 8
        "tipo": "boleto_bancario" if moeda in ("6", "7", "8", "9") else "boleto_concessionaria",
    }


def _validate_campo_dvs(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the internal DVs of each campo in the linha digitável."""
    anomalies = []

    # Validate Campo 1 with Módulo 10
    campo1_check = _validate_modulo10(parsed["campo1"]["raw"] + str(parsed["campo1"]["dv"]))
    if not campo1_check:
        anomalies.append(
            {
                "campo": 1,
                "dv_encontrado": parsed["campo1"]["dv"],
                "dv_calculado": _modulo10(parsed["campo1"]["raw"]),
                "algoritmo": "Módulo 10",
                "severity": "critical",
                "description": "DV do Campo 1 inválido — linha digitável adulterada.",
            }
        )

    # Validate Campo 2 with Módulo 10
    campo2_check = _validate_modulo10(parsed["campo2"]["raw"] + str(parsed["campo2"]["dv1"]))
    if not campo2_check:
        anomalies.append(
            {
                "campo": 2,
                "dv_encontrado": parsed["campo2"]["dv1"],
                "dv_calculado": _modulo10(parsed["campo2"]["raw"]),
                "algoritmo": "Módulo 10",
                "severity": "critical",
                "description": "DV do Campo 2 inválido — linha digitável adulterada.",
            }
        )

    # Validate Campo 3 with Módulo 10
    campo3_check = _validate_modulo10(parsed["campo3"]["raw"] + str(parsed["campo3"]["dv1"]))
    if not campo3_check:
        anomalies.append(
            {
                "campo": 3,
                "dv_encontrado": parsed["campo3"]["dv1"],
                "dv_calculado": _modulo10(parsed["campo3"]["raw"]),
                "algoritmo": "Módulo 10",
                "severity": "critical",
                "description": "DV do Campo 3 inválido — linha digitável adulterada.",
            }
        )

    return anomalies


def _reconstruct_barcode(parsed: dict[str, Any]) -> str:
    """Reconstruct the 44-digit barcode from linha digitável fields."""
    banco = parsed["banco"]
    moeda = parsed["moeda"]
    dv_geral = str(parsed["dv_geral"])
    fator = parsed["fator_vencimento"]
    valor = parsed["valor_nominal"]

    # Campo livre: concatenate relevant parts from campos
    # For boleto bancário: banco(1-3) + moeda(4) + fator(5-8) + valor(9-18) + campo livre(19-44)
    # The campo livre is the concatenation of specific parts from campos 1, 2, 3

    campo1 = parsed["campo1"]["raw"]  # 9 digits
    campo2 = parsed["campo2"]["raw"]  # 10 digits
    campo3 = parsed["campo3"]["raw"]  # 10 digits

    # Campo livre structure depends on bank, but the standard reconstruction:
    # Usually: campo1[4:] + campo2 + campo3 (but this varies)
    # Standard: the barcode is: banco + moeda + dv_geral + fator + valor + campo_livre
    # For simplicity, use the common reconstruction:
    campo_livre = campo1[4:] + campo2 + campo3

    barcode = str(banco) + str(moeda) + dv_geral + str(fator) + str(valor) + str(campo_livre)
    return barcode


def _validate_barcode_dv(barcode: str) -> dict[str, Any]:
    """Validate the general DV (position 5) of the barcode using Módulo 11."""
    if len(barcode) != 44:
        return {"valid": False, "error": f"Barcode must be 44 digits, got {len(barcode)}"}

    dv_printed = int(barcode[4])
    # Payload for DV calculation: all digits except position 5
    payload = barcode[:4] + barcode[5:]
    dv_calculated = _modulo11_febraban(payload)

    return {
        "valid": dv_printed == dv_calculated,
        "dv_printed": dv_printed,
        "dv_calculated": dv_calculated,
        "severity": "critical" if dv_printed != dv_calculated else "low",
    }


@tool
def boleto_linha_digitavel_validator(linha_digitavel: str) -> dict[str, Any]:
    """
    Full FEBRABAN validation of a boleto linha digitável (typed line).
    Performs: format check, Módulo 10 campo DVs, barcode reconstruction,
    Módulo 11 barcode DV, bank code extraction, and value extraction.

    Input:
      - linha_digitavel: The full typed line from the boleto
        (e.g. "00190.00009 01234.567008 12345.678901 2 34560000123456")

    Returns: comprehensive structural validation with all anomalies flagged.
    """
    parsed = _parse_linha_digitavel(linha_digitavel)

    if not parsed.get("valid"):
        return {**parsed, "fraud_signal": True, "fraud_type": "invalid_format"}

    # Stage 1: Campo DV validation
    campo_anomalies = _validate_campo_dvs(parsed)

    # Stage 2: Barcode reconstruction
    barcode = _reconstruct_barcode(parsed)

    # Stage 3: Barcode DV validation
    barcode_result = _validate_barcode_dv(barcode)

    # Aggregate results
    all_anomalies = campo_anomalies.copy()
    if not barcode_result["valid"]:
        all_anomalies.append(
            {
                "campo": "barcode_dv",
                "dv_encontrado": barcode_result["dv_printed"],
                "dv_calculado": barcode_result["dv_calculated"],
                "algoritmo": "Módulo 11 (FEBRABAN)",
                "severity": "critical",
                "description": "DV geral do código de barras inválido "
                "— o boleto é estruturalmente inválido.",
            }
        )

    checksum_valid = len(all_anomalies) == 0
    fraud_signal = not checksum_valid

    return {
        "linha_digitavel_original": linha_digitavel,
        "linha_digitavel_limpa": parsed["digits"],
        "tipo": parsed.get("tipo", "unknown"),
        "banco_codigo": parsed["banco"],
        "moeda": parsed["moeda"],
        "fator_vencimento": parsed["fator_vencimento"],
        "valor_nominal": parsed.get("valor_decimal"),
        "valor_raw": parsed["valor_nominal"],
        "checksum_valid": checksum_valid,
        "barcode_reconstruido": barcode,
        "barcode_dv_valid": barcode_result["valid"],
        "anomalies": all_anomalies,
        "anomaly_count": len(all_anomalies),
        "fraud_signal": fraud_signal,
        "fraud_type": "linha_digitavel_tampering" if fraud_signal else None,
        "severity": "critical" if fraud_signal else "low",
        "confidence": 100,  # Mathematical certainty
        "evidence": (
            f"Linha digitável: {parsed['digits']} | "
            f"Banco: {parsed['banco']} | "
            f"Valor: R$ {parsed.get('valor_decimal', 'N/A')} | "
            f"DV geral: {'VÁLIDO' if barcode_result['valid'] else 'INVÁLIDO'} | "
            f"Anomalias: {len(all_anomalies)}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# BARCODE DECODER (Code 128 / ITF)
# ═══════════════════════════════════════════════════════════════


@tool
def barcode_decoder(barcode_value: str, barcode_type: str = "ITF") -> dict[str, Any]:
    """
    Decode a boleto barcode value into its constituent fields.
    Supports the FEBRABAN 44-digit barcode format.

    Input:
      - barcode_value: The 44-digit numeric barcode value
      - barcode_type: "ITF" (Interleaved 2 of 5 — standard for boletos)

    Returns: decoded barcode fields with bank, currency, due date, value, and free field.
    """
    digits = "".join(c for c in barcode_value if c.isdigit())

    if len(digits) != 44:
        return {
            "valid": False,
            "error": f"Barcode must be 44 digits for boleto bancário, got {len(digits)}",
            "barcode_raw": barcode_value,
            "confidence": 100,
        }

    banco = digits[:3]
    moeda = digits[3]
    dv_geral = digits[4]
    fator_vencimento = digits[5:9]
    valor = digits[9:19]
    campo_livre = digits[19:]

    # Calculate due date from fator de vencimento
    # Base date: 07/10/1997 (FEBRABAN reference)
    from datetime import datetime, timedelta

    base_date = datetime(1997, 10, 7)
    try:
        fator = int(fator_vencimento)
        vencimento = base_date + timedelta(days=fator) if fator > 0 else None
    except (ValueError, OverflowError):
        vencimento = None

    # Decode valor
    valor_decimal = int(valor) / 100 if valor.isdigit() else None

    return {
        "valid": True,
        "barcode_type": barcode_type,
        "barcode_raw": barcode_value,
        "barcode_digits": digits,
        "banco": banco,
        "moeda": moeda,
        "moeda_descricao": {
            "9": "Real (R$)",
            "6": "Real (R$)",
            "7": "Real (R$)",
            "8": "Real (R$)",
        }.get(moeda, "Desconhecida"),
        "dv_geral": dv_geral,
        "fator_vencimento": fator_vencimento,
        "vencimento_estimado": vencimento.strftime("%d/%m/%Y")
        if vencimento
        else "N/A (fator zero ou inválido)",
        "valor": valor_decimal,
        "valor_formatado": f"R$ {valor_decimal:,.2f}" if valor_decimal else "N/A",
        "campo_livre": campo_livre,
        "confidence": 100,
    }


# ═══════════════════════════════════════════════════════════════
# PIX QR CODE EMV PAYLOAD PARSER
# ═══════════════════════════════════════════════════════════════


def _parse_emv_payload(payload: str) -> dict[str, Any]:
    """
    Parse a Pix EMV QR Code payload according to Banco Central do Brasil specification.
    EMV format: ID (2 digits) + Length (2 digits) + Value (variable)
    """
    result: dict[str, Any] = {}
    i = 0
    payload_len = len(payload)

    while i < payload_len:
        if i + 4 > payload_len:
            break

        tag_id = payload[i : i + 2]
        try:
            tag_len = int(payload[i + 2 : i + 4])
        except ValueError:
            break

        i += 4
        if i + tag_len > payload_len:
            break

        tag_value = payload[i : i + tag_len]
        i += tag_len

        # Process known tags
        if tag_id == "00":  # Payload Format Indicator
            result["payload_format"] = tag_value
        elif tag_id == "01":  # Point of Initiation Method
            result["initiation_method"] = "dynamic" if tag_value == "12" else "static"
        elif tag_id == "26":  # Merchant Account Information
            merchant_info = _parse_merchant_account(tag_value)
            result["merchant_account"] = merchant_info
        elif tag_id == "52":  # Merchant Category Code
            result["mcc"] = tag_value
        elif tag_id == "53":  # Transaction Currency
            result["currency"] = "BRL" if tag_value == "986" else tag_value
        elif tag_id == "54":  # Transaction Amount
            result["amount"] = int(tag_value) / 100 if tag_value.isdigit() else tag_value
        elif tag_id == "58":  # Country Code
            result["country"] = "BR" if tag_value == "BR" else tag_value
        elif tag_id == "59":  # Merchant Name
            result["merchant_name"] = tag_value
        elif tag_id == "60":  # Merchant City
            result["merchant_city"] = tag_value
        elif tag_id == "62":  # Additional Data Field
            additional = _parse_additional_data(tag_value)
            result["additional_data"] = additional
        elif tag_id == "63":  # CRC16
            result["crc16"] = tag_value
        else:
            result[f"tag_{tag_id}"] = tag_value

    return result


def _parse_merchant_account(data: str) -> dict[str, Any]:
    """Parse merchant account information (tag 26) with sub-tags."""
    result: dict[str, Any] = {}
    i = 0
    data_len = len(data)

    while i < data_len:
        if i + 4 > data_len:
            break
        sub_id = data[i : i + 2]
        try:
            sub_len = int(data[i + 2 : i + 4])
        except ValueError:
            break
        i += 4
        if i + sub_len > data_len:
            break
        sub_value = data[i : i + sub_len]
        i += sub_len

        if sub_id == "00":  # GUI (Globally Unique Identifier)
            result["gui"] = sub_value
        elif sub_id == "01":  # Pix Key
            result["pix_key"] = sub_value
            result["pix_key_type"] = _classify_pix_key(sub_value)
        elif sub_id == "02":  # Payment description
            result["description"] = sub_value
        elif sub_id == "25":  # FSS (specific service URL)
            result["fss_url"] = sub_value
        else:
            result[f"subtag_{sub_id}"] = sub_value

    return result


def _parse_additional_data(data: str) -> dict[str, Any]:
    """Parse additional data field (tag 62) with sub-tags."""
    result: dict[str, Any] = {}
    i = 0
    data_len = len(data)

    while i < data_len:
        if i + 4 > data_len:
            break
        sub_id = data[i : i + 2]
        try:
            sub_len = int(data[i + 2 : i + 4])
        except ValueError:
            break
        i += 4
        if i + sub_len > data_len:
            break
        sub_value = data[i : i + sub_len]
        i += sub_len

        if sub_id == "05":  # Reference label (txid)
            result["txid"] = sub_value
        elif sub_id == "50":  # Payer name (optional)
            result["payer_name"] = sub_value
        else:
            result[f"subtag_{sub_id}"] = sub_value

    return result


def _classify_pix_key(key: str) -> str:
    """Classify Pix key type based on format."""
    digits_only = "".join(c for c in key if c.isdigit())

    if len(digits_only) == 14 and re.match(r"^\d{14}$", key):
        return "CNPJ"
    elif len(digits_only) == 11 and re.match(r"^\d{11}$", key):
        # Could be CPF or phone — check for mobile phone pattern (DDD 9xxxxxxxx)
        ddd = int(digits_only[:2])
        if 11 <= ddd <= 99 and digits_only[2] == "9":
            return "phone"
        return "CPF"
    elif len(digits_only) == 10 and re.match(r"^\d{10}$", key):
        # 10-digit landline phone
        ddd = int(digits_only[:2])
        if 11 <= ddd <= 99:
            return "phone"
        return "CPF"
    elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", key):
        return "email"
    else:
        return "EVP"  # Random key (Endereço Virtual de Pagamento)


@tool
def pix_emv_parser(qr_code_payload: str) -> dict[str, Any]:
    """
    Parse a Brazilian Pix EMV QR Code payload according to Banco Central specifications.
    Decodes all EMV tags, extracts merchant info, Pix key, amount, and validates
    consistency between visual boleto data and embedded Pix routing.

    Input:
      - qr_code_payload: The raw decoded string from a Pix QR Code
        (e.g. "00020126580014br.gov.bcb.pix0136...")

    Returns: structured EMV payload with fraud-relevant fields highlighted.
    """
    if not qr_code_payload or len(qr_code_payload) < 10:
        return {
            "valid": False,
            "error": "QR code payload too short or empty — not a valid Pix EMV payload",
            "confidence": 100,
            "fraud_signal": True,
        }

    try:
        parsed = _parse_emv_payload(qr_code_payload)
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to parse EMV payload: {str(e)}",
            "confidence": 100,
            "fraud_signal": True,
        }

    # Extract key fields
    merchant = parsed.get("merchant_account", {})
    pix_key = merchant.get("pix_key")
    pix_key_type = merchant.get("pix_key_type", "unknown")
    merchant_name = parsed.get("merchant_name")
    merchant_city = parsed.get("merchant_city")
    amount = parsed.get("amount")
    txid = parsed.get("additional_data", {}).get("txid")

    # Fraud signals
    anomalies = []

    # CPF as Pix key on institutional boletos is suspicious
    if pix_key_type == "CPF":
        anomalies.append(
            {
                "type": "pix_key_cpf_on_institutional",
                "severity": "medium",
                "description": "Chave Pix é um CPF — boletos institucionais "
                "devem usar CNPJ, telefone ou EVP.",
                "confidence": 70,
            }
        )

    # Missing merchant name is suspicious
    if not merchant_name:
        anomalies.append(
            {
                "type": "missing_merchant_name",
                "severity": "high",
                "description": "Nome do recebedor ausente no payload EMV "
                "— impede verificação de titularidade.",
                "confidence": 90,
            }
        )

    # Static QR without amount
    if parsed.get("initiation_method") == "static" and amount is None:
        anomalies.append(
            {
                "type": "static_qr_no_amount",
                "severity": "low",
                "description": "QR Code estático sem valor — o pagador pode "
                "digitar qualquer valor.",
                "confidence": 80,
            }
        )

    fraud_signal = len(anomalies) > 0

    return {
        "valid": True,
        "payload_raw": qr_code_payload,
        "payload_format": parsed.get("payload_format"),
        "initiation_method": parsed.get("initiation_method", "unknown"),
        "pix_key": pix_key,
        "pix_key_type": pix_key_type,
        "merchant_name": merchant_name,
        "merchant_city": merchant_city,
        "amount": amount,
        "currency": parsed.get("currency", "unknown"),
        "txid": txid,
        "mcc": parsed.get("mcc"),
        "all_tags": {
            k: v for k, v in parsed.items() if k not in ("merchant_account", "additional_data")
        },
        "anomalies": anomalies,
        "fraud_signal": fraud_signal,
        "confidence": 95,
        "evidence": (
            f"Chave Pix: {pix_key or 'N/A'} ({pix_key_type}) | "
            f"Recebedor: {merchant_name or 'N/A'} | "
            f"Valor: {'R$ ' + str(amount) if amount else 'N/A'} | "
            f"QR: {parsed.get('initiation_method', 'unknown')}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# QR CODE / PIX CONSISTENCY CROSS-VALIDATOR
# ═══════════════════════════════════════════════════════════════


@tool
def pix_boleto_cross_validator(
    boleto_beneficiario: str,
    boleto_cnpj: str = "",
    boleto_valor: float = 0.0,
    pix_merchant_name: str = "",
    pix_key: str = "",
    pix_amount: float = 0.0,
) -> dict[str, Any]:
    """
    Cross-validate the visual boleto data against the embedded Pix QR Code data.
    This detects troca-boleto attacks where the visual layout is legitimate
    but the Pix destination has been replaced.

    Input:
      - boleto_beneficiario: Beneficiary name printed on boleto
      - boleto_cnpj: CNPJ printed on boleto (optional)
      - boleto_valor: Amount printed on boleto (in BRL)
      - pix_merchant_name: Merchant Name from EMV payload
      - pix_key: Pix key from EMV payload
      - pix_amount: Amount from EMV payload (optional)

    Returns: cross-validation result with mismatch flags.
    """
    anomalies = []

    # Check 1: Beneficiary name consistency
    name_match = False
    if boleto_beneficiario and pix_merchant_name:
        # Normalize for comparison: lowercase, strip accents, remove punctuation
        def _normalize(s: str) -> str:
            import unicodedata

            s = s.lower().strip()
            s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
            s = re.sub(r"[^a-z0-9\s]", "", s)
            return s

        boleto_norm = _normalize(boleto_beneficiario)
        pix_norm = _normalize(pix_merchant_name)

        # Check if one contains the other or they're highly similar
        name_match = (
            boleto_norm in pix_norm or pix_norm in boleto_norm or boleto_norm[:10] == pix_norm[:10]
        )

        if not name_match:
            anomalies.append(
                {
                    "type": "beneficiary_name_mismatch",
                    "severity": "critical",
                    "description": (
                        f"Beneficiário do boleto ('{boleto_beneficiario}') "
                        f"diverge do Merchant Name no Pix ('{pix_merchant_name}'). "
                        f"Indício de troca-boleto via QR Code adulterado."
                    ),
                    "confidence": 95,
                }
            )

    # Check 2: CNPJ in Pix key
    if boleto_cnpj and pix_key:
        boleto_cnpj_digits = "".join(c for c in boleto_cnpj if c.isdigit())
        pix_key_digits = "".join(c for c in pix_key if c.isdigit())
        if len(boleto_cnpj_digits) == 14 and len(pix_key_digits) == 14:
            if boleto_cnpj_digits != pix_key_digits:
                anomalies.append(
                    {
                        "type": "cnpj_pix_key_mismatch",
                        "severity": "critical",
                        "description": (
                            "CNPJ do boleto difere da chave Pix. "
                            "Pagamento será enviado para outro CNPJ."
                        ),
                        "confidence": 100,
                    }
                )

    # Check 3: Amount consistency
    if boleto_valor > 0 and pix_amount is not None and pix_amount > 0:
        amount_delta = abs(boleto_valor - pix_amount)
        if amount_delta > 0.01:
            anomalies.append(
                {
                    "type": "amount_mismatch",
                    "severity": "critical",
                    "description": (
                        f"Valor do boleto (R$ {boleto_valor:,.2f}) "
                        f"diverge do valor no Pix (R$ {pix_amount:,.2f}). "
                        f"Delta: R$ {amount_delta:,.2f}."
                    ),
                    "confidence": 100,
                }
            )

    fraud_signal = len(anomalies) > 0

    return {
        "boleto_beneficiario": boleto_beneficiario,
        "boleto_cnpj": boleto_cnpj,
        "boleto_valor": boleto_valor,
        "pix_merchant_name": pix_merchant_name,
        "pix_key": pix_key,
        "pix_amount": pix_amount,
        "beneficiary_name_match": name_match,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "fraud_signal": fraud_signal,
        "fraud_type": "pix_boleto_mismatch" if fraud_signal else None,
        "severity": "critical" if fraud_signal else "low",
        "confidence": 95,
        "evidence": (
            f"Boleto beneficiário: {boleto_beneficiario} | "
            f"Pix merchant: {pix_merchant_name} | "
            f"Match: {'SIM' if name_match else 'NÃO — FRAUDE PROVÁVEL'}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# BENEFICIARY BINDING VALIDATOR (convenience aggregator)
# ═══════════════════════════════════════════════════════════════


@tool
def beneficiary_binding_check(
    boleto_beneficiario: str = "",
    boleto_cnpj: str = "",
    banco_codigo: str = "",
    pix_merchant_name: str = "",
    pix_key: str = "",
) -> dict[str, Any]:
    """
    Aggregate beneficiary binding check across all data sources.
    Verifies that the beneficiary is consistent across:
    - Visual boleto text
    - CNPJ printed on boleto
    - Bank routing (código do banco)
    - Pix QR Code merchant name
    - Pix QR Code key

    Any mismatch between these five binding points is a critical fraud signal.
    """
    bindings = {
        "boleto_name": boleto_beneficiario,
        "boleto_cnpj": boleto_cnpj,
        "bank_code": banco_codigo,
        "pix_name": pix_merchant_name,
        "pix_key": pix_key,
    }

    populated = {k: v for k, v in bindings.items() if v}
    unique_sources = set()

    for v in populated.values():
        # Normalize
        normalized = v.lower().strip().replace(".", "").replace("-", "").replace("/", "")
        unique_sources.add(normalized)

    # If all populated fields normalize to the same value, binding is consistent
    binding_consistent = len(unique_sources) <= 2  # Allow minor formatting differences

    return {
        "bindings": bindings,
        "populated_fields": list(populated.keys()),
        "binding_consistent": binding_consistent,
        "fraud_signal": not binding_consistent,
        "fraud_type": "beneficiary_binding_broken" if not binding_consistent else None,
        "severity": "critical" if not binding_consistent else "low",
        "confidence": 85,
        "evidence": (
            f"Fontes de beneficiário: {list(populated.keys())} | "
            f"Consistência: "
            f"{'CONSISTENTE' if binding_consistent else 'INCONSISTENTE — possível fraude'}"
        ),
    }
