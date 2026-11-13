from __future__ import annotations

from app.services.storage.base import StorageProvider, UploadResult
from app.services.storage.exceptions import (
    FileNotFoundError,
    UploadFailedError,
)


class InMemoryStorageProvider(StorageProvider):
    """Small in-memory storage implementation for unit tests.

    It records uploads/deletes so tests can assert the exact bytes, keys and
    compensation behavior without touching S3 or the network.
    """

    def __init__(self, bucket: str = "test-bucket") -> None:
        self.bucket = bucket
        self.objects: dict[str, bytes] = {}
        self.uploaded_keys: list[str] = []
        self.uploaded_blobs: list[bytes] = []
        self.uploaded_content_types: list[str] = []
        self.uploaded_metadata: list[dict[str, str] | None] = []
        self.deleted_keys: list[str] = []
        self.fail_upload = False
        self.fail_delete = False
        self.fail_delete_with_exception = False

    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> UploadResult:
        if self.fail_upload:
            raise UploadFailedError(key, "simulated upload failure")
        if not file_data:
            raise UploadFailedError(key, "empty file data")
        self.objects[key] = file_data
        self.uploaded_keys.append(key)
        self.uploaded_blobs.append(file_data)
        self.uploaded_content_types.append(content_type)
        self.uploaded_metadata.append(metadata)
        return UploadResult(
            success=True,
            key=key,
            bucket=self.bucket,
            presigned_url=f"https://storage.test/{self.bucket}/{key}",
        )

    async def download_file(self, key: str) -> bytes:
        if key not in self.objects:
            raise FileNotFoundError(key)
        return self.objects[key]

    async def delete_file(self, key: str) -> bool:
        if self.fail_delete_with_exception:
            raise RuntimeError("simulated delete failure")
        if self.fail_delete:
            return False
        self.deleted_keys.append(key)
        self.objects.pop(key, None)
        return True

    async def file_exists(self, key: str) -> bool:
        return key in self.objects

    async def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
    ) -> str:
        return f"https://storage.test/{self.bucket}/{key}"
