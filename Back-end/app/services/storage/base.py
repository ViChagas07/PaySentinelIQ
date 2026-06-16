# ============================================================
# PaySentinelIQ — Storage Provider Interface + Models
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class StoredFile:
    """Represents a file stored in the storage backend."""

    key: str  # S3 key / path
    bucket: str
    size_bytes: int
    content_type: str
    etag: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class UploadResult:
    """Result of a file upload operation."""

    success: bool
    key: str
    bucket: str
    presigned_url: str | None = None
    error_message: str | None = None


class StorageProvider(ABC):
    """Abstract storage provider — S3 today, any backend tomorrow."""

    @abstractmethod
    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> UploadResult:
        """Upload a file to storage."""
        ...

    @abstractmethod
    async def download_file(self, key: str) -> bytes:
        """Download a file from storage."""
        ...

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete a file from storage."""
        ...

    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        ...

    @abstractmethod
    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a time-limited presigned URL for secure access."""
        ...
