import pytest

from app.shared.settings import Settings


def _settings(**overrides):
    values = {
        "ENVIRONMENT": "development",
        "LLM_PROFILE": "",
        "LLM_PROVIDER": "",
        "LLM_BASE_URL": "",
        "LLM_API_KEY": None,
        "LLM_MODEL": "",
        "LLM_TIMEOUT": None,
        "LLM_MAX_RETRIES": 3,
        "LLM_REASONING_EFFORT": "none",
        "LLM_MAX_CONCURRENCY": None,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_local_profile_overrides_production_environment():
    settings = _settings(ENVIRONMENT="production", LLM_PROFILE="local")

    assert settings.effective_llm_provider == "openai_compatible"
    assert settings.LLM_BASE_URL == "http://localhost:1234/v1"
    assert settings.LLM_TIMEOUT == 180
    assert settings.LLM_MAX_CONCURRENCY == 1
    assert settings.LLM_REASONING_EFFORT == "none"


def test_cloud_profile_uses_cloud_defaults():
    settings = _settings(
        ENVIRONMENT="production",
        LLM_PROFILE="cloud",
        LLM_BASE_URL="https://llm.example.com/v1",
        LLM_MODEL="cloud-model",
        LLM_API_KEY="cloud-secret",
    )

    assert settings.effective_llm_provider == "openai_compatible"
    assert settings.LLM_BASE_URL == "https://llm.example.com/v1"
    assert settings.LLM_TIMEOUT == 60
    assert settings.LLM_MAX_CONCURRENCY == 4
    assert settings.LLM_MODEL == "cloud-model"
    assert settings.LLM_API_KEY is not None
    assert settings.LLM_API_KEY.get_secret_value() == "cloud-secret"


def test_profile_explicit_values_are_preserved():
    settings = _settings(
        ENVIRONMENT="production",
        LLM_PROFILE="local",
        LLM_BASE_URL="http://custom:9999/v1",
        LLM_MODEL="custom-model",
        LLM_TIMEOUT=42,
        LLM_MAX_CONCURRENCY=7,
    )

    assert settings.LLM_BASE_URL == "http://custom:9999/v1"
    assert settings.LLM_MODEL == "custom-model"
    assert settings.LLM_TIMEOUT == 42
    assert settings.LLM_MAX_CONCURRENCY == 7


@pytest.mark.parametrize(
    ("environment", "provider", "expected"),
    [
        ("development", "", "ollama"),
        ("demo", "", "ollama"),
        ("production", "", "gemini"),
        ("production", "ollama", "gemini"),
        ("production", "mock", "gemini"),
        ("production", "gemini", "gemini"),
        ("production", "openai", "openai"),
        ("production", "openai_compatible", "openai_compatible"),
        ("production", "lmstudio", "lmstudio"),
    ],
)
def test_empty_profile_preserves_effective_provider(
    environment, provider, expected
):
    settings = _settings(ENVIRONMENT=environment, LLM_PROVIDER=provider)

    assert settings.effective_llm_provider == expected


@pytest.mark.parametrize("provider", ["openai_compatible", "lmstudio"])
def test_new_provider_names_are_accepted(provider):
    settings = _settings(LLM_PROVIDER=provider)

    assert settings.LLM_PROVIDER == provider


def test_profile_does_not_change_shared_generation_settings():
    local = _settings(ENVIRONMENT="production", LLM_PROFILE="local")
    cloud = _settings(
        ENVIRONMENT="production",
        LLM_PROFILE="cloud",
        LLM_BASE_URL="https://llm.example.com/v1",
        LLM_API_KEY="cloud-secret",
    )

    assert local.effective_ai_temperature == cloud.effective_ai_temperature
    assert local.effective_ai_max_tokens == cloud.effective_ai_max_tokens
    assert local.effective_ai_temperature == 0.1
    assert local.effective_ai_max_tokens == 4096
