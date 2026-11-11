FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/models

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && (pip uninstall -y opencv-python opencv-contrib-python || true) \
    && pip install --no-cache-dir --force-reinstall --no-deps \
        opencv-python-headless==4.10.0.84

RUN python -c "import pyclipper, scipy, skimage; print('ocr dependencies ok')"

COPY app ./app

RUN groupadd --gid 10001 ocr \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /models ocr \
    && mkdir -p /models \
    && chown -R ocr:ocr /app /models

RUN python -c "import scipy, skimage; from paddleocr import PaddleOCR; PaddleOCR(lang='latin', use_angle_cls=True, use_gpu=False, show_log=False)"

RUN chown -R ocr:ocr /models

USER ocr

ENV OCR_SERVICE_MAX_MB=25 \
    OCR_SERVICE_MAX_PAGES=10 \
    OCR_SERVICE_DPI=300 \
    OCR_SERVICE_FORCE_FALLBACK=0 \
    OCR_SERVICE_PORT=8010

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
