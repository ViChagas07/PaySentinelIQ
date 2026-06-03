# ============================================================
# PaySentinelIQ — AI Agent Tools
# LangChain tools for fraud detection pipeline
# ============================================================

from app.ai_agents.tools.custom_tools import (
    analyze_metadata_integrity,
    analyze_payroll_discrepancy,
    check_tax_id_format,
)

from app.ai_agents.tools.brazil_financial_tools import (
    bacen_bank_validator,
    cbo_salary_range,
    cnae_compatibility_check,
    cnpj_validator,
    fgts_calculator,
    inss_calculator,
    irrf_calculator,
    liquido_consistency_check,
)

from app.ai_agents.tools.boleto_tools import (
    barcode_decoder,
    beneficiary_binding_check,
    boleto_linha_digitavel_validator,
    pix_boleto_cross_validator,
    pix_emv_parser,
)

from app.ai_agents.tools.pdf_forensic_tools import (
    ai_generation_detector,
    image_forensic_analyzer,
    ocr_confidence_analyzer,
    pdf_layer_analyzer,
    pdf_metadata_extractor,
)

__all__ = [
    # Custom/base tools
    "analyze_payroll_discrepancy",
    "check_tax_id_format",
    "analyze_metadata_integrity",
    # Brazilian financial
    "cnpj_validator",
    "inss_calculator",
    "irrf_calculator",
    "fgts_calculator",
    "liquido_consistency_check",
    "cbo_salary_range",
    "cnae_compatibility_check",
    "bacen_bank_validator",
    # Boleto/Pix
    "boleto_linha_digitavel_validator",
    "barcode_decoder",
    "pix_emv_parser",
    "pix_boleto_cross_validator",
    "beneficiary_binding_check",
    # PDF forensics
    "pdf_metadata_extractor",
    "pdf_layer_analyzer",
    "image_forensic_analyzer",
    "ocr_confidence_analyzer",
    "ai_generation_detector",
]
