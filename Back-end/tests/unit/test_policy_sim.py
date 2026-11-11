import json
from pathlib import Path

import pytest

from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.services.scoring.fusion_engine import FusionEngine
from app.synthetic.policy_sim import (
    classify,
    simulate_score,
)

DUMP = (
    Path(__file__).resolve().parents[1]
    / ".."
    / "docs"
    / "eval"
    / "evidence_dump_before.jsonl"
).resolve()


def _load_dump() -> list[dict]:
    return [
        json.loads(line)
        for line in DUMP.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_simulator_matches_fusion_engine_for_200_documents():
    dump = _load_dump()[:200]
    assert len(dump) == 200

    for item in dump:
        simulated = simulate_score(item["evidences"], "V0")
        assert abs(simulated - float(item["score"])) <= 0.01


def test_simulator_matches_fusion_engine_object_by_object():
    fusion = FusionEngine()
    evidences = [
        {
            "code": "A",
            "severity": "critical",
            "source": "deterministic",
            "confidence": 1.0,
        },
        {
            "code": "B",
            "severity": "high",
            "source": "heuristic",
            "confidence": 0.5,
        },
        {
            "code": "C",
            "severity": "low",
            "source": "deterministic",
            "confidence": 0.7,
        },
    ]
    objects = [
        Evidence(
            code=item["code"],
            description=item["code"],
            severity=Severity(item["severity"]),
            source=EvidenceSource(item["source"]),
            confidence=item["confidence"],
        )
        for item in evidences
    ]

    assert simulate_score(evidences) == fusion.fuse(objects)["final_score"]


def test_variants_change_only_the_documented_policy():
    evidences = [
        {
            "code": "C",
            "severity": "critical",
            "source": "deterministic",
            "confidence": 1.0,
        },
        {
            "code": "H",
            "severity": "high",
            "source": "deterministic",
            "confidence": 1.0,
        },
        {
            "code": "L",
            "severity": "low",
            "source": "deterministic",
            "confidence": 1.0,
        },
    ]

    assert simulate_score(evidences, "V2") > simulate_score(evidences, "V0")
    assert simulate_score(evidences, "V3") == simulate_score(
        evidences[:2], "V0"
    )
    assert classify(30.0, "V1") == "MEDIUM"
    assert classify(30.0, "V0") == "LOW"


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError):
        simulate_score([], "V9")
