# ============================================================
# PaySentinelIQ — PDF Forensic Analysis Tools
# Multi-layer PDF forensics for document tampering detection
# ============================================================

from typing import Any

from langchain_core.tools import tool

# ═══════════════════════════════════════════════════════════════
# Known legitimate payroll system PDF producers (reference)
# ═══════════════════════════════════════════════════════════════

_LEGITIMATE_PAYROLL_PRODUCERS = {
    "totvs": "TOTVS (Protheus/RM/Datasul)",
    "senior": "Senior Sistemas (HCM)",
    "sap": "SAP HCM / SuccessFactors",
    "fortes": "Fortes RH / Domínio Contábil",
    "adp": "ADP Brasil",
    "alterdata": "Alterdata",
    "metadados": "Metadados",
    "iob": "IOB",
    "cenofisco": "Cenofisco",
    "oracle": "Oracle HCM",
    "workday": "Workday",
    "peoplesoft": "PeopleSoft",
    "pontomais": "PontoMais",
    "convenia": "Convenia",
    "gupy": "Gupy",
    "solides": "Sólides",
    "sólides": "Sólides",
}

_SUSPICIOUS_PDF_PRODUCERS = [
    "canva",
    "microsoft word",
    "microsoft print to pdf",
    "wkhtmltopdf",
    "phantomjs",
    "puppeteer",
    "weasyprint",
    "fpdf",
    "tcpdf",
    "dompdf",
    "mpdf",
    "libreoffice",
    "openoffice",
    "smallpdf",
    "ilovepdf",
    "pdf2go",
    "sejda",
    "pdfescape",
    "adobe photoshop",
    "adobe illustrator",
    "corel",
    "gimp",
    "inkscape",
]

_CONSUMER_EDITING_TOOLS = [
    "adobe acrobat",
    "foxit",
    "nitro",
    "pdfelement",
    "pdf-xchange",
    "pdfsam",
    "master pdf",
]


@tool
def pdf_metadata_extractor(
    creator: str = "",
    producer: str = "",
    creation_date: str = "",
    modification_date: str = "",
    pdf_version: str = "",
    page_count: int = 1,
    incremental_save_count: int = 0,
    file_size_bytes: int = 0,
) -> dict[str, Any]:
    """
    Analyze PDF metadata for tampering indicators.
    Checks producer software, date consistency, incremental saves,
    and creation/modification timeline.

    Input:
      - creator: PDF Creator field (from metadata)
      - producer: PDF Producer field (from metadata)
      - creation_date: CreationDate (ISO 8601 or PDF date format)
      - modification_date: ModDate (if different from creation)
      - pdf_version: PDF version (e.g. "1.4", "1.7", "2.0")
      - page_count: Number of pages
      - incremental_save_count: Number of incremental saves detected
      - file_size_bytes: File size in bytes

    Returns: metadata analysis with tampering signals.
    """
    anomalies = []
    risk_score = 0

    # --- Producer Software Analysis ---
    producer_lower = producer.lower() if producer else ""
    creator_lower = creator.lower() if creator else ""

    # Check for suspicious producers
    matched_suspicious = None
    for suspicious in _SUSPICIOUS_PDF_PRODUCERS:
        if suspicious in producer_lower or suspicious in creator_lower:
            matched_suspicious = suspicious
            break

    if matched_suspicious:
        anomalies.append({
            "type": "suspicious_pdf_producer",
            "severity": "high",
            "description": (
                f"PDF gerado por software incomum para documentos institucionais: "
                f"'{producer or creator}'. Produtores legítimos de contracheque incluem "
                f"TOTVS, Senior, SAP, ADP, Fortes."
            ),
            "confidence": 85,
        })
        risk_score += 25

    # Check for consumer PDF editors on institutional docs
    matched_editor = None
    for editor in _CONSUMER_EDITING_TOOLS:
        if editor in producer_lower or editor in creator_lower:
            matched_editor = editor
            break

    if matched_editor and matched_suspicious is None:
        anomalies.append({
            "type": "consumer_editing_tool",
            "severity": "medium",
            "description": (
                f"PDF mostra traços de edição por ferramenta de consumo ({matched_editor}). "
                f"Documentos institucionais devem ser gerados por sistemas de folha de pagamento."
            ),
            "confidence": 75,
        })
        risk_score += 15

    # Check for legitimate producer match
    legitimate_match = None
    for key, name in _LEGITIMATE_PAYROLL_PRODUCERS.items():
        if key in producer_lower or key in creator_lower:
            legitimate_match = name
            break

    # --- Date/Time Analysis ---
    creation_dt = None
    modification_dt = None

    try:
        from datetime import datetime, timezone
        for fmt in [
            "D:%Y%m%d%H%M%S",  # PDF date format
            "%Y-%m-%dT%H:%M:%S",  # ISO 8601 without timezone
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 with timezone
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d",  # Date only
        ]:
            try:
                if creation_date and not creation_dt:
                    creation_dt = datetime.strptime(creation_date.replace("'", "").replace("Z", "+0000"), fmt)
                    if creation_dt.tzinfo is None:
                        creation_dt = creation_dt.replace(tzinfo=timezone.utc)
                if modification_date and not modification_dt:
                    modification_dt = datetime.strptime(modification_date.replace("'", "").replace("Z", "+0000"), fmt)
                    if modification_dt.tzinfo is None:
                        modification_dt = modification_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
    except Exception:
        pass

    if creation_dt and modification_dt:
        delta_hours = (modification_dt - creation_dt).total_seconds() / 3600

        if delta_hours > 24:
            anomalies.append({
                "type": "creation_modification_gap",
                "severity": "medium",
                "description": (
                    f"Intervalo anômalo entre criação ({creation_date}) e "
                    f"modificação ({modification_date}): {delta_hours:.0f} horas. "
                    f"Documentos legítimos são gerados e finalizados em uma única sessão."
                ),
                "confidence": 80,
                "delta_hours": delta_hours,
            })
            risk_score += 20

        if delta_hours > 0.01:  # Any detectable modification after creation
            pass  # Minor mod is normal; already logged if > 24h

        if creation_dt > modification_dt:
            anomalies.append({
                "type": "creation_after_modification",
                "severity": "high",
                "description": (
                    f"Data de criação ({creation_date}) posterior à data de modificação "
                    f"({modification_date}). Linha temporal impossível — indica adulteração de metadados."
                ),
                "confidence": 95,
            })
            risk_score += 30

    # --- Incremental Saves ---
    if incremental_save_count > 0:
        anomalies.append({
            "type": "incremental_saves_detected",
            "severity": "medium" if incremental_save_count <= 2 else "high",
            "description": (
                f"Detectadas {incremental_save_count} gravações incrementais no PDF. "
                f"Documentos originais de folha de pagamento não devem ter histórico de edição. "
                f"Isso indica que o PDF foi aberto e salvo após a geração inicial."
            ),
            "confidence": 85,
            "incremental_saves": incremental_save_count,
        })
        risk_score += 15 * incremental_save_count

    # --- Overall Assessment ---
    return {
        "creator": creator,
        "producer": producer,
        "creation_date": creation_date,
        "modification_date": modification_date,
        "pdf_version": pdf_version,
        "page_count": page_count,
        "incremental_save_count": incremental_save_count,
        "file_size_bytes": file_size_bytes,
        "legitimate_producer": legitimate_match is not None,
        "legitimate_producer_name": legitimate_match,
        "suspicious_producer_detected": matched_suspicious is not None,
        "editing_tool_detected": matched_editor is not None,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "metadata_risk_score": min(risk_score, 100),
        "metadata_verdict": (
            "limpo" if risk_score == 0
            else "baixo_risco" if risk_score < 20
            else "moderado" if risk_score < 40
            else "alto_risco" if risk_score < 60
            else "critico"
        ),
        "confidence": 85,
        "evidence": (
            f"Producer: {producer or 'N/A'} | "
            f"Legítimo: {'Sim (' + legitimate_match + ')' if legitimate_match else 'Não'} | "
            f"Incremental saves: {incremental_save_count} | "
            f"Veredito: {('Limpo' if risk_score == 0 else 'Suspeito (' + str(risk_score) + '/100)')}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# PDF LAYER/FONT/CONTENT ANALYSIS
# ═══════════════════════════════════════════════════════════════

@tool
def pdf_layer_analyzer(
    content_stream_count: int = 1,
    font_inventory: str = "",
    image_object_count: int = 0,
    form_field_count: int = 0,
    has_annotations: bool = False,
    encryption_level: str = "none",
) -> dict[str, Any]:
    """
    Analyze PDF structure for multi-layer content, font inconsistency,
    and image/text overlay — all indicators of manual PDF editing.

    Input:
      - content_stream_count: Number of content stream objects
      - font_inventory: Semicolon-separated list of font families found (e.g. "Helvetica;Arial;TimesNewRoman")
      - image_object_count: Total number of embedded image objects
      - form_field_count: Number of interactive form fields
      - has_annotations: Whether the PDF contains annotations/comments
      - encryption_level: Encryption type if present (e.g. "128-bit AES", "none")

    Returns: layer/structural analysis with tampering signals.
    """
    anomalies = []
    risk_score = 0

    # --- Multi-layer content detection ---
    if content_stream_count > 2:
        anomalies.append({
            "type": "multiple_content_layers",
            "severity": "high",
            "description": (
                f"Detectadas {content_stream_count} camadas de conteúdo no PDF. "
                f"Boletos e contracheques institucionais legítimos são documentos de camada única. "
                f"Múltiplas camadas indicam sobreposição de texto editado sobre o original."
            ),
            "confidence": 85,
        })
        risk_score += 35
    elif content_stream_count > 1:
        anomalies.append({
            "type": "extra_content_layer",
            "severity": "medium",
            "description": (
                f"Detectadas {content_stream_count} camadas de conteúdo. "
                f"Camada extra pode ser texto injetado ou marca d'água."
            ),
            "confidence": 65,
        })
        risk_score += 15

    # --- Font analysis ---
    if font_inventory:
        fonts = [f.strip() for f in font_inventory.split(";") if f.strip()]
        unique_fonts = set(fonts)

        if len(unique_fonts) > 3:
            anomalies.append({
                "type": "font_inconsistency",
                "severity": "medium",
                "description": (
                    f"Detectadas {len(unique_fonts)} famílias de fontes distintas: {unique_fonts}. "
                    f"Documentos institucionais usam tipicamente 1-2 fontes consistentes. "
                    f"Múltiplas fontes indicam texto injetado de fontes diferentes."
                ),
                "confidence": 75,
                "fonts_detected": list(unique_fonts),
            })
            risk_score += 20

        # Check for font mismatches that indicate injection
        # (e.g., Arial mixed with Times — very unusual for a single institutional doc)
        serif_fonts = {"times", "timesnewroman", "times new roman", "courier", "georgia"}
        sans_serif_fonts = {"helvetica", "arial", "verdana", "calibri", "tahoma"}
        found_serif = any(f.lower() in serif_fonts for f in fonts)
        found_sans = any(f.lower() in sans_serif_fonts for f in fonts)

        if found_serif and found_sans and len(unique_fonts) >= 2:
            anomalies.append({
                "type": "mixed_font_families",
                "severity": "high",
                "description": (
                    f"Detectada mescla de fontes serifadas com não-serifadas: {unique_fonts}. "
                    f"Padrão típico de texto injetado sobre documento original."
                ),
                "confidence": 80,
            })
            risk_score += 25

    # --- Image overlay detection ---
    if image_object_count > 0:
        # Images on institutional docs are unusual unless it's a scanned doc
        if image_object_count > 2:
            anomalies.append({
                "type": "excessive_images",
                "severity": "medium",
                "description": (
                    f"Detectadas {image_object_count} imagens embutidas no PDF. "
                    f"Pode indicar logotipos/assinaturas/carimbos copiados da internet."
                ),
                "confidence": 60,
            })
            risk_score += 10

    # --- Form fields ---
    if form_field_count > 0:
        anomalies.append({
            "type": "interactive_form_fields",
            "severity": "low",
            "description": (
                f"Detectados {form_field_count} campos de formulário interativos. "
                f"Contracheques institucionais normalmente não são PDFs preenchíveis."
            ),
            "confidence": 50,
        })
        risk_score += 5

    # --- Annotations (comments, highlights) ---
    if has_annotations:
        anomalies.append({
            "type": "annotations_present",
            "severity": "medium",
            "description": (
                "Anotações/comentários detectados no PDF. "
                "Indica que o documento passou por revisão manual em software de edição."
            ),
            "confidence": 70,
        })
        risk_score += 15

    return {
        "content_stream_count": content_stream_count,
        "font_count": len(set(font_inventory.split(";")) if font_inventory else []),
        "fonts_detected": list(set(font_inventory.split(";") if font_inventory else [])),
        "image_object_count": image_object_count,
        "form_field_count": form_field_count,
        "has_annotations": has_annotations,
        "encryption_level": encryption_level,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "structural_risk_score": min(risk_score, 100),
        "confidence": 80,
        "evidence": (
            f"Camadas: {content_stream_count} | "
            f"Fontes: {len(set(font_inventory.split(';') if font_inventory else []))} | "
            f"Imagens: {image_object_count} | "
            f"Anomalias estruturais: {len(anomalies)}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# IMAGE FORENSIC ANALYZER
# ═══════════════════════════════════════════════════════════════

@tool
def image_forensic_analyzer(
    image_dpi: int = 0,
    image_compression: str = "",
    image_color_profile: str = "",
    text_dpi: int = 0,
    has_jpeg_artifacts: bool = False,
    image_position_x: float = 0.0,
    image_position_y: float = 0.0,
) -> dict[str, Any]:
    """
    Analyze embedded images in PDF for forgery indicators.
    Checks DPI consistency, JPEG artifacts, color profiles,
    and image/text alignment.

    Input:
      - image_dpi: DPI of detected image
      - image_compression: Compression method (e.g. "JPEG", "FlateDecode", "CCITT")
      - image_color_profile: ICC color profile name
      - text_dpi: DPI of surrounding text (for comparison)
      - has_jpeg_artifacts: Whether JPEG compression artifacts are visible
      - image_position_x, image_position_y: Image bounding box coordinates

    Returns: image forensic analysis with forgery signals.
    """
    anomalies = []
    risk_score = 0

    # --- DPI inconsistency ---
    if image_dpi > 0 and text_dpi > 0:
        dpi_ratio = image_dpi / text_dpi if text_dpi > 0 else 1
        if dpi_ratio > 1.5 or dpi_ratio < 0.67:
            anomalies.append({
                "type": "dpi_mismatch",
                "severity": "high",
                "description": (
                    f"DPI da imagem ({image_dpi}) difere significativamente do DPI do texto ({text_dpi}). "
                    f"Isso indica que a imagem foi inserida de fonte externa (ex.: logo copiado da internet) "
                    f"em vez de ser gerada nativamente pelo sistema de folha de pagamento."
                ),
                "confidence": 85,
            })
            risk_score += 25

    # --- JPEG artifact detection ---
    if has_jpeg_artifacts and image_compression:
        anomalies.append({
            "type": "jpeg_artifacts_detected",
            "severity": "medium",
            "description": (
                f"Artefatos de compressão JPEG detectados na imagem ({image_compression}). "
                f"Imagens de logotipos e assinaturas em documentos institucionais devem ser "
                f"vetoriais ou de alta qualidade. Artefatos JPEG indicam imagem baixada da web."
            ),
            "confidence": 80,
        })
        risk_score += 20

    # --- Color profile inconsistency ---
    if image_color_profile and image_color_profile.lower() not in ("srgb", "devicecmyk", "devicergb", ""):
        anomalies.append({
            "type": "unusual_color_profile",
            "severity": "low",
            "description": (
                f"Perfil de cor incomum detectado: '{image_color_profile}'. "
                f"Isso pode indicar que a imagem foi processada em software de edição de imagem "
                f"(Photoshop, GIMP, etc.) antes de ser inserida no PDF."
            ),
            "confidence": 60,
        })
        risk_score += 10

    # --- Position analysis (fractional pixel alignment) ---
    if image_position_x != 0 or image_position_y != 0:
        x_frac = image_position_x % 1
        y_frac = image_position_y % 1
        if (x_frac > 0.01 or y_frac > 0.01):
            anomalies.append({
                "type": "fractional_pixel_position",
                "severity": "low",
                "description": (
                    f"Imagem posicionada em coordenadas fracionárias ({image_position_x:.2f}, {image_position_y:.2f}). "
                    f"Pode indicar posicionamento manual em software de edição."
                ),
                "confidence": 50,
            })
            risk_score += 5

    return {
        "image_dpi": image_dpi,
        "text_dpi": text_dpi,
        "dpi_ratio": round(image_dpi / text_dpi, 2) if text_dpi > 0 else None,
        "image_compression": image_compression,
        "image_color_profile": image_color_profile,
        "has_jpeg_artifacts": has_jpeg_artifacts,
        "position": {"x": image_position_x, "y": image_position_y},
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "image_risk_score": min(risk_score, 100),
        "confidence": 75,
        "evidence": (
            f"DPI imagem: {image_dpi} | DPI texto: {text_dpi} | "
            f"Compressão: {image_compression} | "
            f"Artefatos JPEG: {'Sim' if has_jpeg_artifacts else 'Não'}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# OCR CONFIDENCE & TEXT QUALITY ANALYZER
# ═══════════════════════════════════════════════════════════════

@tool
def ocr_confidence_analyzer(
    overall_confidence: float = 0.0,
    min_character_confidence: float = 0.0,
    low_confidence_regions: int = 0,
    total_text_blocks: int = 0,
    inconsistent_kerning_detected: bool = False,
    resampling_artifacts: bool = False,
) -> dict[str, Any]:
    """
    Analyze OCR confidence scores and text quality for tampering indicators.
    Edited document regions often show degraded OCR confidence due to
    re-rasterization artifacts and inconsistent character rendering.

    Input:
      - overall_confidence: Average per-character OCR confidence (0-100)
      - min_character_confidence: Lowest single-character confidence score
      - low_confidence_regions: Count of regions with confidence < 80%
      - total_text_blocks: Total number of text blocks detected
      - inconsistent_kerning_detected: Whether character spacing varies unexpectedly
      - resampling_artifacts: Whether re-rasterization blurring is detected

    Returns: OCR quality analysis with tampering signals.
    """
    anomalies = []
    risk_score = 0

    # --- Low overall confidence ---
    if overall_confidence < 90:
        anomalies.append({
            "type": "low_ocr_confidence",
            "severity": "medium",
            "description": (
                f"Confiança média de OCR baixa ({overall_confidence:.1f}%). "
                f"Texto do documento pode ter sido re-rasterizado após edição."
            ),
            "confidence": 70,
        })
        risk_score += 15

    # --- Very low character confidence (isolated edited chars) ---
    if min_character_confidence < 60:
        anomalies.append({
            "type": "character_level_low_confidence",
            "severity": "high",
            "description": (
                f"Caracteres isolados com confiança de OCR muito baixa ({min_character_confidence:.1f}%). "
                f"Padrão típico de texto editado manualmente onde a re-renderização degrada a qualidade."
            ),
            "confidence": 80,
        })
        risk_score += 25

    # --- Low confidence regions ratio ---
    if total_text_blocks > 0:
        low_ratio = low_confidence_regions / total_text_blocks
        if low_ratio > 0.3:
            anomalies.append({
                "type": "high_ratio_low_confidence_regions",
                "severity": "high",
                "description": (
                    f"{low_confidence_regions}/{total_text_blocks} ({low_ratio:.0%}) regiões de texto "
                    f"com baixa confiança de OCR. Sugere adulteração generalizada do documento."
                ),
                "confidence": 85,
            })
            risk_score += 30
        elif low_ratio > 0.1:
            anomalies.append({
                "type": "elevated_low_confidence_regions",
                "severity": "medium",
                "description": (
                    f"{low_confidence_regions}/{total_text_blocks} ({low_ratio:.0%}) regiões de baixa confiança. "
                    f"Áreas localizadas podem ter sido editadas."
                ),
                "confidence": 70,
            })
            risk_score += 15

    # --- Kerning inconsistency ---
    if inconsistent_kerning_detected:
        anomalies.append({
            "type": "inconsistent_kerning",
            "severity": "high",
            "description": (
                "Espaçamento entre caracteres inconsistente detectado. "
                "Texto injetado em editores de PDF frequentemente apresenta kerning irregular "
                "que difere do texto original gerado pelo sistema de folha."
            ),
            "confidence": 85,
        })
        risk_score += 25

    # --- Resampling artifacts ---
    if resampling_artifacts:
        anomalies.append({
            "type": "resampling_artifacts",
            "severity": "high",
            "description": (
                "Artefatos de re-amostragem detectados — blurring ou aliasing em regiões de texto. "
                "Indica que o texto foi re-rasterizado, processo que ocorre quando se edita "
                "valores em PDFs e o software re-renderiza a região modificada."
            ),
            "confidence": 85,
        })
        risk_score += 25

    return {
        "overall_confidence": overall_confidence,
        "min_character_confidence": min_character_confidence,
        "low_confidence_regions": low_confidence_regions,
        "total_text_blocks": total_text_blocks,
        "low_confidence_ratio": round(low_confidence_regions / total_text_blocks, 3) if total_text_blocks > 0 else 0,
        "inconsistent_kerning": inconsistent_kerning_detected,
        "resampling_artifacts": resampling_artifacts,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "ocr_risk_score": min(risk_score, 100),
        "confidence": 80,
        "evidence": (
            f"OCR confiança média: {overall_confidence:.1f}% | "
            f"Regiões baixa confiança: {low_confidence_regions}/{total_text_blocks} | "
            f"Kerning: {'Anômalo' if inconsistent_kerning_detected else 'Normal'} | "
            f"Resampling: {'Detectado' if resampling_artifacts else 'Ausente'}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# AI-GENERATED DOCUMENT DETECTOR
# ═══════════════════════════════════════════════════════════════

@tool
def ai_generation_detector(
    text_entropy: float = 0.0,
    numerical_implausibility_score: float = 0.0,
    font_rendering_anomaly: bool = False,
    attention_boundary_artifacts: bool = False,
    inconsistent_baseline: bool = False,
    document_hash_match: str = "",
) -> dict[str, Any]:
    """
    Detect indicators of AI-generated synthetic documents.
    AI-generated payslips and boletos show characteristic patterns
    in text distribution, numerical plausibility, and rendering.

    This is an EMERGING THREAT category — findings carry explicit uncertainty.

    Input:
      - text_entropy: Shannon entropy of OCR-extracted text (higher = more random/less structured)
      - numerical_implausibility_score: How statistically unlikely the salary/deduction combo is (0-1)
      - font_rendering_anomaly: Whether characters appear metrically inconsistent with known fonts
      - attention_boundary_artifacts: Whether text/background boundaries show AI characteristic artifacts
      - inconsistent_baseline: Whether text baseline alignment is inconsistent
      - document_hash_match: Perceptual hash distance from known-authentic templates

    Returns: AI-generation suspicion analysis with explicit uncertainty ranges.
    """
    anomalies = []
    risk_score = 0
    uncertainty_range = (0, 100)  # Will be refined by findings

    # --- Text entropy analysis ---
    # AI-generated text tends to have either very high entropy (random-ish)
    # or unusually low entropy (repetitive patterns)
    if text_entropy > 6.5:
        anomalies.append({
            "type": "high_text_entropy",
            "severity": "medium",
            "description": (
                f"Entropia de texto elevada ({text_entropy:.2f} bits). "
                f"Textos gerados por IA frequentemente apresentam distribuição estatística "
                f"anômala dos tokens. INCERTEZA: ±30%."
            ),
            "confidence": 55,
            "uncertainty": "±30%",
        })
        risk_score += 15
    elif text_entropy < 3.0 and text_entropy > 0:
        anomalies.append({
            "type": "low_text_entropy",
            "severity": "low",
            "description": (
                f"Entropia de texto muito baixa ({text_entropy:.2f} bits). "
                f"Pode indicar texto gerado por template ou IA com padrões repetitivos. "
                f"INCERTEZA: ±35%."
            ),
            "confidence": 45,
        })
        risk_score += 10

    # --- Numerical implausibility ---
    if numerical_implausibility_score > 0.8:
        anomalies.append({
            "type": "numerical_implausibility",
            "severity": "high",
            "description": (
                f"Combinação salário/deduções estatisticamente implausível "
                f"(score: {numerical_implausibility_score:.2f}). "
                f"Modelos de IA frequentemente geram valores financeiros que são "
                f"matematicamente válidos mas estatisticamente improváveis para o cargo/região. "
                f"INCERTEZA: ±25%."
            ),
            "confidence": 65,
        })
        risk_score += 25

    # --- Font rendering anomalies ---
    if font_rendering_anomaly:
        anomalies.append({
            "type": "font_hallucination",
            "severity": "high",
            "description": (
                "Detectados caracteres visualmente similares mas metricamente diferentes "
                "de fontes conhecidas. Modelos de IA geradores de imagem não conseguem "
                "reproduzir fielmente métricas tipográficas. INCERTEZA: ±20%."
            ),
            "confidence": 70,
        })
        risk_score += 25

    # --- Attention boundary artifacts ---
    if attention_boundary_artifacts:
        anomalies.append({
            "type": "attention_boundary_artifacts",
            "severity": "medium",
            "description": (
                "Artefatos de borda de atenção detectados nas transições texto/fundo. "
                "Característico de imagens geradas por IA (diffusion models, GANs). "
                "INCERTEZA: ±30%."
            ),
            "confidence": 55,
        })
        risk_score += 20

    # --- Baseline alignment ---
    if inconsistent_baseline:
        anomalies.append({
            "type": "baseline_inconsistency",
            "severity": "medium",
            "description": (
                "Alinhamento de baseline inconsistente entre blocos de texto. "
                "Documentos gerados por sistemas de folha de pagamento mantêm baseline "
                "perfeito. Desalinhamento sugere montagem sintética. INCERTEZA: ±25%."
            ),
            "confidence": 65,
        })
        risk_score += 20

    # Determine whether AI generation is suspected
    ai_suspected = risk_score >= 30
    uncertainty_range = (max(0, risk_score - 25), min(100, risk_score + 25))

    return {
        "ai_generation_suspected": ai_suspected,
        "ai_risk_score": min(risk_score, 100),
        "uncertainty_range": uncertainty_range,
        "text_entropy": text_entropy,
        "numerical_implausibility_score": numerical_implausibility_score,
        "font_rendering_anomaly": font_rendering_anomaly,
        "attention_boundary_artifacts": attention_boundary_artifacts,
        "inconsistent_baseline": inconsistent_baseline,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "confidence": 50 if ai_suspected else 70,
        "disclaimer": (
            "ATENÇÃO: Detecção de documentos gerados por IA é uma tecnologia emergente. "
            "Todas as conclusões nesta categoria carregam incerteza significativa e devem "
            "ser validadas por um analista humano antes de qualquer decisão."
        ),
        "evidence": (
            f"Entropia: {text_entropy:.2f} | "
            f"Implausibilidade numérica: {numerical_implausibility_score:.2f} | "
            f"Anomalia de fonte: {'Sim' if font_rendering_anomaly else 'Não'} | "
            f"IA suspeita: {'SIM' if ai_suspected else 'Não'} "
            f"(incerteza: ±{uncertainty_range[1] - risk_score:.0f}%)"
        ),
    }
