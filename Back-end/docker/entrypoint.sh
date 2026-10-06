#!/bin/sh
# ============================================================
# PaySentinelIQ — Production Entrypoint
# Runs alembic migrations (with pgvector extension) then starts uvicorn
# ============================================================

set -e

echo "[psi] Entrypoint started"
echo "[psi] ENVIRONMENT=${ENVIRONMENT}"

# Wait for PostgreSQL to be ready (Render internal DB may need a moment)
echo "[psi] Waiting for PostgreSQL..."
until pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-psi}" -d "${DATABASE_NAME:-paysentineliq}" > /dev/null 2>&1; do
    echo "[psi] PostgreSQL not ready, waiting..."
    sleep 2
done
echo "[psi] PostgreSQL is ready"

# Ensure pgvector extension exists (idempotent, runs as superuser via psql)
# On Render managed Postgres, we may not have superuser; the extension
# should be pre-installed or created by the first migration.
# We try to create it but don't fail if we lack permissions.
echo "[psi] Ensuring pgvector extension..."
psql "${DATABASE_URL}" -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "[psi] pgvector extension creation skipped (may require superuser or already exists)"

# Run alembic migrations
echo "[psi] Running alembic upgrade head..."
alembic upgrade head

echo "[psi] Migrations complete, starting uvicorn..."
exec "$@"