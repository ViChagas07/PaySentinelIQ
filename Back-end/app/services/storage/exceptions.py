# ============================================================
# PaySentinelIQ — Storage Exceptions
# ============================================================


class StorageError(Exception):
    """Base exception for storage-related errors."""

    def __init__(self, message: str, key: str | None = None):
        self.key = key
        super().__init__(message)


class FileTooLargeError(StorageError):
    """Raised when uploaded file exceeds the size limit."""

    def __init__(self, size_bytes: int, max_bytes: int):
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes
        super().__init__(
            f"File size {size_bytes / 1_048_576:.1f}MB exceeds limit of {max_bytes / 1_048_576:.0f}MB"
        )


class InvalidFileTypeError(StorageError):
    """Raised when uploaded file type is not allowed."""

    def __init__(self, file_type: str, allowed: list[str]):
        self.file_type = file_type
        self.allowed = allowed
        super().__init__(
            f"File type '{file_type}' is not allowed. Accepted: {', '.join(allowed)}"
        )


class FileNotFoundError(StorageError):
    """Raised when a requested file does not exist in storage."""

    def __init__(self, key: str):
        super().__init__(f"File not found in storage: {key}", key=key)


class UploadFailedError(StorageError):
    """Raised when upload to storage backend fails."""

    def __init__(self, key: str, reason: str):
        super().__init__(f"Upload failed for {key}: {reason}", key=key)
