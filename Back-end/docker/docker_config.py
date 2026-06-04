# ============================================================
# PaySentinelIQ — Docker Setup
# Multi-service: API, Celery worker, PostgreSQL, Redis
# ============================================================

# Dockerfile
DOCKERFILE_CONTENT = r""" 
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# ── Production stage ──
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN groupadd -r psi && useradd -r -g psi psi

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN chown -R psi:psi /app
USER psi

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", \
    "--port", "8000", "--workers", "4"]
"""

# ── docker-compose.yml ──
DOCKER_COMPOSE_CONTENT = r"""
version: "3.9"

services:
  # ── PostgreSQL ──
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: psi
      POSTGRES_PASSWORD: psi_secret
      POSTGRES_DB: paysentineliq
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U psi -d paysentineliq"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Redis ──
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── FastAPI Application ──
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: production
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://psi:psi_secret@postgres:5432/paysentineliq
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── Celery Worker ──
  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: production
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://psi:psi_secret@postgres:5432/paysentineliq
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── Celery Beat (Scheduled Tasks) ──
  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: production
    command: celery -A app.tasks beat --loglevel=info
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://psi:psi_secret@postgres:5432/paysentineliq
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3
    depends_on:
      - redis
    restart: unless-stopped

  # ── Ollama — Local LLM (Optional, zero-cost) ──
  # Uncomment to run Ollama inside Docker. GPU recommended.
  # ollama:
  #   image: ollama/ollama:latest
  #   ports:
  #     - "11434:11434"
  #   volumes:
  #     - ollama_data:/root/.ollama
  #   environment:
  #     - OLLAMA_KEEP_ALIVE=24h
  #     - OLLAMA_HOST=0.0.0.0
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             count: 1
  #             capabilities: [gpu]
  #   restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  # ollama_data:
"""
