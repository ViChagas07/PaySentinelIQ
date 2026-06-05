# ============================================================
# PaySentinelIQ — AWS Lambda Service
# Invoca funções Lambda para processamento assíncrono
# ============================================================

import json
import os
from typing import Any, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.shared.exceptions import ServiceError

# ── Cliente Lambda ──────────────────────────────────────────

lambda_client: Any = boto3.client(
    "lambda",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

DEFAULT_FUNCTION_NAME = "paysentineliq-sqs-worker"


def invoke_lambda(
    payload: dict[str, Any],
    function_name: str = DEFAULT_FUNCTION_NAME,
    invocation_type: str = "Event",
) -> dict[str, Any]:
    """Invoca uma função Lambda de forma assíncrona.

    Args:
        payload: Dicionário com os dados a serem enviados à função.
        function_name: Nome ou ARN da função Lambda.
        invocation_type: Tipo de invocação — 'Event' (assíncrono, padrão)
                         ou 'RequestResponse' (síncrono).

    Returns:
        Resposta da invocação (contém StatusCode, Payload, etc.).

    Raises:
        ServiceError: Se a invocação falhar.
    """
    try:
        response: Any = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload).encode("utf-8"),
        )
        return cast(dict[str, Any], response)
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao invocar Lambda '{function_name}': {exc}") from exc
