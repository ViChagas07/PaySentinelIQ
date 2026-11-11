from __future__ import annotations

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.base import BaseStage


class DeterministicRulesStage(BaseStage):
    def __init__(self) -> None:
        super().__init__(name="DeterministicRulesStage")

    def _execute(self, context: PipelineContext) -> None:
        from app.shared.settings import get_settings

        if not getattr(
            get_settings(),
            "ENABLE_DETERMINISTIC_RULES",
            True,
        ):
            return

        document_type = (context.document_type or "").lower()
        extraction_metadata = context.metadata.get("extraction", {})
        if document_type not in {
            "boleto",
            "contracheque",
            "holerite",
            "payroll",
            "payslip",
        }:
            inferred = (
                extraction_metadata.get("document_type_inferred")
                if isinstance(extraction_metadata, dict)
                else None
            )
            document_type = str(inferred or "").lower()

        if document_type == "boleto":
            self._validate_boleto(context)
        elif document_type in {
            "contracheque",
            "holerite",
            "payroll",
            "payslip",
        }:
            self._validate_payslip(context)
        else:
            context.metadata["validation"] = {
                "skipped_rules": ["unsupported_document_type"],
            }

    def _validate_boleto(self, context: PipelineContext) -> None:
        from app.services.validation.febraban import validate_boleto

        try:
            fields = context.extracted_fields
            evidences, decoded, skipped = validate_boleto(
                linha_digitavel=fields.get("linha_digitavel"),
                valor_nominal=fields.get("valor_nominal"),
                data_vencimento=fields.get("data_vencimento"),
                codigo_barras=fields.get("codigo_barras"),
                codigo_banco=fields.get("codigo_banco"),
                text=context.extracted_text,
            )
            for evidence in evidences:
                context.add_evidence(evidence)
            context.metadata["validation"] = {
                "document_type": "boleto",
                "boleto_decoded": decoded,
                "skipped_rules": skipped,
                "tabelas": {},
                "findings": {
                    evidence.code: evidence.metadata
                    for evidence in evidences
                },
            }
        except Exception as exc:
            context.add_warning(
                f"Deterministic rules failed: {type(exc).__name__}"
            )

    def _validate_payslip(self, context: PipelineContext) -> None:
        from app.services.validation.payslip_rules import validate_payslip

        try:
            evidences, expected, skipped = validate_payslip(
                context.extracted_fields
            )
            for evidence in evidences:
                context.add_evidence(evidence)
            context.metadata["validation"] = {
                "document_type": "contracheque",
                "payslip_expected": expected,
                "skipped_rules": skipped,
                "tabelas": expected.get("tables", {}),
                "findings": {
                    evidence.code: evidence.metadata
                    for evidence in evidences
                },
            }
        except Exception as exc:
            context.add_warning(
                f"Deterministic rules failed: {type(exc).__name__}"
            )
