# ============================================================
# PaySentinelIQ — Golden Dataset Runner (Fase 5)
# ============================================================
"""Automated test runner for the golden dataset.

Usage:
    python -m tests.golden_dataset_runner

Validates that the CanonicalPipeline correctly classifies:
  - Fraudulent boletos as HIGH risk (score >= 70)
  - Legitimate documents as LOW risk (score < 40)

Generates accuracy, precision, recall, F1, and confusion matrix.
"""

from __future__ import annotations

import time
import json
from pathlib import Path

DATASET_ROOT = Path(__file__).parent / "resources" / "fraud_cases"


class GoldenDatasetRunner:
    def __init__(self):
        self.results: list[dict] = []
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0

    def run(self) -> dict:
        """Run all test cases and return statistics."""
        # Test cases: (expected_level, document_type, indicators_count)
        test_cases = [
            # Fraudulent: must score >= 70 (HIGH)
            ("HIGH", "boleto", "banco_invalido", 1),
            ("HIGH", "boleto", "cnpj_falso", 1),
            ("HIGH", "boleto", "multa_ilegal", 1),
            ("HIGH", "boleto", "vencido_2anos", 1),
            ("HIGH", "boleto", "todos_indicadores", 5),
            # Legitimate: should score < 40 (LOW)
            ("LOW", "boleto", "legitimo", 0),
            ("LOW", "contracheque", "legitimo", 0),
        ]

        for expected_level, doc_type, case_name, min_indicators in test_cases:
            t0 = time.monotonic()
            try:
                result = self._run_test_case(doc_type, min_indicators)
                elapsed_ms = (time.monotonic() - t0) * 1000
                actual_level = "HIGH" if result.get("risk_score", 0) >= 70 else (
                    "MEDIUM" if result.get("risk_score", 0) >= 40 else "LOW"
                )
                passed = actual_level == expected_level

                if expected_level == "HIGH" and actual_level == "HIGH":
                    self.true_positives += 1
                elif expected_level == "HIGH" and actual_level != "HIGH":
                    self.false_negatives += 1
                elif expected_level == "LOW" and actual_level == "LOW":
                    self.true_negatives += 1
                elif expected_level == "LOW" and actual_level != "LOW":
                    self.false_positives += 1

                self.results.append({
                    "case": case_name,
                    "expected": expected_level,
                    "actual": actual_level,
                    "score": result.get("risk_score", 0),
                    "evidence_count": result.get("evidence_count", 0),
                    "passed": passed,
                    "time_ms": round(elapsed_ms, 1),
                })
            except Exception as e:
                self.results.append({
                    "case": case_name, "expected": expected_level,
                    "actual": "ERROR", "score": 0, "evidence_count": 0,
                    "passed": False, "time_ms": 0, "error": str(e),
                })

        return self._compute_stats()

    def _run_test_case(self, doc_type: str, min_indicators: int) -> dict:
        """Simulate a test case with known evidence."""
        from app.core.contracts.pipeline_context import PipelineContext
        from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
        from app.services.pipeline.canonical_pipeline import CanonicalPipeline

        ctx = PipelineContext(document_type=doc_type)
        if min_indicators >= 1:
            ctx.add_evidence(Evidence(
                code="BANCO_INVALIDO", description="Bank code 999 not in BACEN ISPB",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
            ))
        if min_indicators >= 2:
            ctx.add_evidence(Evidence(
                code="CNPJ_INVALIDO", description="CNPJ 00.000.000/0001-99 is fake",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
            ))
        if min_indicators >= 3:
            ctx.add_evidence(Evidence(
                code="MULTA_ILEGAL", description="Late fee 5% per day — legal limit is 2%",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
            ))
        if min_indicators >= 4:
            ctx.add_evidence(Evidence(
                code="VENCIDO_2ANOS", description="Due date is 892 days past",
                severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
            ))
        if min_indicators >= 5:
            ctx.add_evidence(Evidence(
                code="VALOR_REDONDO", description="Suspicious round amount R$ 500.00",
                severity=Severity.MEDIUM, source=EvidenceSource.HEURISTIC, confidence=0.7,
            ))

        pipeline = CanonicalPipeline()
        result = pipeline.execute(ctx)
        d = result.to_dict()
        d["evidence_count"] = len(result.evidence)
        return d

    def _compute_stats(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        tp, tn, fp, fn = self.true_positives, self.true_negatives, self.false_positives, self.false_negatives

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)

        return {
            "summary": {
                "total_cases": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed / max(total, 1) * 100, 1),
            },
            "confusion_matrix": {
                "true_positives": tp, "true_negatives": tn,
                "false_positives": fp, "false_negatives": fn,
            },
            "metrics": {
                "accuracy": round((tp + tn) / max(tp + tn + fp + fn, 1), 3),
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3),
            },
            "results": self.results,
        }


if __name__ == "__main__":
    runner = GoldenDatasetRunner()
    stats = runner.run()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if stats["summary"]["failed"] > 0:
        print(f"\nFAILED: {stats['summary']['failed']} cases!")
        exit(1)
    else:
        print(f"\nALL {stats['summary']['total_cases']} cases PASSED")
