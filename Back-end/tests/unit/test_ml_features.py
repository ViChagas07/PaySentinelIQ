import math

import numpy as np

from app.ml.features import (
    FEATURE_NAMES,
    FORBIDDEN_FEATURE_TOKENS,
    align_features,
    vectorize,
)


def _row(**overrides):
    row = {
        "document_type": "boleto",
        "path": "A_native",
        "extracted_fields": {
            "linha_digitavel": "0019" + "0" * 43,
            "valor_nominal": 100.0,
            "data_vencimento": "20/01/2027",
            "codigo_banco": "001",
        },
        "evidences": [],
        "warnings": [],
        "errors": [],
    }
    row.update(overrides)
    return row


def test_feature_names_have_no_forbidden_tokens():
    for token in FORBIDDEN_FEATURE_TOKENS:
        assert not any(token in name for name in FEATURE_NAMES)


def test_vector_has_fixed_shape_and_missing_values_become_nan():
    vector = vectorize(_row())

    assert vector.shape == (len(FEATURE_NAMES),)
    index = FEATURE_NAMES.index("inss_gross")
    assert math.isnan(vector[index])


def test_align_features_ignores_unknown_and_fills_missing():
    values = {"evidence_total": 3, "desconhecida": 99}
    vector = align_features(values)

    assert vector.shape == (len(FEATURE_NAMES),)
    assert vector[FEATURE_NAMES.index("evidence_total")] == 3
    assert math.isnan(vector[FEATURE_NAMES.index("field_missing_count")])


def test_gabarito_and_tamper_metadata_do_not_change_features():
    first = _row()
    second = _row(
        gabarito_fields={"valor_nominal": "999.00"},
        tamper_types=["B1"],
        sophistication="expert",
        intended_band="HIGH",
    )

    assert np.array_equal(vectorize(first), vectorize(second), equal_nan=True)


def test_evidence_signal_changes_features():
    without = vectorize(_row())
    with_critical = vectorize(
        _row(
            evidences=[
                {
                    "code": "BOLETO_AMOUNT_MISMATCH",
                    "severity": "critical",
                    "source": "deterministic",
                    "confidence": 1.0,
                    "metadata": {},
                }
            ]
        )
    )
    index = FEATURE_NAMES.index("evidence_confirmed_critical")

    assert with_critical[index] == 1
    assert without[index] == 0
