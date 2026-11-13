import io

import pytest
from botocore.exceptions import ClientError

from app.services.storage.exceptions import UploadFailedError
from app.services.storage.s3_storage import S3StorageProvider
from app.shared.settings import Settings


class FakeS3Client:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.content_types: dict[tuple[str, str], str] = {}
        self.fail_put = False

    def put_object(self, Bucket, Key, Body, **kwargs):
        if self.fail_put:
            raise ClientError(
                {"Error": {"Code": "500", "Message": "boom"}},
                "PutObject",
            )
        self.objects[(Bucket, Key)] = bytes(Body)
        self.content_types[(Bucket, Key)] = kwargs.get("ContentType")

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise self.exceptions.NoSuchKey()
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "HeadObject",
            )
        return {}

    def generate_presigned_url(self, *args, **kwargs):
        return "https://storage.test/presigned"


@pytest.fixture
def fake_client(monkeypatch):
    client = FakeS3Client()
    monkeypatch.setattr(
        "app.services.storage.s3_storage.boto3.client",
        lambda *args, **kwargs: client,
    )
    monkeypatch.setattr(
        "app.services.storage.s3_storage._get_s3_settings",
        lambda: Settings(_env_file=None),
    )
    return client


@pytest.mark.asyncio
async def test_s3_adapter_roundtrip_bytes(fake_client):
    provider = S3StorageProvider(bucket="test-bucket", region="us-east-1")
    data = b"%PDF-1.4 exact original bytes\x00\xff"
    key = "receipts/tenant/document.pdf"

    result = await provider.upload_file(
        data,
        key,
        "application/pdf",
        metadata={"sha256": "abc"},
    )

    assert result.success is True
    assert result.bucket == "test-bucket"
    assert result.key == key
    assert fake_client.content_types[("test-bucket", key)] == "application/pdf"
    assert await provider.download_file(key) == data
    assert await provider.file_exists(key) is True

    assert await provider.delete_file(key) is True
    assert await provider.file_exists(key) is False


@pytest.mark.asyncio
async def test_s3_adapter_raises_controlled_upload_error(fake_client):
    fake_client.fail_put = True
    provider = S3StorageProvider(bucket="test-bucket", region="us-east-1")

    with pytest.raises(UploadFailedError):
        await provider.upload_file(
            b"original bytes",
            "receipts/tenant/document.pdf",
            "application/pdf",
        )


@pytest.mark.asyncio
async def test_s3_adapter_presigned_failure_keeps_upload_success(
    fake_client,
    monkeypatch,
):
    def fail_presigned(*args, **kwargs):
        raise RuntimeError("presigned boom")

    monkeypatch.setattr(fake_client, "generate_presigned_url", fail_presigned)
    provider = S3StorageProvider(bucket="test-bucket", region="us-east-1")
    key = "receipts/tenant/document.pdf"

    result = await provider.upload_file(
        b"stored bytes",
        key,
        "application/pdf",
    )

    assert result.success is True
    assert result.presigned_url is None
    assert await provider.download_file(key) == b"stored bytes"
