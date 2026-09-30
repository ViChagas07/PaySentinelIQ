# ============================================================
# PaySentinelIQ — Mock LLM Provider (Demo/Interview Mode)
# Instant, deterministic responses — zero dependencies, zero latency.
# Use DEMO_MODE=true in .env to activate.
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Any

from app.providers.base import BaseLLMProvider, LLMConfig, ProviderInfo

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """
    Mock provider for demos, interviews, and CI/CD.

    Returns realistic-looking structured JSON responses instantly
    without calling any LLM. Perfect for:
    - Job interview demos (smooth, no waiting)
    - CI/CD pipelines (fast, deterministic)
    - Development without Ollama running
    """

    # Pre-canned responses by agent type
    _RESPONSES = {
        "fraud": {
            "febraban_compliance": {
                "bank_valid": True,
                "checksum_valid": True,
                "due_date_valid": True,
                "fees_legal": True,
                "cnpj_valid": True,
                "pix_match": True,
                "barcode_match": True
            },
            "additional_indicators": [
                "Análise comportamental: padrão de envio fora do horário comercial"
            ],
            "fraud_patterns": ["velocity_check"],
            "investigative_insights": "Documento estruturalmente válido. Nenhum indicador forte de fraude detectado pelo modelo determinístico.",
            "enhanced_score": 15,
            "febraban_violations": [],
            "confidence": 0.85
        },
        "verification": {
            "forensic_flags": [],
            "tampering_evidence": "Metadados do PDF consistentes. Camadas únicas. OCR confidence: 92%.",
            "verification_steps": [
                "Validar assinatura digital do emissor",
                "Confirmar CNPJ na Receita Federal"
            ],
            "authenticity_confidence": 0.92
        },
        "compliance": {
            "compliance_flags": [],
            "regulatory_risks": [],
            "verification_steps": [
                "Consultar BACEN ISPB para código do banco",
                "Validar CNPJ na Receita Federal",
                "Verificar CNAE x CBO compatibilidade"
            ],
            "compliance_score": 95,
            "references": [
                "BACEN Resolution 4.557",
                "Art. 406 CC/2002",
                "LGPD Art. 7º"
            ]
        },
        "risk": {
            "final_score": 15,
            "final_classification": "LOW",
            "confidence": 0.88,
            "explanation": "Score base determinístico: 15/100. Nenhuma anomalia crítica ou alta detectada. Documento passa em todas validações FEBRABAN/BACEN. Classificação final: LOW (ACEITAR).",
            "key_evidence": [
                "Checksums FEBRABAN válidos",
                "CNPJ válido e ativo na Receita Federal",
                "Beneficiário corresponde ao cedente visual"
            ],
            "recommendation": "ACCEPT",
            "escalation_required": False
        }
    }

    # High-risk scenario for demo variety
    _HIGH_RISK_RESPONSES = {
        "fraud": {
            "febraban_compliance": {
                "bank_valid": False,
                "checksum_valid": False,
                "due_date_valid": True,
                "fees_legal": True,
                "cnpj_valid": False,
                "pix_match": False,
                "barcode_match": False
            },
            "additional_indicators": [
                "Código de banco inexistente no BACEN ISPB",
                "CNPJ falha no Módulo 11",
                "QR Code Pix aponta para beneficiário divergente",
                "Linha digitável com checksum inválido (Módulo 10/11)"
            ],
            "fraud_patterns": ["boleto_falso", "troca_boleto", "cnpj_invalido"],
            "investigative_insights": "MÚLTIPLAS VIOLAÇÕES FEBRABAN CRÍTICAS: banco inexistente, CNPJ inválido, QR Code divergente. Padrão clássico de boleto fraudado (troca-boleto).",
            "enhanced_score": 95,
            "febraban_violations": [
                "Regra 1: Código de banco não registrado no BACEN ISPB",
                "Regra 5: CNPJ falha no Módulo 11",
                "Regra 6: QR Code Pix beneficiário ≠ cedente visual",
                "Regra 2: Linha digitável checksum Módulo 10/11 inválido",
                "Regra 7: Barcode não corresponde à linha digitável"
            ],
            "confidence": 0.98
        },
        "verification": {
            "forensic_flags": [
                "PDF multi-camadas detectado (overlay attack)",
                "Fontes inconsistentes entre campos",
                "Metadados de criação/modificação suspeitos"
            ],
            "tampering_evidence": "Estrutura PDF indica edição pós-geração. Camada de texto sobreposta ao layout original. Artefatos de geração por IA detectados em 3 regiões.",
            "verification_steps": [
                "Solicitar documento original ao emissor",
                "Análise forense profunda (hash SHA-256)",
                "Verificar certificado digital do emissor"
            ],
            "authenticity_confidence": 0.12
        },
        "compliance": {
            "compliance_flags": [
                {"rule_violated": "Banco não registrado no BACEN ISPB", "regulation": "BACEN Resolution 4.557", "severity": "critical", "evidence": "Código 999 não existe no ISPB"},
                {"rule_violated": "CNPJ inválido (Módulo 11)", "regulation": "Lei 12.973/2014", "severity": "critical", "evidence": "Dígito verificador incorreto"},
                {"rule_violated": "Beneficiário divergente (QR Code vs Visual)", "regulation": "BACEN Circular 3.882", "severity": "critical", "evidence": "Troca-boleto confirmada"}
            ],
            "regulatory_risks": [
                "Possível lavagem de dinheiro (Art. 1º Lei 9.613/98)",
                "Estelionato eletrônico (Art. 171 §2º CP)"
            ],
            "verification_steps": [
                "DENÚNCIA IMEDIATA: Banco Central / Polícia Federal",
                "Bloquear transação no sistema de pagamentos",
                "Notificar vítima e instituição financeira"
            ],
            "compliance_score": 5,
            "references": [
                "BACEN Resolution 4.557 (Art. 406 CC)",
                "Lei 9.613/98 (Lavagem de Dinheiro)",
                "Art. 171 §2º Código Penal (Estelionato)"
            ]
        },
        "risk": {
            "final_score": 95,
            "final_classification": "HIGH",
            "confidence": 0.97,
            "explanation": "DETERMINISTIC BASELINE: 85/100 (já HIGH). MOCK ENHANCEMENT: +10 pontos por evidências forenses e compliance CRÍTICAS. Banco inexistente + CNPJ inválido + troca-boleto = FRAUDE CONFIRMADA. REJEIÇÃO OBRIGATÓRIA.",
            "key_evidence": [
                "Banco código 999 não existe no BACEN ISPB (CRÍTICO)",
                "CNPJ falha Módulo 11 (CRÍTICO)",
                "QR Code Pix → beneficiário divergente = troca-boleto (CRÍTICO)",
                "PDF multi-camadas + fontes inconsistentes = forjaria (CRÍTICO)"
            ],
            "recommendation": "REJECT",
            "escalation_required": True
        }
    }

    def __init__(self, config: LLMConfig, scenario: str = "auto") -> None:
        super().__init__(config)
        self._scenario = scenario  # "auto", "clean", "high_risk"
        self._call_count = 0
        logger.info("MockLLMProvider initialized: scenario=%s", scenario)

    def get_chat_model(self) -> Any:
        """Return a mock LangChain-compatible model."""
        if self._chat_model is not None:
            return self._chat_model

        class MockChatModel:
            def __init__(self, provider: "MockLLMProvider"):
                self.provider = provider

            def invoke(self, messages, **kwargs):
                from langchain_core.messages import AIMessage
                return AIMessage(content=self.provider._generate_response(messages))

            async def ainvoke(self, messages, **kwargs):
                return self.invoke(messages, **kwargs)

        self._chat_model = MockChatModel(self)
        return self._chat_model

    def _generate_response(self, messages) -> str:
        """Generate deterministic mock response based on message content."""
        self._call_count += 1

        # Determine which agent is calling based on system prompt
        system_content = ""
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'system':
                system_content = msg.content.lower()
                break
            elif hasattr(msg, 'content'):
                content = str(msg.content).lower()
                if 'fraud' in content or 'febraban' in content:
                    system_content = 'fraud'
                elif 'forensic' in content or 'verification' in content:
                    system_content = 'verification'
                elif 'compliance' in content or 'bacen' in content or 'cnpj' in content:
                    system_content = 'compliance'
                elif 'risk' in content or 'synthesis' in content or 'final' in content:
                    system_content = 'risk'

        # Pick response set
        if self._scenario == "high_risk" or (self._scenario == "auto" and self._call_count % 3 == 0):
            responses = self._HIGH_RISK_RESPONSES
        else:
            responses = self._RESPONSES

        # Match agent type
        agent_key = "fraud"
        if "verification" in system_content or "forensic" in system_content:
            agent_key = "verification"
        elif "compliance" in system_content or "bacen" in system_content:
            agent_key = "compliance"
        elif "risk" in system_content or "synthesis" in system_content:
            agent_key = "risk"

        response = responses.get(agent_key, self._RESPONSES["fraud"])
        return json.dumps(response, ensure_ascii=False)

    def health_check(self) -> bool:
        """Always healthy — it's a mock!"""
        return True

    def get_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_name="mock",
            model_name="mock-deterministic",
            is_local=True,
            base_url="mock://local",
        )