# ============================================================
# PaySentinelIQ — AWS S3 Service
# Upload e gerenciamento de documentos no bucket S3
# ============================================================

import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.shared.exceptions import ServiceError

# ── Cliente S3 ──────────────────────────────────────────────

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

BUCKET_NAME = os.getenv("S3_BUCKET")


def upload_file(file_bytes: bytes, filename: str, content_type: str | None = None) -> str:
    """Faz upload de um arquivo para o bucket S3.

    Args:
        file_bytes: Conteúdo do arquivo em bytes.
        filename: Caminho/chave do objeto no bucket (ex: 'documents/relatorio.pdf').
        content_type: Tipo MIME do arquivo (opcional).

    Returns:
        URI do objeto no formato 's3://<bucket>/<key>'.

    Raises:
        ServiceError: Se o bucket não estiver configurado ou o upload falhar.
    """
    if not BUCKET_NAME:
        raise ServiceError("S3_BUCKET não configurado. Defina no .env para usar o S3.")

    try:
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        else:
            extra_args["ContentType"] = "application/octet-stream"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=file_bytes,
            **extra_args,
        )

        return f"s3://{BUCKET_NAME}/{filename}"
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao fazer upload para S3: {exc}") from exc


def download_file(filename: str) -> bytes:
    """Faz download de um arquivo do bucket S3.

    Args:
        filename: Chave do objeto no bucket.

    Returns:
        Conteúdo do arquivo em bytes.

    Raises:
        ServiceError: Se o arquivo não existir ou a chamada falhar.
    """
    if not BUCKET_NAME:
        raise ServiceError("S3_BUCKET não configurado.")

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        return response["Body"].read()
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao baixar arquivo do S3: {exc}") from exc


def delete_file(filename: str) -> None:
    """Remove um arquivo do bucket S3.

    Args:
        filename: Chave do objeto a ser removido.

    Raises:
        ServiceError: Se a remoção falhar.
    """
    if not BUCKET_NAME:
        raise ServiceError("S3_BUCKET não configurado.")

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao remover arquivo do S3: {exc}") from exc
