from app.synthetic.policy_6a import _score, v5_decision


def _evidence(
    code: str,
    severity: str,
    source: str = "deterministic",
    confidence: float = 1.0,
    ocr_uncertain: bool = False,
) -> dict:
    metadata = {"ocr_uncertain": True} if ocr_uncertain else {}
    return {
        "code": code,
        "severity": severity,
        "source": source,
        "confidence": confidence,
        "metadata": metadata,
    }


def _item(evidences: list[dict], extracted: dict | None = None) -> dict:
    return {
        "path": "A_native",
        "document_type": "boleto",
        "evidences": evidences,
        "extracted_fields": extracted
        or {
            "linha_digitavel": "0019" + "0" * 43,
            "valor_nominal": 100.0,
            "data_vencimento": "20/01/2027",
        },
    }


def test_v4_increases_confirmed_deterministic_but_not_ocr_uncertain():
    confirmed = [_evidence("BOLETO_AMOUNT_MISMATCH", "high")]
    uncertain = [_evidence("BOLETO_AMOUNT_MISMATCH", "high", ocr_uncertain=True)]

    assert _score(confirmed, "V4") > _score(confirmed, "V0")
    assert _score(uncertain, "V4") == _score(uncertain, "V0")


def test_v5_temporal_info_does_not_confirm_adulteration():
    item = _item(
        [
            _evidence("BOLETO_OVERDUE", "info"),
            _evidence("BOLETO_VENCIDO", "info"),
            _evidence("DOCUMENT_EXPIRED", "info"),
        ]
    )

    decision = v5_decision(item)

    assert decision["decision"] == "LOW"
    assert decision["needs_review"] is False


def test_v5_requires_independent_confirmed_groups_for_high():
    single = v5_decision(
        _item([_evidence("BOLETO_AMOUNT_MISMATCH", "high")])
    )
    independent = v5_decision(
        _item(
            [
                _evidence("BOLETO_AMOUNT_MISMATCH", "high"),
                _evidence("BANCO_INVALIDO", "high"),
            ]
        )
    )

    assert single["decision"] == "MEDIUM"
    assert independent["decision"] == "HIGH"


def test_v5_marks_ocr_uncertain_material_as_review():
    item = _item(
        [
            _evidence(
                "BOLETO_AMOUNT_MISMATCH",
                "critical",
                ocr_uncertain=True,
            )
        ]
    )
    item["path"] = "C_ocr_degraded"

    decision = v5_decision(item)

    assert decision["decision"] == "MEDIUM"
    assert decision["needs_review"] is True


def test_v5_marks_missing_extraction_as_review():
    item = _item(
        [_evidence("BOLETO_AMOUNT_MISMATCH", "high")],
        extracted={"linha_digitavel": "0019" + "0" * 43},
    )

    decision = v5_decision(item)

    assert decision["needs_review"] is True
    assert "valor_nominal" in decision["missing_fields"]
    assert "data_vencimento" in decision["missing_fields"]
