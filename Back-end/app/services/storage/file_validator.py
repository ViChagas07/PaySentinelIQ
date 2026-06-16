# ============================================================
# PaySentinelIQ — File Validator
# Pre-upload validation: type, size, MIME, security scan.
# ============================================================

from dataclasses import dataclass, field
from typing import BinaryIO
import logging

logger = logging.getLogger(__name__)

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Blocked extensions (security)
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".js", ".vbs", ".ps1",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".dll", ".so", ".dylib",
    ".sh", ".py", ".rb", ".pl",
}

# Default max file size: 10 MB
DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024


@dataclass
class FileValidationResult:
    """Result of file validation."""

    is_valid: bool
    file_name: str
    file_size_bytes: int
    content_type: str | None = None
    extension: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class FileValidator:
    """Validates uploaded files before storage/processing.

    Checks:
    - File size (max 10MB default)
    - File extension (allowed + blocked lists)
    - MIME type (PDF, PNG, JPG only)
    - Security: blocks executables, scripts, archives
    """

    def __init__(self, max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES):
        self._max_size = max_size_bytes

    def validate(
        self,
        file_name: str,
        file_size_bytes: int,
        content_type: str | None = None,
    ) -> FileValidationResult:
        """Validate a file before upload.

        Args:
            file_name: Original file name.
            file_size_bytes: File size in bytes.
            content_type: MIME type (optional).

        Returns:
            FileValidationResult with validity and error messages.
        """
        result = FileValidationResult(
            is_valid=True,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )

        # Extract extension
        ext = self._get_extension(file_name)
        result.extension = ext

        # Check 1: Size
        if file_size_bytes > self._max_size:
            result.is_valid = False
            result.errors.append(
                f"File size ({file_size_bytes / 1_048_576:.1f}MB) exceeds "
                f"maximum ({self._max_size / 1_048_576:.0f}MB)"
            )

        # Check 2: Blocked extension
        if ext.lower() in BLOCKED_EXTENSIONS:
            result.is_valid = False
            result.errors.append(
                f"File type '{ext}' is blocked for security reasons"
            )

        # Check 3: Allowed extension
        elif ext.lower() not in ALLOWED_EXTENSIONS:
            if ext:
                result.is_valid = False
                result.errors.append(
                    f"File type '{ext}' is not supported. "
                    f"Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
                )

        # Check 4: MIME type
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            result.warnings.append(
                f"MIME type '{content_type}' is unusual for document upload"
            )

        # Check 5: Empty file
        if file_size_bytes == 0:
            result.is_valid = False
            result.errors.append("File is empty")

        if result.is_valid:
            logger.info(
                "File validation passed: %s (%d bytes, %s)",
                file_name, file_size_bytes, content_type or "unknown",
            )
        else:
            logger.warning(
                "File validation failed: %s — %s",
                file_name, "; ".join(result.errors),
            )

        return result

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """Extract lowercase file extension."""
        if "." not in file_name:
            return ""
        return "." + file_name.rsplit(".", 1)[-1].lower()
