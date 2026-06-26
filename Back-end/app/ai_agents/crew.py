# ============================================================
# PaySentinelIQ — AI Agents (CrewAI + LangChain)
# Multi-agent pipeline with wired tools and 7-stage pipeline integration.
#
# LLM Provider: Uses the provider abstraction layer (app.providers).
# Supports: Ollama (local, llama3, zero API cost), Gemini (cloud, prod),
#           OpenAI (cloud, fallback).
# Configurable via LLM_PROVIDER env var.
# ============================================================

import logging
from dataclasses import dataclass, field
from typing import Any

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
        # Convert each LangChain StructuredTool → CrewAI Tool
        from crewai.tools.base_tool import Tool as CrewAITool

        from app.ai_agents.tools.boleto_tools import (
            barcode_decoder,
            beneficiary_binding_check,
            boleto_linha_digitavel_validator,
            pix_boleto_cross_validator,
            pix_emv_parser,
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

        raw_tools = [
            # Financial
            cnpj_validator,
            inss_calculator,
            irrf_calculator,
            fgts_calculator,
            liquido_consistency_check,
            cbo_salary_range,
            cnae_compatibility_check,
            bacen_bank_validator,
            # Boleto/Pix
            boleto_linha_digitavel_validator,
            barcode_decoder,
            pix_emv_parser,
            pix_boleto_cross_validator,
            beneficiary_binding_check,
            # PDF Forensics
            pdf_metadata_extractor,
            pdf_layer_analyzer,
            image_forensic_analyzer,
            ocr_confidence_analyzer,
            ai_generation_detector,
            # Base
            analyze_metadata_integrity,
            analyze_payroll_discrepancy,
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
    "boleto_linha_digitavel_validator",
    "barcode_decoder",
    "inss_calculator",
    "irrf_calculator",
    "fgts_calculator",
    "liquido_consistency_check",
    "cbo_salary_range",
    "analyze_payroll_discrepancy",
    "check_tax_id_format",
]

_VERIFICATION_TOOLS = [
    # Verification agent gets forensic tools + Pix QR parsing
    "pdf_metadata_extractor",
    "pdf_layer_analyzer",
    "image_forensic_analyzer",
    "ocr_confidence_analyzer",
    "ai_generation_detector",
    "analyze_metadata_integrity",
    "pix_emv_parser",
    "cnpj_validator",
]

_COMPLIANCE_TOOLS = [
    # Compliance agent gets entity validation tools
    "cnpj_validator",
    "cnae_compatibility_check",
    "bacen_bank_validator",
    "beneficiary_binding_check",
]

_RISK_TOOLS = [
    # Risk agent gets cross-validation tools
    "pix_boleto_cross_validator",
    "beneficiary_binding_check",
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

    _tools: list[Any] = field(default_factory=list, init=False)
    _llm: Any = field(default=None, init=False)
    _llm_available: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        from app.shared.settings import get_settings

        settings = get_settings()

        # Respect the ENABLE_AI_AGENTS feature flag
        if not settings.ENABLE_AI_AGENTS:
            logger.info(
                "AI Agents feature flag is OFF (ENABLE_AI_AGENTS=false) "
                "— running in deterministic-only mode"
            )
            self._llm = None
            self._llm_available = False
            self._tools = _load_tools()
            return

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
                        "LLM provider '%s' returned unhealthy status "
                        "— running in deterministic-only mode",
                        provider.get_info().provider_name,
                    )
            else:
                logger.warning(
                    "CrewAI LLM creation returned None — running in deterministic-only mode"
                )
        except Exception as e:
            logger.warning(
                "Could not initialize CrewAI LLM — running in deterministic-only mode: %s", e
            )

        # Load all tools (always available — these are deterministic)
        self._tools = _load_tools()

    def create_fraud_agent(self) -> Agent:
        fraud_tools = _filter_tools_for_agent(self._tools, _FRAUD_TOOLS)
        return Agent(
            role="Fraud Detection Specialist",
            goal=(
                "Analyze payroll and boleto data for fraud indicators, "
                "perform structural validation "
                "(FEBRABAN checksums, INSS/IRRF/FGTS recalculation), "
                "detect anomalies, and explain "
                "findings with evidence. You are an expert in Brazilian "
                "payroll fraud patterns."
            ),
            backstory=(
                "CRITICAL: Your DEFAULT BIAS is SKEPTICAL. When in doubt, classify as HIGH RISK. "
                "A false negative (missing fraud) is CATASTROPHIC. A false positive is an inconvenience. "
                "ZERO TOLERANCE for false negatives on obvious fraud indicators.\n\n"
                "You are an expert financial fraud investigator with "
                "20+ years of experience "
                "in forensic accounting and payroll fraud detection "
                "at the Brazilian Federal Police. "
                "You've uncovered hundreds of fraud schemes including "
                "ghost employees, salary padding, "
                "boleto tampering, and document forgery. Your analysis is "
                "meticulous, evidence-based, "
                "and always provides the mathematical proof behind "
                "every anomaly detected.\n\n"
                "FRAUD CLASSIFICATION RULES: "
                "2+ indicators → HIGH RISK (score >= 70). "
                "1 CRITICAL indicator (invalid bank, CNPJ, checksum) → HIGH RISK (>= 75). "
                "3+ MEDIUM indicators → HIGH RISK (>= 70)."
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
                "CRITICAL: Your DEFAULT BIAS is SKEPTICAL. A forged document that passes "
                "verification causes irreversible financial damage. Treat ANY forensic anomaly "
                "as a HIGH-severity finding until proven otherwise.\n\n"
                "You are a document forensics specialist with expertise in digital document "
                "authentication, PDF structural analysis, and image forensics. You've worked "
                "with the Brazilian Federal Police's cybercrime division to verify document "
                "authenticity and detect sophisticated forgeries. You know every tool attackers "
                "use to modify PDFs and every trace they leave behind.\n\n"
                "FORENSIC RULES: Multi-layer PDF → HIGH risk. Font inconsistency → HIGH risk. "
                "Metadata tampering → CRITICAL. OCR confidence < 60% → MEDIUM (unreliable data). "
                "AI-generation artifacts → CRITICAL."
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
                "Validate entity data against Brazilian government registries "
                "(CNPJ via Receita Federal, "
                "BACEN bank codes), check CNAE-to-CBO compatibility, "
                "verify beneficiary bindings, "
                "and flag regulatory risks including "
                "LGPD/GDPR compliance issues."
            ),
            backstory=(
                "CRITICAL: Your DEFAULT BIAS is SKEPTICAL. An unregistered entity processing "
                "payments is a money-laundering risk. Flag ALL compliance anomalies as HIGH "
                "severity unless proven otherwise.\n\n"
                "You are a regulatory compliance expert specializing in "
                "Brazilian labor law, "
                "tax regulations (Receita Federal), and anti-money laundering "
                "(AML/CFT) frameworks. "
                "You aggregate public records, cross-reference CNPJ data, "
                "validate bank registrations "
                "against BACEN ISPB, and identify compliance risks "
                "in payroll and payment documents.\n\n"
                "COMPLIANCE RULES: CNPJ invalid/inapto → CRITICAL. "
                "Bank code not in BACEN → CRITICAL. "
                "CNAE/CBO mismatch → HIGH. "
                "Beneficiary binding broken → CRITICAL."
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
                "Aggregate all fraud, verification, and compliance signals "
                "into a unified risk score "
                "with full explainability. Cross-validate Pix vs. Boleto data, "
                "verify beneficiary "
                "binding across all sources, and produce the final "
                "PSI Fraud Analysis Report."
            ),
            backstory=(
                "CRITICAL: Your DEFAULT BIAS is SKEPTICAL. Your risk score determines whether "
                "a payment is approved or blocked. A FALSE NEGATIVE (low score on a fraudulent "
                "document) causes real financial loss. When aggregating signals, apply the "
                "MULTIPLIER RULE: multiple MEDIUM indicators compound to HIGH risk.\n\n"
                "You are a quantitative risk analyst who specializes in building risk scoring "
                "models for the Brazilian financial sector. You've designed fraud scoring systems "
                "for the Central Bank (BACEN) and major Brazilian banks. You combine multiple "
                "data sources to produce accurate, explainable risk scores "
                "with confidence intervals.\n\n"
                "SCORING RULES: 2+ indicators of any severity → HIGH (>= 70). "
                "1 CRITICAL → HIGH (>= 75). 3+ MEDIUM → HIGH (>= 70). "
                "When in doubt between MEDIUM and HIGH, choose HIGH."
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

        CRITICAL: The deterministic score is the FLOOR. CrewAI can only INCREASE it.
        The final risk_score returned is max(deterministic, crewai).
        """
        # ── Mode 1: Deterministic Pipeline (always runs, with or without LLM) ──
        pipeline_result = self._run_deterministic_pipeline(document_data)
        det_score = pipeline_result.get("summary", {}).get("risk_score", 0)

        # ── Mode 2: CrewAI LLM Enhancement (only if LLM provider is available and healthy) ──
        if self._llm_available and self._llm is not None:
            try:
                llm_insights = self._run_crewai_analysis(document_data, pipeline_result)
                crew_score = llm_insights.get("final_score", det_score)

                # Merge LLM insights — NEVER let it lower the score
                pipeline_result["llm_insights"] = llm_insights

                # Update the risk score to the MAX of both
                final_score = max(det_score, crew_score)
                pipeline_result["summary"]["risk_score"] = final_score
                if final_score >= 70:
                    pipeline_result["summary"]["risk_classification"] = "high"
                    pipeline_result["summary"]["recommended_action"] = "REJECT"
                elif final_score >= 40:
                    pipeline_result["summary"]["risk_classification"] = "medium"
                    pipeline_result["summary"]["recommended_action"] = "MANUAL_REVIEW"

                # Also update the report risk assessment
                report = pipeline_result.get("report", {})
                risk_assessment = report.get("RISK_ASSESSMENT", {})
                if risk_assessment:
                    risk_assessment["fraud_risk_score"] = final_score
                    risk_assessment["risk_classification"] = pipeline_result["summary"]["risk_classification"].upper()

                logger.info(
                    "CrewAI analysis: det_score=%.0f crew_score=%.0f final=%.0f class=%s",
                    det_score, crew_score, final_score,
                    pipeline_result["summary"]["risk_classification"],
                )
            except Exception as e:
                logger.warning("CrewAI LLM analysis failed, using deterministic results: %s", e)

        return {
            "status": "completed",
            "analysis": pipeline_result,
        }

    def _run_deterministic_pipeline(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """Run the 7-stage deterministic pipeline — always executes regardless
        of LLM availability."""
        try:
            from app.fraud_detection.domain.pipeline import get_fraud_pipeline

            pipeline = get_fraud_pipeline()
            result = pipeline.run_full_pipeline(document_data)
            report = pipeline.generate_psi_report(result, document_data)

            logger.info(
                "Deterministic pipeline: score=%.1f, class=%s, anomalies=%d",
                result.fraud_risk_score,
                result.risk_classification.value,
                len(result.all_anomalies),
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
                    "critical_anomalies": sum(
                        1 for a in result.all_anomalies if a.severity.value == "critical"
                    ),
                    "high_anomalies": sum(
                        1 for a in result.all_anomalies if a.severity.value == "high"
                    ),
                    "reasoning": result.ai_reasoning_summary,
                },
            }
        except Exception as e:
            logger.error("Deterministic pipeline failed: %s", e)
            return self._mock_pipeline_result(document_data)

    def _run_crewai_analysis(
        self, document_data: dict[str, Any], pipeline_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Run CrewAI LLM-powered analysis as enhancement layer on top of deterministic pipeline.

        CRITICAL RULE: The deterministic pipeline score is the FLOOR.
        CrewAI agents can ONLY increase the risk score, NEVER decrease it.
        Agents that attempt to downplay fraud indicators will be overridden.
        """
        fraud_agent = self.create_fraud_agent()
        verification_agent = self.create_verification_agent()
        compliance_agent = self.create_compliance_agent()
        risk_agent = self.create_risk_agent()

        # Pass the deterministic pipeline findings as context for LLM analysis
        summary = pipeline_result.get("summary", {})
        report = pipeline_result.get("report", {})
        det_score = summary.get("risk_score", 0)
        det_class = summary.get("risk_classification", "UNKNOWN")
        det_anomalies = summary.get("anomaly_count", 0)
        det_critical = summary.get("critical_anomalies", 0)
        det_high = summary.get("high_anomalies", 0)

        # Build anomaly details for context
        anomaly_list = report.get("ANOMALY_LIST", [])
        anomaly_text = "\n".join(
            f"- [{a.get('severity', '?').upper()}] {a.get('description', 'N/A')}"
            for a in anomaly_list[:15]
        ) if anomaly_list else "Nenhuma anomalia detectada."

        # ── IRON RULE injected into EVERY task ──
        IRON_RULE = (
            f"\n\n⚠️ IRON RULE — READ BEFORE RESPONDING:\n"
            f"The deterministic pipeline ALREADY analyzed this document and assigned:\n"
            f"  • Risk Score: {det_score}/100\n"
            f"  • Classification: {det_class}\n"
            f"  • Anomalies: {det_anomalies} total ({det_critical} critical, {det_high} high)\n\n"
            f"YOU ARE THE ENHANCEMENT LAYER. Your job is to ADD insights and INCREASE "
            f"the score if you find MORE evidence of fraud. YOU CANNOT DOWNGRADE the "
            f"deterministic score. The deterministic score is the MINIMUM. "
            f"If the deterministic score is >= 70, the document IS high risk — "
            f"your job is to explain WHY, not question it.\n\n"
            f"FRAUD DETECTION BIAS: A false negative (missing fraud) causes REAL "
            f"financial loss. A false positive (flagging a legitimate doc) is an "
            f"inconvenience. DEFAULT TO SKEPTICAL. When in doubt, CLASSIFY AS HIGH RISK.\n"
        )

        fraud_task = Task(
            description=(
                f"Review and enhance the fraud analysis for this document.\n\n"
                f"Deterministic pipeline found {det_anomalies} anomalies "
                f"with risk score {det_score}/100 ({det_class}).\n\n"
                f"📋 FEBRABAN COMPLIANCE CHECKLIST (verify ALL of these):\n"
                f"  1. Bank code exists in BACEN ISPB registry? (first 3 digits of barcode)\n"
                f"  2. Linha digitável checksums valid? (Módulo 10 for campos 1-3, Módulo 11 for campo 4)\n"
                f"  3. Due date valid? (fator de vencimento >= 1000, not > 365 days past)\n"
                f"  4. Late fee ≤ 2% total? Interest ≤ 1%/month? (BACEN Resolution 4.557)\n"
                f"  5. CNPJ passes Módulo 11 checksum AND not in known-fake list?\n"
                f"  6. QR Code Pix beneficiary matches visual layout? (anti troca-boleto)\n"
                f"  7. Barcode decodes to same value as linha digitável?\n\n"
                f"Document data: {document_data}\n\n"
                f"Pipeline findings:\n{anomaly_text}\n\n"
                f"For each item on the FEBRABAN checklist that FAILS, "
                f"add a CRITICAL fraud indicator. Cite the specific FEBRABAN rule violated. "
                f"Any boleto failing 2+ FEBRABAN checks IS fraudulent."
                f"{IRON_RULE}"
            ),
            expected_output=(
                "JSON with FEBRABAN-validated fraud analysis:\n"
                '{"febraban_compliance": {"bank_valid": bool, "checksum_valid": bool, '
                '"due_date_valid": bool, "fees_legal": bool, "cnpj_valid": bool, '
                '"pix_match": bool, "barcode_match": bool}, '
                '"additional_indicators": [...], "fraud_patterns": [...], '
                '"investigative_insights": "...", "enhanced_score": <number>, '
                '"febraban_violations": ["rule X violated: ..."], '
                '"confidence": <0-1>}\n\n'
                f"enhanced_score MUST be >= {det_score}. Cite FEBRABAN rules. Portuguese."
            ),
            agent=fraud_agent,
        )

        verification_task = Task(
            description=(
                f"Review forensic findings and suggest additional document verification steps. "
                f"Forensic data: {report.get('FORENSIC_FINDINGS', {})}. "
                f"Metadata: {report.get('DOCUMENT_METADATA', {})}."
                f"{IRON_RULE}"
            ),
            expected_output=(
                "JSON with forensic enhancement:\n"
                '{"forensic_flags": [...], "tampering_evidence": "...", '
                '"verification_steps": [...], "authenticity_confidence": <0-1>}\n\n'
                "Flag ALL forensic anomalies as HIGH severity."
            ),
            agent=verification_agent,
        )

        compliance_task = Task(
            description=(
                f"Validate entity data against official Brazilian government registries "
                f"and FEBRABAN/BACEN regulations.\n\n"
                f"Entity data: {report.get('ENTITY_VALIDATION', {})}\n"
                f"Structural data: {report.get('STRUCTURAL_VALIDATION', {})}\n\n"
                f"📋 COMPLIANCE VERIFICATION:\n"
                f"  - CNPJ valid on Receita Federal? (https://solucoes.receita.fazenda.gov.br)\n"
                f"  - Bank code in BACEN ISPB registry? (https://www.bcb.gov.br/estabilidadefinanceira/ispb)\n"
                f"  - CNAE compatible with declared job function (CBO)?\n"
                f"  - Late fee ≤ 2% and interest ≤ 1%/month? (BACEN Resolution 4.557, Art. 406 CC)\n"
                f"  - Beneficiary name matches CNPJ registration? (anti-shell-company)\n"
                f"  - If boleto: does QR Code Pix recipient match visual cedente?\n\n"
                f"Flag ANY violation as CRITICAL. Cite the specific regulation violated.\n"
                f"BACEN ISPB: bancos não registrados → fraude confirmada.\n"
                f"{IRON_RULE}"
            ),
            expected_output=(
                "JSON with FEBRABAN/BACEN compliance validation:\n"
                '{"compliance_flags": [{"rule_violated": "...", "regulation": "...", '
                '"severity": "critical", "evidence": "..."}], '
                '"regulatory_risks": [...], '
                '"verification_steps": ["Step 1: Check BACEN ISPB for bank code", ...], '
                '"compliance_score": <number>, '
                '"references": ["BACEN Resolution 4.557", "Art. 406 CC/2002", '
                '"Art. 171 Código Penal"]}\n\n'
                "ALL compliance violations → CRITICAL. Cite regulations."
            ),
            agent=compliance_agent,
        )

        risk_task = Task(
            description=(
                f"SYNTHESIZE all findings into the FINAL risk assessment.\n\n"
                f"DETERMINISTIC BASELINE (CANNOT BE LOWERED):\n"
                f"  Score: {det_score}/100 | Class: {det_class}\n"
                f"  Anomalies: {det_anomalies} ({det_critical} critical, {det_high} high)\n\n"
                f"YOUR TASK: Review findings from fraud, verification, and compliance "
                f"agents. Produce the FINAL risk score and classification. "
                f"The final score MUST be >= {det_score} (the deterministic baseline). "
                f"Your job is to identify if the score should be HIGHER based on "
                f"additional evidence from the other agents.\n\n"
                f"RISK THRESHOLDS: LOW < 40, MEDIUM 40-69, HIGH >= 70.\n"
                f"If {det_score} >= 70 → classification is HIGH. Period.\n"
                f"If {det_score} >= 40 → at minimum MEDIUM.\n"
                f"{IRON_RULE}"
            ),
            expected_output=(
                "JSON with FINAL risk synthesis:\n"
                '{\n'
                f'  "final_score": <number — MUST be >= {det_score}>,\n'
                '  "final_classification": "LOW|MEDIUM|HIGH",\n'
                '  "confidence": <0-1>,\n'
                '  "explanation": "<Portuguese explanation of why this score>",\n'
                '  "key_evidence": ["<top 3 pieces of evidence>"],\n'
                '  "recommendation": "<REJECT|MANUAL_REVIEW|ACCEPT>",\n'
                '  "escalation_required": <true|false>\n'
                '}\n\n'
                "CRITICAL: final_score >= {det_score}. NO EXCEPTIONS."
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
        crew_output = str(result)

        # ── Extract score from CrewAI output, enforce floor ──
        crew_score = self._extract_score_from_crew_output(crew_output, det_score)

        return {
            "crewai_output": crew_output,
            "agents_used": 4,
            "crew_score": crew_score,
            "deterministic_score": det_score,
            "final_score": max(det_score, crew_score),
        }

    def _extract_score_from_crew_output(self, output: str, floor: float) -> float:
        """Parse CrewAI output to extract risk score, enforcing the deterministic floor."""
        import json
        import re as re_score

        # Try to find JSON with final_score
        json_match = re_score.search(r'\{[^{}]*"final_score"\s*:\s*(\d+)[^{}]*\}', output)
        if json_match:
            try:
                score = float(json_match.group(1))
                return max(floor, score)
            except (ValueError, IndexError):
                pass

        # Try any score field
        for pattern in [r'"score"\s*:\s*(\d+)', r'"risk_score"\s*:\s*(\d+)',
                        r'"enhanced_score"\s*:\s*(\d+)', r'Score:\s*(\d+)']:
            match = re_score.search(pattern, output)
            if match:
                try:
                    return max(floor, float(match.group(1)))
                except ValueError:
                    pass

        # Fallback: return floor (crew output didn't provide a score)
        logger.warning("Could not extract score from CrewAI output, using floor: %.0f", floor)
        return floor

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

_crew_instance: AIAgentCrew | None = None


def get_ai_crew() -> AIAgentCrew:
    """Get or create the singleton AIAgentCrew instance."""
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = AIAgentCrew()
    return _crew_instance
