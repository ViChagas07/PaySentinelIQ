from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.ml.dataset import Dataset
from app.ml.evaluate import build_logistic
from app.ml.features import FEATURE_NAMES, align_features


def _dataset() -> Dataset:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(40, len(FEATURE_NAMES)))
    y = np.array([0] * 20 + [1] * 20, dtype=np.int8)
    X[y == 1, FEATURE_NAMES.index("evidence_confirmed_material")] += 3
    meta = [
        {
            "document_id": f"doc-{index}",
            "split": "train",
            "language": "pt",
            "layout": "A",
            "document_type": "boleto",
            "is_fraud": bool(label),
            "sophistication": "naive" if label else None,
            "tamper_types": ["B1"] if label else [],
            "path": "A_native",
            "score": 0.0,
            "risk_level": "LOW",
        }
        for index, label in enumerate(y)
    ]
    return Dataset(X=X, y=y, meta=meta, feature_names=list(FEATURE_NAMES))


def test_preprocessing_and_model_are_inside_pipeline():
    model = build_logistic(1.0)

    assert isinstance(model, Pipeline)
    assert list(model.named_steps) == ["imputer", "scaler", "model"]


def test_imputer_is_fitted_on_train_only():
    dataset = _dataset()
    train = Dataset(
        X=dataset.X[:30],
        y=dataset.y[:30],
        meta=dataset.meta[:30],
        feature_names=dataset.feature_names,
    )
    model = build_logistic(1.0)
    model.fit(train.X, train.y)
    imputer = model.named_steps["imputer"]
    index = FEATURE_NAMES.index("inss_gross")

    assert np.isclose(
        imputer.statistics_[index],
        np.nanmedian(train.X[:, index]),
    )


def test_training_is_reproducible_and_joblib_roundtrips(tmp_path):
    dataset = _dataset()
    first = build_logistic(1.0)
    second = build_logistic(1.0)
    first.fit(dataset.X, dataset.y)
    second.fit(dataset.X, dataset.y)

    assert np.allclose(
        first.predict_proba(dataset.X),
        second.predict_proba(dataset.X),
    )

    path = tmp_path / "model.joblib"
    joblib.dump(first, path)
    loaded = joblib.load(path)
    assert np.allclose(
        loaded.predict_proba(dataset.X),
        first.predict_proba(dataset.X),
    )


def test_missing_or_unknown_feature_does_not_break_inference():
    dataset = _dataset()
    model = build_logistic(1.0)
    model.fit(dataset.X, dataset.y)

    vector = align_features({"evidence_total": 2, "unknown_feature": 1})
    probabilities = model.predict_proba(vector.reshape(1, -1))

    assert probabilities.shape == (1, 2)
    assert np.isfinite(probabilities).all()


def test_ml_code_has_no_llm_or_network_imports():
    root = Path(__file__).resolve().parents[2] / "app" / "ml"
    forbidden = (
        "requests",
        "httpx",
        "aiohttp",
        "openai",
        "app.ai_agents",
        "websocket",
        "urllib.request",
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"


def test_pipeline_and_api_do_not_import_ml():
    root = Path(__file__).resolve().parents[2] / "app"
    for directory in (root / "services" / "pipeline", root / "api"):
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "app.ml" not in text, f"{path} imports app.ml"
