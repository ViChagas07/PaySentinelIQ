FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl tesseract-ocr tesseract-ocr-por tesseract-ocr-eng poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files first (cache layer)
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-lock

# Copy application code
COPY . .

# Non-root user
RUN groupadd -r psi && useradd -r -g psi psi
RUN chown -R psi:psi /app
USER psi

# Render injects PORT
EXPOSE 8000

# Run migrations then start
CMD ["sh", "-c", "poetry run alembic upgrade head && poetry run uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --workers 1 --ws-ping-interval 30 --ws-ping-timeout 10 --ws-max-size 1048576"]