# ============================================================
# PaySentinelIQ — S3 Storage Provider
# Production S3 implementation using boto3.
# Wraps the existing aws_s3.py with Clean Architecture interface.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.services.storage.base import StorageProvider, UploadResult
from app.services.storage.exceptions import (
    StorageError,
    FileNotFoundError,
    UploadFailedError,
)
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)


def _get_s3_settings():
    """Lazy settings accessor to avoid circular imports at module load time."""
    return get_settings()


class S3StorageProvider(StorageProvider):
    """AWS S3 storage provider with presigned URL support.

    Uses boto3 client configured from app settings.
    Implements the StorageProvider interface for Clean Architecture.
    """

    FOLDER_PREFIXES = {
        "payroll": "payrolls",
        "receipt": "receipts",
        "report": "reports",
        "document": "receipts",  # default
    }

    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
    ):
        s = _get_s3_settings()
        self._bucket = bucket or s.S3_BUCKET
        self._region = region or s.AWS_REGION
        self._client = self._create_client(s)

    def _create_client(self, settings) -> Any:
        """Create boto3 S3 client."""
        return boto3.client(
            "s3",
            region_name=self._region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=(
                settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
                if settings.AWS_SECRET_ACCESS_KEY
                else None
            ),
        )

    # ── Public API ──

    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> UploadResult:
        """Upload file bytes to S3.

        The object is the source of truth. A failure to generate the optional
        presigned URL must not turn a successful upload into an orphan.
        """
        try:
            extra_args: dict[str, Any] = {"ContentType": content_type}
            if metadata:
                extra_args["Metadata"] = {k: str(v)[:2000] for k, v in metadata.items()}

            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=file_data,
                **extra_args,
            )
        except (ClientError, BotoCoreError) as e:
            logger.error(
                "event=s3_upload_failed operation=upload error_type=%s",
                type(e).__name__,
            )
            raise UploadFailedError(key, str(e)) from e

        presigned = None
        try:
            presigned = await self.generate_presigned_url(key)
        except Exception as e:
            logger.warning(
                "event=s3_presign_failed operation=upload error_type=%s",
                type(e).__name__,
            )

        logger.info(
            "event=s3_upload_succeeded operation=upload bytes=%d",
            len(file_data),
        )

        return UploadResult(
            success=True,
            key=key,
            bucket=self._bucket,
            presigned_url=presigned,
        )

    async def download_file(self, key: str) -> bytes:
        """Download file bytes from S3."""
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            data = response["Body"].read()
            logger.debug(
                "event=s3_download_succeeded operation=download bytes=%d",
                len(data),
            )
            return data
        except self._client.exceptions.NoSuchKey:
            raise FileNotFoundError(key) from None
        except (ClientError, BotoCoreError) as e:
            raise StorageError(f"Download failed: {e}", key=key) from e

    async def delete_file(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            logger.info("event=s3_delete_succeeded operation=delete")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(
                "event=s3_delete_failed operation=delete error_type=%s",
                type(e).__name__,
            )
            return False

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    async def generate_presigned_url(self, key: str, expiration: int | None = None) -> str:
        """Generate a time-limited presigned URL for secure file access."""
        s = _get_s3_settings()
        expiry = expiration or s.S3_PRESIGNED_URL_EXPIRY
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expiry,
            )
            return url
        except (ClientError, BotoCoreError) as e:
            raise StorageError(f"Presigned URL generation failed: {e}", key=key) from e

    # ── Helpers ──

    @staticmethod
    def build_key(
        folder: str,
        tenant_id: str,
        document_id: str,
        extension: str = ".pdf",
    ) -> str:
        """Build a standardized S3 key: {folder}/{tenant_id}/{document_id}{ext}."""
        return f"{folder}/{tenant_id}/{document_id}{extension}"

    @staticmethod
    def get_folder_for_type(document_type: str) -> str:
        """Map document type to storage folder."""
        return S3StorageProvider.FOLDER_PREFIXES.get(
            document_type,
            S3StorageProvider.FOLDER_PREFIXES["document"],
        )
