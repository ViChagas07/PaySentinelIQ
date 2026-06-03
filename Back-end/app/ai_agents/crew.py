# ============================================================
# PaySentinelIQ — AI Agents (CrewAI + LangChain)
# Multi-agent pipeline with wired tools and 7-stage pipeline integration.
#
# LLM Provider: Uses the provider abstraction layer (app.providers).
# Default: Ollama (local, llama3, zero API cost).
# Configurable via LLM_PROVIDER env var to any supported provider.
# ============================================================

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from crewai import Agent, Crew, Process, Task

from app.providers.factory import get_crewai_llm, get_llm_provider

logger = logging.getLogger(__name__)


# ── Tool Imports ──

def _load_tools() -> list[Any]:
    """Load all registered tools and convert them to CrewAI-compatible format.

    CrewAI 1.14+ requires tools to be instances of crewai.tools.base_tool.Tool,
    NOT raw LangChain StructuredTool objects. This function converts using
    Tool.from_langchain() so that Agent(validate_tools) accepts them.
    """
    tools = []
    try:
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
        from app.ai_agents.tools.custom_tools import (
            analyze_metadata_integrity,
            analyze_payroll_discrepancy,
            check_tax_id_format,
        )
        from app.ai_agents.tools.pdf_forensic_tools import (
            ai_generation_detector,
            image_forensic_analyzer,
            ocr_confidence_analyzer,
            pdf_layer_analyzer,
            pdf_metadata_extractor,
        )

        # Convert each LangChain StructuredTool → CrewAI Tool
        from crewai.tools.base_tool import Tool as CrewAITool

        raw_tools = [
            # Financial
            cnpj_validator, inss_calculator, irrf_calculator, fgts_calculator,
            liquido_consistency_check, cbo_salary_range, cnae_compatibility_check,
            bacen_bank_validator,
            # Boleto/Pix
            boleto_linha_digitavel_validator, barcode_decoder,
            pix_emv_parser, pix_boleto_cross_validator, beneficiary_binding_check,
            # PDF Forensics
            pdf_metadata_extractor, pdf_layer_analyzer,
            image_forensic_analyzer, ocr_confidence_analyzer,
            ai_generation_detector,
            # Base
            analyze_metadata_integrity, analyze_payroll_discrepancy,
            check_tax_id_format,
        ]

        tools = [CrewAITool.from_langchain(t) for t in raw_tools]
        logger.info("Loaded and converted %d tools for CrewAI agents", len(tools))
    except Exception as e:
        logger.warning("Could not load some tools: %s", e)

    return tools


# Agent-specific tool assignments
_FRAUD_TOOLS = [
    # Fraud agent gets the core detection tools
    "boleto_linha_digitavel_validator", "barcode_decoder",
    "inss_calculator", "irrf_calculator", "fgts_calculator",
    "liquido_consistency_check", "cbo_salary_range",
    "analyze_payroll_discrepancy", "check_tax_id_format",
]

_VERIFICATION_TOOLS = [
    # Verification agent gets forensic tools + Pix QR parsing
    "pdf_metadata_extractor", "pdf_layer_analyzer",
    "image_forensic_analyzer", "ocr_confidence_analyzer",
    "ai_generation_detector", "analyze_metadata_integrity",
    "pix_emv_parser", "cnpj_validator",
]

_COMPLIANCE_TOOLS = [
    # Compliance agent gets entity validation tools
    "cnpj_validator", "cnae_compatibility_check",
    "bacen_bank_validator", "beneficiary_binding_check",
]

_RISK_TOOLS = [
    # Risk agent gets cross-validation tools
    "pix_boleto_cross_validator", "beneficiary_binding_check",
    "check_tax_id_format",
]


def _filter_tools_for_agent(all_tools: list[Any], tool_names: list[str]) -> list[Any]:
    """Filter tools by name for a specific agent."""
    return [t for t in all_tools if t.name in tool_names]


@dataclass
class AIAgentCrew:
    """
    Orchestrates the multi-agent pipeline for document analysis.

    LLM integration is handled via the provider abstraction layer (app.providers).
    By default, uses Ollama running locally with llama3 for zero-cost inference.

    Dual execution mode:
    1. Deterministic 7-stage pipeline (always runs, no LLM required)
    2. CrewAI LLM enhancement (runs when LLM provider is healthy)

    If the LLM provider is unavailable, the deterministic pipeline still produces
    complete results — the LLM layer is purely additive.
    """

    _tools: list = field(default_factory=list, init=False)
    _llm: Any = field(default=None, init=False)
    _llm_available: bool = field(default=False, init=False)

    def __post_init__(self):
        # Attempt to initialize the CrewAI-compatible LLM from the configured provider
        self._llm = None
        self._llm_available = False
        try:
            self._llm = get_crewai_llm()
            if self._llm is not None:
                # Quick connectivity check — non-blocking
                provider = get_llm_provider()
                if provider.health_check():
                    self._llm_available = True
                    pinfo = provider.get_info()
                    logger.info(
                        "LLM provider ready: %s / %s (local=%s)",
                        pinfo.provider_name,
                        pinfo.model_name,
                        pinfo.is_local,
                    )
                else:
                    logger.warning(
                        "LLM provider '%s' returned unhealthy status — running in deterministic-only mode",
                        provider.get_info().provider_name,
                    )
            else:
                logger.warning("CrewAI LLM creation returned None — running in deterministic-only mode")
        except Exception as e:
            logger.warning("Could not initialize CrewAI LLM — running in deterministic-only mode: %s", e)

        # Load all tools (always available — these are deterministic)
        self._tools = _load_tools()

    def create_fraud_agent(self) -> Agent:
        fraud_tools = _filter_tools_for_agent(self._tools, _FRAUD_TOOLS)
        return Agent(
            role="Fraud Detection Specialist",
            goal=(
                "Analyze payroll and boleto data for fraud indicators, perform structural validation "
                "(FEBRABAN checksums, INSS/IRRF/FGTS recalculation), detect anomalies, and explain "
                "findings with evidence. You are an expert in Brazilian payroll fraud patterns."
            ),
            backstory=(
                "You are an expert financial fraud investigator with 20+ years of experience "
                "in forensic accounting and payroll fraud detection at the Brazilian Federal Police. "
                "You've uncovered hundreds of fraud schemes including ghost employees, salary padding, "
                "boleto tampering, and document forgery. Your analysis is meticulous, evidence-based, "
                "and always provides the mathematical proof behind every anomaly detected."
            ),
            llm=self._llm,
            tools=fraud_tools,
            verbose=False,
            allow_delegation=False,
        )

    def create_verification_agent(self) -> Agent:
        verification_tools = _filter_tools_for_agent(self._tools, _VERIFICATION_TOOLS)
        return Agent(
            role="Document Verification Expert",
            goal=(
                "Validate document authenticity through multi-layer PDF forensic analysis. "
                "Detect metadata tampering, font inconsistencies, layer overlay attacks, "
                "image forgery, AI-generated document artifacts, and OCR confidence anomalies."
            ),
            backstory=(
                "You are a document forensics specialist with expertise in digital document "
                "authentication, PDF structural analysis, and image forensics. You've worked "
                "with the Brazilian Federal Police's cybercrime division to verify document "
                "authenticity and detect sophisticated forgeries. You know every tool attackers "
                "use to modify PDFs and every trace they leave behind."
            ),
            llm=self._llm,
            tools=verification_tools,
            verbose=False,
            allow_delegation=False,
        )

    def create_compliance_agent(self) -> Agent:
        compliance_tools = _filter_tools_for_agent(self._tools, _COMPLIANCE_TOOLS)
        return Agent(
            role="Compliance Intelligence Analyst",
            goal=(
                "Validate entity data against Brazilian government registries (CNPJ via Receita Federal, "
                "BACEN bank codes), check CNAE-to-CBO compatibility, verify beneficiary bindings, "
                "and flag regulatory risks including LGPD/GDPR compliance issues."
            ),
            backstory=(
                "You are a regulatory compliance expert specializing in Brazilian labor law, "
                "tax regulations (Receita Federal), and anti-money laundering (AML/CFT) frameworks. "
                "You aggregate public records, cross-reference CNPJ data, validate bank registrations "
                "against BACEN ISPB, and identify compliance risks in payroll and payment documents."
            ),
            llm=self._llm,
            tools=compliance_tools,
            verbose=False,
            allow_delegation=False,
        )

    def create_risk_agent(self) -> Agent:
        risk_tools = _filter_tools_for_agent(self._tools, _RISK_TOOLS)
        return Agent(
            role="Risk Scoring Specialist",
            goal=(
                "Aggregate all fraud, verification, and compliance signals into a unified risk score "
                "with full explainability. Cross-validate Pix vs. Boleto data, verify beneficiary "
                "binding across all sources, and produce the final PSI Fraud Analysis Report."
            ),
            backstory=(
                "You are a quantitative risk analyst who specializes in building risk scoring "
                "models for the Brazilian financial sector. You've designed fraud scoring systems "
                "for the Central Bank (BACEN) and major Brazilian banks. You combine multiple "
                "data sources to produce accurate, explainable risk scores with confidence intervals."
            ),
            llm=self._llm,
            tools=risk_tools,
            verbose=False,
            allow_delegation=False,
        )

    def run_pipeline(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the full multi-agent analysis pipeline.

        Two execution modes:
        1. Deterministic 7-stage pipeline (always runs — no LLM needed)
        2. CrewAI LLM enhancement layer (only if LLM provider is healthy and available)

        Both modes produce the same structured output format.
        """
        # ── Mode 1: Deterministic Pipeline (always runs, with or without LLM) ──
        pipeline_result = self._run_deterministic_pipeline(document_data)

        # ── Mode 2: CrewAI LLM Enhancement (only if LLM provider is available and healthy) ──
        if self._llm_available and self._llm is not None:
            try:
                llm_insights = self._run_crewai_analysis(document_data, pipeline_result)
                # Merge LLM insights into pipeline result
                pipeline_result["llm_insights"] = llm_insights
                logger.info("CrewAI LLM analysis completed and merged")
            except Exception as e:
                logger.warning("CrewAI LLM analysis failed, using deterministic results: %s", e)

        return {
            "status": "completed",
            "analysis": pipeline_result,
        }

    def _run_deterministic_pipeline(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """Run the 7-stage deterministic pipeline — always executes regardless of LLM availability."""
        try:
            from app.fraud_detection.domain.pipeline import get_fraud_pipeline

            pipeline = get_fraud_pipeline()
            result = pipeline.run_full_pipeline(document_data)
            report = pipeline.generate_psi_report(result, document_data)

            logger.info(
                "Deterministic pipeline: score=%.1f, class=%s, anomalies=%d",
                result.fraud_risk_score, result.risk_classification.value, len(result.all_anomalies),
            )

            return {
                "pipeline_version": "7-stage PSI v1.0",
                "report": report,
                "summary": {
                    "document_id": result.document_id,
                    "document_class": result.document_class.value,
                    "risk_score": result.fraud_risk_score,
                    "risk_classification": result.risk_classification.value,
                    "ai_confidence": result.ai_confidence,
                    "recommended_action": result.recommended_action,
                    "anomaly_count": len(result.all_anomalies),
                    "critical_anomalies": sum(1 for a in result.all_anomalies if a.severity.value == "critical"),
                    "high_anomalies": sum(1 for a in result.all_anomalies if a.severity.value == "high"),
                    "reasoning": result.ai_reasoning_summary,
                },
            }
        except Exception as e:
            logger.error("Deterministic pipeline failed: %s", e)
            return self._mock_pipeline_result(document_data)

    def _run_crewai_analysis(
        self, document_data: dict[str, Any], pipeline_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Run CrewAI LLM-powered analysis as enhancement layer on top of deterministic pipeline."""
        fraud_agent = self.create_fraud_agent()
        verification_agent = self.create_verification_agent()
        compliance_agent = self.create_compliance_agent()
        risk_agent = self.create_risk_agent()

        # Pass the deterministic pipeline findings as context for LLM analysis
        summary = pipeline_result.get("summary", {})
        report = pipeline_result.get("report", {})

        fraud_task = Task(
            description=(
                f"Review and enhance the fraud analysis for this document. "
                f"Deterministic pipeline found {summary.get('anomaly_count', 0)} anomalies "
                f"with risk score {summary.get('risk_score', 0)}/100. "
                f"Document data: {document_data}. "
                f"Pipeline findings: {report.get('ANOMALY_LIST', [])}. "
                f"Provide additional investigative insights and fraud pattern analysis."
            ),
            expected_output=(
                "Enhanced fraud analysis with investigative insights, fraud pattern "
                "identification, and recommended investigation steps in Portuguese."
            ),
            agent=fraud_agent,
        )

        verification_task = Task(
            description=(
                f"Review forensic findings and suggest additional document verification steps. "
                f"Forensic data: {report.get('FORENSIC_FINDINGS', {})}. "
                f"Metadata: {report.get('DOCUMENT_METADATA', {})}."
            ),
            expected_output="Document verification enhancement with specific forensic recommendations.",
            agent=verification_agent,
        )

        compliance_task = Task(
            description=(
                f"Review entity validation and flag additional compliance risks. "
                f"Entity data: {report.get('ENTITY_VALIDATION', {})}. "
                f"Suggest additional regulatory checks and compliance verification steps."
            ),
            expected_output="Compliance enhancement with regulatory risk flags and verification steps.",
            agent=compliance_agent,
        )

        risk_task = Task(
            description=(
                f"Synthesize all findings: deterministic score {summary.get('risk_score', 0)}/100, "
                f"classification {summary.get('risk_classification', 'LOW')}. "
                f"Provide risk interpretation, confidence assessment, and final recommendations "
                f"in Portuguese for human analysts."
            ),
            expected_output=(
                "Final risk synthesis in Portuguese with plain-language explanation, "
                "confidence assessment, and prioritized action items."
            ),
            agent=risk_agent,
            context=[fraud_task, verification_task, compliance_task],
        )

        crew = Crew(
            agents=[fraud_agent, verification_agent, compliance_agent, risk_agent],
            tasks=[fraud_task, verification_task, compliance_task, risk_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()
        return {"crewai_output": str(result), "agents_used": 4}

    def _mock_pipeline_result(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback when both deterministic pipeline and LLM are unavailable."""
        return {
            "pipeline_version": "mock-fallback",
            "report": {
                "RISK_ASSESSMENT": {
                    "fraud_risk_score": 0,
                    "risk_classification": "LOW",
                    "ai_confidence": 50,
                    "recommended_action": "MANUAL_REVIEW",
                },
                "AI_REASONING_SUMMARY": (
                    "Pipeline não pôde ser executado completamente. "
                    "Verifique a configuração do ambiente e tente novamente."
                ),
                "ANOMALY_LIST": [],
            },
            "summary": {
                "risk_score": 0,
                "risk_classification": "low",
                "anomaly_count": 0,
                "reasoning": "Pipeline fallback — análise completa indisponível.",
            },
        }


# ── Singleton ──

_crew_instance: Optional[AIAgentCrew] = None


def get_ai_crew() -> AIAgentCrew:
    """Get or create the singleton AIAgentCrew instance."""
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = AIAgentCrew()
    return _crew_instance
