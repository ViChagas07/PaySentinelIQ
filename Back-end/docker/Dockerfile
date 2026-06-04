FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (compilers, PostgreSQL headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and project dependencies into an in-project virtualenv.
# With package-mode=false, pip install . would fail, so we use poetry install.
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-interaction --no-ansi

# ─────────────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user
RUN groupadd -r psi && useradd -r -g psi psi

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the project's virtualenv site-packages (not Poetry's own deps).
# This avoids bringing build‑time tools into production.
COPY --from=builder /app/.venv/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/.venv/bin /usr/local/bin

# Upgrade any vulnerable packages that may have leaked in from the base
# image or tooling (e.g. wheel from python:3.11-slim, jaraco.context
# from pip install poetry).  Keeping Trivy HIGH/CRITICAL-free.
RUN pip install --no-cache-dir --upgrade \
    wheel==0.46.2 \
    "jaraco.context>=6.1.0"

# Application code
COPY . .

# Fix ownership
RUN chown -R psi:psi /app
USER psi

EXPOSE 8000

# Run with 4 workers
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
