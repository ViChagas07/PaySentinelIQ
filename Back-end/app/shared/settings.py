# ============================================================
# PaySentinelIQ — Application Settings (pydantic-settings)
# All config from env vars — never hardcode secrets
# ============================================================

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──
    APP_NAME: str = "PaySentinelIQ"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production|test)$",
    )
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # ── Database (PostgreSQL) ──
    DATABASE_URL: SecretStr = Field(
        default=SecretStr("postgresql+asyncpg://psi:psi_secret@localhost:5432/paysentineliq"),
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # ── Celery ──
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540

    # ── Auth / JWT ──
    JWT_SECRET_KEY: SecretStr = Field(default=SecretStr("change-me-in-production-use-256-bit-key"))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER: str = "PaySentinelIQ"

    # ── Google OIDC ──
    GOOGLE_CLIENT_ID: str = ""

    # ── AWS ──
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: SecretStr | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "psi-documents"
    S3_PRESIGNED_URL_EXPIRY: int = 3600
    AWS_TEXTRACT_ROLE_ARN: str | None = None

    # ── AI / LLM Provider Selection ──
    # Supported providers: ollama, openai, anthropic, bedrock, groq, gemini
    # Default is 'ollama' for zero-cost local inference.
    LLM_PROVIDER: str = Field(
        default="ollama",
        pattern="^(ollama|openai|anthropic|bedrock|groq|gemini)$",
    )

    # ── Shared LLM Settings ──
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 4096

    # ── Ollama (Local LLM) ──
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: float = 120.0  # seconds — local models can be slower
    OLLAMA_MAX_RETRIES: int = 3
    OLLAMA_NUM_GPU: int | None = None  # None = auto-detect; set to 0 for CPU-only
    OLLAMA_NUM_THREAD: int | None = None  # None = auto-detect

    # ── OpenAI (Cloud LLM — optional, for fallback or specific use cases) ──
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL: str = "gpt-4o"

    # ── Gemini (Google AI — production cloud LLM) ──
    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Anthropic (Cloud LLM — reserved for future use) ──
    ANTHROPIC_API_KEY: SecretStr | None = None

    # ── Sentry ──
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1

    # ── Rate Limiting ──
    RATE_LIMIT_PER_USER: int = 100  # requests per window
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_LOGIN_MAX: int = 5  # attempts per window

    # ── Feature Flags ──
    ENABLE_AI_AGENTS: bool = True
    ENABLE_OCR: bool = True
    ENABLE_COMPLIANCE_CHECKS: bool = True

    # ── Business ──
    MAX_UPLOAD_SIZE_MB: int = 50
    RISK_SCORE_THRESHOLD_HIGH: int = 70
    RISK_SCORE_THRESHOLD_CRITICAL: int = 85
    DOCUMENT_RETENTION_DAYS: int = 2555  # 7 years for payroll records


@lru_cache
def get_settings() -> Settings:
    return Settings()
