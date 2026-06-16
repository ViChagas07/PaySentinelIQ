# Tesseract OCR Setup Guide for PaySentinelIQ

## Installation

### Windows

```powershell
# Option 1: winget (recommended)
winget install UB-Mannheim.TesseractOCR

# Option 2: Manual download
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
```

Add to system PATH or configure in `.env`:
```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng
```

### macOS

```bash
brew install tesseract tesseract-lang
```

### Docker

Add to your Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### Railway / Render

The `poppler-utils` package is required for PDF support (pdf2image dependency).

Add to `packages` or build script:
```
tesseract-ocr tesseract-ocr-por tesseract-ocr-eng poppler-utils
```

---

## Python Dependencies

Already in `pyproject.toml`:
```
pytesseract>=0.3.10
Pillow>=10.0.0
pdf2image>=1.16.0
```

Install with:
```bash
pip install pytesseract Pillow pdf2image
```

---

## Configuration

Environment variables (optional, defaults shown):

```env
OCR_PROVIDER=tesseract        # OCR provider: tesseract | textract (future)
OCR_LANGUAGE=por+eng          # Language codes for Tesseract
OCR_PREPROCESS=true           # Enable image preprocessing for accuracy
OCR_DPI=300                   # DPI for PDF-to-image conversion
```

Or directly in `app/shared/settings.py`:
```python
OCR_PROVIDER: str = "tesseract"
OCR_LANGUAGE: str = "por+eng"
OCR_PREPROCESS: bool = True
OCR_DPI: int = 300
```

---

## Verification

Run the health check:
```bash
python -c "
from app.services.ocr import get_ocr_provider
import asyncio

async def test():
    provider = get_ocr_provider()
    healthy = await provider.health_check()
    info = provider.get_info()
    print(f'Healthy: {healthy}')
    print(f'Info: {info}')

asyncio.run(test())
"
```

---

## Usage Example

```python
from app.services.ocr import get_ocr_provider, DocumentExtractionService

# Get provider singleton
ocr = get_ocr_provider()

# Extract text from document
result = await ocr.extract_text("/path/to/document.pdf")
print(f"Text: {result.full_text[:200]}...")
print(f"Confidence: {result.confidence:.2%}")
print(f"Pages: {result.page_count}")

# Extract structured fields
extractor = DocumentExtractionService()
extraction = extractor.extract(result.full_text)
print(f"CNPJ: {extraction.cnpj}")
print(f"Amounts: {extraction.amounts}")
print(f"Dates: {extraction.dates}")
```

---

## Future: Switching to AWS Textract

When ready to migrate to AWS Textract:

1. Implement `TextractOCRProvider(app/services/ocr/textract_provider.py)`:
```python
class TextractOCRProvider(OCRProvider):
    async def extract_text(self, file_path: str) -> OCRResult:
        # Use boto3 textract.detect_document_text()
        ...
```

2. Change config:
```env
OCR_PROVIDER=textract
```

3. That's it. No business logic changes needed. The `OCRProvider` interface and `OCRFactory` abstract everything.

---

## Troubleshooting

### "Tesseract is not installed"
- Verify Tesseract is installed: `tesseract --version`
- Set `TESSERACT_CMD` environment variable to the full path of tesseract.exe

### "PDF conversion failed"
- Install poppler: `apt-get install poppler-utils` (Linux) or download from https://github.com/oschwartz10612/poppler-windows (Windows)
- Ensure `pdf2image` can find poppler binaries

### "Low OCR accuracy"
- Increase DPI: `OCR_DPI=400`
- Try without preprocessing: `OCR_PREPROCESS=false`
- Use specific language: `OCR_LANGUAGE=por` (Portuguese only)

### "TesseractNotFoundError" in production
- Railway/Render/Docker: ensure `tesseract-ocr` is in the build image
- Set `TESSERACT_CMD=/usr/bin/tesseract` in environment variables
