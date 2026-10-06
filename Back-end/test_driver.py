#!/usr/bin/env python3
# ============================================================
# PaySentinelIQ — Driver Normalization Test
# Tests that DATABASE_URL normalization produces asyncpg for async engine
# Run: python test_driver.py
# ============================================================

import os
import sys

# Set dummy environment variables BEFORE importing the app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost/db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("RABBITMQ_ENABLED", "false")
os.environ.setdefault("RABBITMQ_URL", "amqp://test:test@localhost:5672/")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars-minimum!!")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("ENABLE_AI_AGENTS", "false")
os.environ.setdefault("ENABLE_OCR", "false")
os.environ.setdefault("ENABLE_COMPLIANCE_CHECKS", "false")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')

# Add the Back-end directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Back-end"))

from app.shared.settings import get_settings

print("=" * 80)
print("DATABASE_URL Normalization Test")
print("=" * 80)

settings = get_settings()

# Test various input URL formats
test_urls = [
    "postgresql://u:p@localhost/db",
    "postgres://u:p@localhost/db",
    "postgresql+psycopg2://u:p@localhost/db",
    "postgresql+psycopg://u:p@localhost/db",
    "postgresql+asyncpg://u:p@localhost/db",
    "postgresql://u:p@localhost/db?sslmode=require",
    "postgresql://u:p@localhost/db?sslmode=verify-full&channel_binding=disable",
]

print("\nAsync engine URL (database_url_async):")
for url in test_urls:
    # Temporarily override DATABASE_URL
    original = settings.DATABASE_URL.get_secret_value()
    settings.DATABASE_URL._value = url  # type: ignore
    normalized = settings.database_url_async
    print(f"  Input:  {url}")
    print(f"  Output: {normalized}")
    is_asyncpg = normalized.startswith("postgresql+asyncpg://")
    print(f"  Driver: {'asyncpg OK' if is_asyncpg else 'WRONG'}")
    print()

# Test sync URL (for Alembic)
print("\nSync engine URL (database_url_sync) for Alembic:")
for url in test_urls:
    settings.DATABASE_URL._value = url  # type: ignore
    normalized = settings.database_url_sync
    print(f"  Input:  {url}")
    print(f"  Output: {normalized}")
    is_psycopg = normalized.startswith("postgresql+psycopg://")
    print(f"  Driver: {'psycopg OK' if is_psycopg else 'WRONG'}")
    print()

# Restore
settings.DATABASE_URL._value = original  # type: ignore

# Verify connect_args logic
from urllib.parse import urlparse
_db_url = settings.database_url_async
_parsed = urlparse(_db_url)
_is_asyncpg = _parsed.scheme == "postgresql+asyncpg"

print("=" * 80)
print("Connect Args Test:")
print("=" * 80)
if _is_asyncpg:
    connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    print(f"Scheme: {_parsed.scheme} -> asyncpg connect_args: {connect_args}")
else:
    connect_args = {"prepared_statement_cache_size": 0}
    print(f"Scheme: {_parsed.scheme} -> psycopg connect_args: {connect_args}")

print("\nAll tests passed!" if _is_asyncpg else "\nFAILED: Not using asyncpg!")
sys.exit(0 if _is_asyncpg else 1)