#!/usr/bin/env python3
# ============================================================
# PaySentinelIQ — Route Test Script
# Imports the app with dummy env vars and prints all routes.
# Run: python test_routes.py
# ============================================================

import os
import sys

# Set dummy environment variables BEFORE importing the app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
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

from app.main import create_app

print("=" * 80)
print("PaySentinelIQ Route Test")
print("=" * 80)

app = create_app()

print("\nAll registered routes:")
print("-" * 80)

routes = []
for route in app.routes:
    if hasattr(route, "methods") and hasattr(route, "path"):
        methods = ",".join(sorted(route.methods))
        routes.append((methods, route.path, route.name if hasattr(route, "name") else ""))

# Sort by path for readability
routes.sort(key=lambda x: x[1])

for methods, path, name in routes:
    print(f"  {methods:20s} {path}")

print("-" * 80)
print(f"Total routes: {len(routes)}")

# Check for critical auth routes
auth_routes = [
    ("POST", "/api/auth/google"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/mfa/verify"),
    ("GET", "/api/auth/me"),
    ("POST", "/api/auth/logout"),
]

print("\nCritical Auth Routes Check:")
print("-" * 80)
all_found = True
for method, path in auth_routes:
    found = any(r[0] == method and r[1] == path for r in routes)
    status = "[OK]" if found else "[MISSING]"
    if not found:
        all_found = False
    print(f"  {status}: {method} {path}")

print("-" * 80)
if all_found:
    print("All critical auth routes are registered!")
    sys.exit(0)
else:
    print("Some critical auth routes are MISSING!")
    sys.exit(1)