# ============================================================
# PaySentinelIQ — Upload validation
# Content, format, structure and resource-limit checks for
# original document uploads before OCR/LLM/storage/persistence.
# ============================================================

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import fitz
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.services.storage.file_validator import (
    ALLOWED_MIME_TYPES,
    BLOCKED_EXTENSIONS,
)
from app.shared.settings import Settings

_CHUNK_SIZE = 64 * 1024
_GENERIC_MIME_TYPES = {"", "application/octet-stream", "binary/octet-stream"}
_EXTENSION_BY_TYPE = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}
_TYPE_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class UploadValidationError(Exception):
    """Controlled upload rejection with a public, non-sensitive message."""

    def __init__(self, status_code: int, public_message: str) -> None:
        super().__init__(public_message)
        self.status_code = status_code
        self.public_message = public_message


@dataclass(frozen=True)
class UploadPolicy:
    max_file_bytes: int
    max_pdf_pages: int
    max_pdf_page_dimension_pt: float
    max_pdf_page_area_pt2: float
    max_image_pixels: int
    max_image_dimension: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "UploadPolicy":
        return cls(
            max_file_bytes=settings.max_upload_file_bytes,
            max_pdf_pages=settings.OCR_MAX_PAGES,
            max_pdf_page_dimension_pt=settings.MAX_PDF_PAGE_DIMENSION_PT,
            max_pdf_page_area_pt2=settings.MAX_PDF_PAGE_AREA_PT2,
            max_image_pixels=settings.MAX_IMAGE_PIXELS,
            max_image_dimension=settings.MAX_IMAGE_DIMENSION,
        )


@dataclass(frozen=True)
class ValidatedUpload:
    data: bytes
    content_type: str
    extension: str
    safe_filename: str
    original_filename: str


async def read_upload_limited(
    upload: UploadFile,
    max_bytes: int,
    chunk_size: int = _CHUNK_SIZE,
) -> bytes:
    """Read an UploadFile in bounded chunks, rejecting before unbounded growth."""
    if max_bytes <= 0 or chunk_size <= 0:
        raise UploadValidationError(413, "File exceeds the allowed size")

    chunks: list[bytes] = []
    total = 0
    while True:
        try:
            chunk = await upload.read(chunk_size)
        except Exception:
            raise UploadValidationError(
                400,
                "Upload could not be read",
            ) from None
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadValidationError(413, "File exceeds the allowed size")
        chunks.append(chunk)
    return b"".join(chunks)


def sanitize_filename(file_name: str | None) -> str:
    """Keep only a safe basename for metadata; never a server path."""
    raw = (file_name or "").replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(
        char
        for char in raw
        if ord(char) >= 32 and ord(char) != 127
    ).strip().strip(".")
    if not cleaned:
        return "document"
    return cleaned[:255]


def _detect_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def _normalized_mime(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def _check_declared_mime(declared: str | None, detected: str) -> None:
    normalized = _normalized_mime(declared)
    if normalized in _GENERIC_MIME_TYPES:
        return
    if normalized == "image/jpg":
        normalized = "image/jpeg"
    if normalized not in ALLOWED_MIME_TYPES:
        raise UploadValidationError(415, "Unsupported file type")
    if normalized != detected:
        raise UploadValidationError(
            415,
            "File content does not match the declared type",
        )


def _check_extension(file_name: str | None, detected: str) -> None:
    suffix = Path(sanitize_filename(file_name)).suffix.lower()
    if not suffix:
        return
    if suffix in BLOCKED_EXTENSIONS or suffix not in _TYPE_BY_EXTENSION:
        raise UploadValidationError(415, "Unsupported file type")
    if _TYPE_BY_EXTENSION[suffix] != detected:
        raise UploadValidationError(
            415,
            "File extension does not match the content",
        )


def _validate_pdf(data: bytes, policy: UploadPolicy) -> None:
    # A truncated PDF often loses its final EOF marker. This complements
    # PyMuPDF's repair tolerance without executing or rendering the document.
    if b"%%EOF" not in data[-4096:]:
        raise UploadValidationError(422, "Malformed or truncated PDF")

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise UploadValidationError(422, "Malformed or truncated PDF") from None

    try:
        try:
            if document.needs_pass:
                raise UploadValidationError(
                    415,
                    "Password-protected PDFs are not supported",
                )
            if document.page_count <= 0:
                raise UploadValidationError(422, "Malformed or empty PDF")
            if document.page_count > policy.max_pdf_pages:
                raise UploadValidationError(
                    422,
                    "PDF exceeds the maximum number of pages",
                )

            for page in document:
                rect = page.rect
                if (
                    rect.width <= 0
                    or rect.height <= 0
                    or rect.width > policy.max_pdf_page_dimension_pt
                    or rect.height > policy.max_pdf_page_dimension_pt
                    or rect.width * rect.height > policy.max_pdf_page_area_pt2
                ):
                    raise UploadValidationError(
                        422,
                        "PDF page dimensions exceed the allowed limit",
                    )
        except UploadValidationError:
            raise
        except Exception:
            raise UploadValidationError(422, "Malformed or truncated PDF") from None
    finally:
        document.close()


def _validate_image(data: bytes, detected: str, policy: UploadPolicy) -> None:
    expected_format = "PNG" if detected == "image/png" else "JPEG"

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != expected_format:
                raise UploadValidationError(
                    415,
                    "Image format does not match its content",
                )

            width, height = image.size
            if width <= 0 or height <= 0:
                raise UploadValidationError(
                    422,
                    "Malformed image dimensions",
                )
            if (
                width > policy.max_image_dimension
                or height > policy.max_image_dimension
                or width * height > policy.max_image_pixels
            ):
                raise UploadValidationError(
                    422,
                    "Image dimensions exceed the allowed limit",
                )
            if getattr(image, "n_frames", 1) != 1:
                raise UploadValidationError(
                    415,
                    "Multi-frame images are not supported",
                )
            image.verify()

        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except UploadValidationError:
        raise
    except Image.DecompressionBombError:
        raise UploadValidationError(
            422,
            "Image dimensions exceed the allowed limit",
        ) from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise UploadValidationError(
            422,
            "Malformed or truncated image",
        ) from None


def validate_upload_bytes(
    data: bytes,
    *,
    declared_content_type: str | None,
    file_name: str | None,
    policy: UploadPolicy,
) -> ValidatedUpload:
    """Validate exact bytes and return the server-authoritative type/name."""
    if not data:
        raise UploadValidationError(400, "File is empty")
    if len(data) > policy.max_file_bytes:
        raise UploadValidationError(413, "File exceeds the allowed size")

    detected = _detect_type(data)
    if detected is None:
        raise UploadValidationError(
            415,
            "Unsupported or unrecognized file type",
        )

    _check_declared_mime(declared_content_type, detected)
    _check_extension(file_name, detected)

    if detected == "application/pdf":
        _validate_pdf(data, policy)
    else:
        _validate_image(data, detected, policy)

    safe_name = sanitize_filename(file_name)
    return ValidatedUpload(
        data=data,
        content_type=detected,
        extension=_EXTENSION_BY_TYPE[detected],
        safe_filename=safe_name,
        original_filename=file_name or safe_name,
    )
