# ============================================================
# PaySentinelIQ — Upload Security (Fase 4)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field

# ── Magic bytes for supported types ──
MAGIC_BYTES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF-"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/webp": [b"RIFF"],
    "image/tiff": [b"II*\x00", b"MM\x00*"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024   # 50 MB
MAX_PAGES = 500
MIN_FILE_SIZE = 100                # 100 bytes minimum

DANGEROUS_EXTENSIONS = {".exe", ".dll", ".so", ".sh", ".bat", ".cmd", ".ps1", ".vbs", ".jar", ".war"}
DOUBLE_EXTENSIONS_BLOCKED = [".pdf.exe", ".pdf.zip", ".pdf.js", ".png.exe"]


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_file(filename: str, file_data: bytes, mime_type: str) -> ValidationResult:
    result = ValidationResult()

    # ── Size checks ──
    if len(file_data) == 0:
        result.is_valid = False
        result.errors.append("File is empty")
    if len(file_data) < MIN_FILE_SIZE:
        result.is_valid = False
        result.errors.append(f"File too small: {len(file_data)} bytes")
    if len(file_data) > MAX_FILE_SIZE:
        result.is_valid = False
        result.errors.append(f"File exceeds {MAX_FILE_SIZE // 1_048_576}MB limit")

    # ── Name checks ──
    name_lower = filename.lower()
    for ext in DANGEROUS_EXTENSIONS:
        if name_lower.endswith(ext):
            result.is_valid = False
            result.errors.append(f"Dangerous extension: {ext}")
    for double_ext in DOUBLE_EXTENSIONS_BLOCKED:
        if name_lower.endswith(double_ext):
            result.is_valid = False
            result.errors.append(f"Double extension blocked: {double_ext}")

    # ── Magic bytes validation ──
    expected_magic = MAGIC_BYTES.get(mime_type)
    if expected_magic and file_data:
        matched = any(file_data[:len(m)].startswith(m) for m in expected_magic)
        if not matched:
            result.is_valid = False
            result.errors.append(f"MIME type {mime_type} does not match file content")

    # ── Sanitize filename ──
    import re
    sanitized = re.sub(r'[^\w\-_. ]', '_', filename)[:200]
    if sanitized != filename:
        result.warnings.append("Filename contained special characters — sanitized")

    return result
