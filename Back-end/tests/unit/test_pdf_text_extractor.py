import logging

import fitz

from app.services.ocr.pdf_text_extractor import extract_text_robust


def _pdf_bytes(pages: int = 2) -> bytes:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), f"pagina {index + 1}", fontsize=12)
    data = document.tobytes()
    document.close()
    return data


def test_valid_pdf_reports_page_count_without_fallback_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="psi.extractor"):
        result = extract_text_robust(_pdf_bytes(2), document_type="TEST")

    assert result["method"] in {"pymupdf", "pdfplumber", "pypdf"}
    pymupdf_attempt = next(
        attempt
        for attempt in result["all_attempts"]
        if attempt["method"] == "pymupdf"
    )
    assert pymupdf_attempt["pages"] == 2
    assert "PyMuPDF failed" not in caplog.text
    assert "document closed" not in caplog.text.lower()
    assert "pagina 1" in result["text"]
    assert "pagina 2" in result["text"]
