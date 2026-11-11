from __future__ import annotations

import importlib
import importlib.util
import logging
import threading
import time
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OCRServiceError(Exception):
    pass


class PageLimitError(OCRServiceError):
    def __init__(self, page_count: int, max_pages: int) -> None:
        self.page_count = page_count
        self.max_pages = max_pages
        super().__init__(
            f"Document has {page_count} pages, exceeding OCR_MAX_PAGES={max_pages}"
        )


class UnsupportedFileError(OCRServiceError):
    pass


@dataclass
class _PageImage:
    image: Any
    width: int
    height: int


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "N/A"


def _parse_v2_result(raw: Any) -> tuple[str, float]:
    if not raw:
        return "", 0.0

    first = raw[0] if isinstance(raw, list) else raw
    lines = first if isinstance(first, list) else []

    texts: list[str] = []
    scores: list[float] = []
    for item in lines:
        if not item or not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        payload = item[1]
        if isinstance(payload, (list, tuple)) and len(payload) >= 2:
            text = str(payload[0])
            score = float(payload[1])
        elif isinstance(payload, str):
            text = payload
            score = 0.0
        else:
            continue
        if text.strip():
            texts.append(text.strip())
            scores.append(max(0.0, min(1.0, score)))

    if not texts:
        return "", 0.0
    return "\n".join(texts), round(sum(scores) / len(scores), 4)


def _parse_v3_result(raw: Any) -> tuple[str, float]:
    texts: list[str] = []
    scores: list[float] = []

    for page in raw or []:
        data: Any = page
        if hasattr(page, "json"):
            data = page.json
        elif hasattr(page, "res"):
            data = page.res
        if not isinstance(data, dict):
            continue
        result = data.get("res", data)
        if not isinstance(result, dict):
            continue
        page_texts = result.get("rec_texts") or []
        page_scores = result.get("rec_scores") or []
        for index, text in enumerate(page_texts):
            if not text:
                continue
            score = (
                float(page_scores[index])
                if index < len(page_scores)
                else 0.0
            )
            texts.append(str(text))
            scores.append(max(0.0, min(1.0, score)))

    if not texts:
        return "", 0.0
    return "\n".join(texts), round(sum(scores) / len(scores), 4)


class OCREngine:
    def __init__(
        self,
        default_dpi: int = 300,
        max_pages: int = 10,
        force_fallback: bool = False,
    ) -> None:
        self._default_dpi = default_dpi
        self._max_pages = max_pages
        self._force_fallback = force_fallback
        self._paddle_engine: Any = None
        self._paddle_version: str | None = None
        self._paddle_error: str | None = None
        self._init_lock = threading.Lock()
        self._ocr_lock = threading.Lock()

    @property
    def paddle_ready(self) -> bool:
        return self._paddle_engine is not None

    def is_ready(self) -> bool:
        return self.paddle_ready

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        dpi: int | None = None,
        max_pages: int | None = None,
        force_fallback: bool | None = None,
    ) -> dict[str, Any]:
        with self._ocr_lock:
            start_time = time.monotonic()
            effective_dpi = dpi or self._default_dpi
            effective_max_pages = max_pages or self._max_pages
            pages = self._load_pages(
                file_bytes,
                filename,
                effective_dpi,
                effective_max_pages,
            )

            use_fallback = (
                self._force_fallback
                if force_fallback is None
                else force_fallback
            )
            provider = "tesseract"
            used_fallback = True

            if not use_fallback:
                try:
                    page_results = self._run_paddle(pages)
                    provider = "paddleocr"
                    used_fallback = False
                except Exception as exc:
                    logger.warning(
                        "PaddleOCR failed (%s); falling back to Tesseract",
                        type(exc).__name__,
                    )
                    page_results = self._run_tesseract(pages)
            else:
                page_results = self._run_tesseract(pages)

            duration_ms = int((time.monotonic() - start_time) * 1000)
            confidence = (
                sum(page["confidence"] for page in page_results)
                / len(page_results)
                if page_results
                else 0.0
            )
            text = "\n\n".join(page["text"] for page in page_results)

            logger.info(
                "ocr completed provider=%s pages=%d bytes=%d "
                "duration_ms=%d fallback=%s",
                provider,
                len(page_results),
                len(file_bytes),
                duration_ms,
                used_fallback,
            )

            return {
                "text": text,
                "pages": page_results,
                "confidence": round(confidence, 4),
                "provider": provider,
                "processing_time_seconds": round(duration_ms / 1000, 2),
                "metadata": {
                    "dpi": str(effective_dpi),
                    "page_count": str(len(page_results)),
                    "duration_ms": str(duration_ms),
                    "fallback": str(used_fallback).lower(),
                    "languages": (
                        "latin" if provider == "paddleocr" else "por+spa+eng"
                    ),
                },
            }

    def _ensure_paddle(self) -> tuple[Any, str]:
        if self._paddle_engine is not None:
            return self._paddle_engine, self._paddle_version or ""
        if self._paddle_error is not None:
            raise OCRServiceError(self._paddle_error)

        with self._init_lock:
            if self._paddle_engine is not None:
                return self._paddle_engine, self._paddle_version or ""
            if self._paddle_error is not None:
                raise OCRServiceError(self._paddle_error)

            if importlib.util.find_spec("paddleocr") is None:
                self._paddle_error = "PaddleOCR is not installed"
                raise OCRServiceError(self._paddle_error)

            try:
                try:
                    importlib.import_module("scipy")
                    importlib.import_module("skimage")
                except Exception:
                    pass
                paddleocr_module = importlib.import_module("paddleocr")
                engine_version = _package_version("paddleocr")
                if engine_version.startswith("3."):
                    try:
                        paddle = importlib.import_module("paddle")
                        paddle.set_flags({"FLAGS_use_mkldnn": False})
                    except Exception:
                        pass
                    try:
                        engine = paddleocr_module.PaddleOCR(
                            lang="latin",
                            device="cpu",
                            use_doc_orientation_classify=True,
                            use_doc_unwarping=False,
                            use_textline_orientation=True,
                            enable_mkldnn=False,
                        )
                    except TypeError:
                        engine = paddleocr_module.PaddleOCR(
                            lang="latin",
                            device="cpu",
                            use_doc_orientation_classify=True,
                            use_doc_unwarping=False,
                            use_textline_orientation=True,
                        )
                else:
                    engine = paddleocr_module.PaddleOCR(
                        lang="latin",
                        use_angle_cls=True,
                        use_gpu=False,
                        show_log=False,
                    )
            except Exception as exc:
                self._paddle_error = (
                    f"PaddleOCR initialization failed: {type(exc).__name__}"
                )
                raise OCRServiceError(self._paddle_error) from exc

            self._paddle_engine = engine
            self._paddle_version = engine_version
            return engine, engine_version

    def _load_pages(
        self,
        file_bytes: bytes,
        filename: str,
        dpi: int,
        max_pages: int,
    ) -> list[_PageImage]:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            fitz = importlib.import_module("fitz")
            from PIL import Image

            document = fitz.open(stream=file_bytes, filetype="pdf")
            try:
                if document.page_count > max_pages:
                    raise PageLimitError(document.page_count, max_pages)
                pages: list[_PageImage] = []
                for page in document:
                    pixmap = page.get_pixmap(dpi=dpi, alpha=False)
                    mode = "RGB" if pixmap.n == 3 else "RGBA"
                    image = Image.frombytes(
                        mode,
                        (pixmap.width, pixmap.height),
                        pixmap.samples,
                    ).convert("RGB")
                    pages.append(
                        _PageImage(
                            image=image,
                            width=pixmap.width,
                            height=pixmap.height,
                        )
                    )
                return pages
            finally:
                document.close()

        if suffix not in {".png", ".jpg", ".jpeg"}:
            raise UnsupportedFileError(f"Unsupported file type: {suffix}")

        from PIL import Image

        image = Image.open(BytesIO(file_bytes))
        image.load()
        image = image.convert("RGB")
        return [
            _PageImage(
                image=image,
                width=image.width,
                height=image.height,
            )
        ]

    def _run_paddle(self, pages: list[_PageImage]) -> list[dict[str, Any]]:
        import numpy as np

        engine, engine_version = self._ensure_paddle()
        results: list[dict[str, Any]] = []

        for page_number, page in enumerate(pages, start=1):
            image = np.asarray(page.image)[:, :, ::-1].copy()
            if engine_version.startswith("3."):
                raw = engine.predict(image)
                text, confidence = _parse_v3_result(raw)
            else:
                raw = engine.ocr(image, cls=True)
                text, confidence = _parse_v2_result(raw)
            results.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "confidence": confidence,
                    "width": page.width,
                    "height": page.height,
                }
            )
        return results

    def _run_tesseract(self, pages: list[_PageImage]) -> list[dict[str, Any]]:
        try:
            pytesseract = importlib.import_module("pytesseract")
        except ImportError as exc:
            raise OCRServiceError("Tesseract is not installed") from exc

        results: list[dict[str, Any]] = []
        for page_number, page in enumerate(pages, start=1):
            try:
                data = pytesseract.image_to_data(
                    page.image,
                    lang="por+spa+eng",
                    output_type=pytesseract.Output.DICT,
                    config="--psm 6",
                )
            except Exception as exc:
                raise OCRServiceError(
                    f"Tesseract OCR failed: {type(exc).__name__}"
                ) from exc

            lines: dict[tuple[int, int, int], list[str]] = {}
            confidences: list[float] = []
            texts = data.get("text", [])
            confs = data.get("conf", [])
            blocks = data.get("block_num", [])
            paragraphs = data.get("par_num", [])
            line_numbers = data.get("line_num", [])
            for index, word in enumerate(texts):
                confidence = confs[index] if index < len(confs) else "-1"
                if not word.strip() or confidence in ("-1", -1):
                    continue
                key = (
                    blocks[index] if index < len(blocks) else 0,
                    paragraphs[index] if index < len(paragraphs) else 0,
                    line_numbers[index] if index < len(line_numbers) else 0,
                )
                lines.setdefault(key, []).append(word.strip())
                confidences.append(
                    max(0.0, min(1.0, float(confidence) / 100.0))
                )

            page_text = "\n".join(
                " ".join(words)
                for _, words in sorted(lines.items())
            )
            results.append(
                {
                    "page_number": page_number,
                    "text": page_text,
                    "confidence": (
                        round(sum(confidences) / len(confidences), 4)
                        if confidences
                        else 0.0
                    ),
                    "width": page.width,
                    "height": page.height,
                }
            )
        return results
