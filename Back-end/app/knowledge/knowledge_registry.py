"""Central registry of knowledge categories with RAG weights."""

REGISTRY: dict[str, dict] = {
    "regulations/febraban":    {"weight": 1.00, "label": "FEBRABAN Regulations"},
    "regulations/bacen":       {"weight": 0.98, "label": "BACEN Regulations"},
    "regulations/receita_federal": {"weight": 0.95, "label": "Receita Federal"},
    "regulations/coaf":        {"weight": 0.90, "label": "COAF"},
    "regulations/lgpd":        {"weight": 0.70, "label": "LGPD"},
    "document_types/boleto":   {"weight": 0.95, "label": "Boleto Documents"},
    "document_types/pix":      {"weight": 0.95, "label": "PIX Documents"},
    "document_types/holerite": {"weight": 0.90, "label": "Holerite Documents"},
    "document_types/darf":     {"weight": 0.85, "label": "DARF Documents"},
    "document_types/gps":      {"weight": 0.85, "label": "GPS Documents"},
    "document_types/fgts":     {"weight": 0.85, "label": "FGTS Documents"},
    "attack_patterns/boleto_falso":         {"weight": 0.95, "label": "Boleto Falso"},
    "attack_patterns/qr_overlay":           {"weight": 0.95, "label": "QR Overlay"},
    "attack_patterns/beneficiario_divergente": {"weight": 0.90, "label": "Beneficiario Divergente"},
    "attack_patterns/banco_inexistente":    {"weight": 0.95, "label": "Banco Inexistente"},
    "attack_patterns/folha_fraudada":       {"weight": 0.90, "label": "Folha Fraudada"},
    "algorithms":              {"weight": 0.95, "label": "Algorithms"},
    "reference":               {"weight": 0.95, "label": "Reference"},
    "entities":                {"weight": 0.80, "label": "Entities"},
    "examples":                {"weight": 0.75, "label": "Examples"},
    "case_studies/legitimate": {"weight": 0.75, "label": "Legitimate Cases"},
    "case_studies/fraudulent": {"weight": 0.90, "label": "Fraudulent Cases"},
    "case_studies/edge_cases": {"weight": 0.80, "label": "Edge Cases"},
    "rules":                   {"weight": 0.95, "label": "Rules"},
    "glossary":                {"weight": 0.50, "label": "Glossary"},
    "faq":                     {"weight": 0.50, "label": "FAQ"},
}


def get_weight(category: str) -> float:
    return REGISTRY.get(category, {}).get("weight", 0.5)


def get_label(category: str) -> str:
    return REGISTRY.get(category, {}).get("label", category)
