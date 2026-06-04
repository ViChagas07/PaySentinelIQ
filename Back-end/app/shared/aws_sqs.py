# ============================================================
# PaySentinelIQ — AWS SQS Service
# Envia eventos assíncronos para fila de processamento
# ============================================================

import json
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.shared.exceptions import ServiceError

# ── Cliente SQS ─────────────────────────────────────────────

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")


def send_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Envia um evento para a fila SQS.

    Args:
        event_type: Tipo do evento (ex: 'payroll.submitted', 'document.uploaded').
        payload: Dados do evento a serem processados.

    Returns:
        Resposta da chamada send_message (contém MessageId, etc.).

    Raises:
        ServiceError: Se a fila não estiver configurada ou a chamada falhar.
    """
    if not QUEUE_URL:
        raise ServiceError("SQS_QUEUE_URL não configurada. Defina no .env para usar a fila.")

    try:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "type": event_type,
                    "payload": payload,
                }
            ),
        )
        return response
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao enviar mensagem para SQS: {exc}") from exc
