# ============================================================
# PaySentinelIQ — AWS CloudWatch Logs Service
# Envio de logs estruturados para monitoramento e auditoria
# ============================================================

import os
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.shared.exceptions import ServiceError

# ── Cliente CloudWatch Logs ─────────────────────────────────

logs = boto3.client(
    "logs",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def put_log_event(
    log_group: str,
    log_stream: str,
    message: str,
    timestamp: Optional[int] = None,
) -> dict[str, Any]:
    """Envia um evento de log para o CloudWatch Logs.

    Se o log group ou log stream não existirem, tenta criá-los
    automaticamente antes de enviar o evento.

    Args:
        log_group: Nome do grupo de logs (ex: '/psi/payroll-worker').
        log_stream: Nome do stream de logs (ex: 'worker-001').
        message: Mensagem de log (pode ser JSON stringificada).
        timestamp: Timestamp em milissegundos (epoch). Se None,
                   usa o momento atual.

    Returns:
        Resposta da chamada put_log_events.

    Raises:
        ServiceError: Se o envio falhar.
    """
    import time as time_module

    if timestamp is None:
        timestamp = int(time_module.time() * 1000)

    # ── Garantir que o log group existe ──
    _ensure_log_group(log_group)

    # ── Garantir que o log stream existe ──
    _ensure_log_stream(log_group, log_stream)

    try:
        response = logs.put_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            logEvents=[
                {
                    "timestamp": timestamp,
                    "message": message,
                },
            ],
        )
        return response
    except (ClientError, BotoCoreError) as exc:
        raise ServiceError(f"Falha ao enviar log para CloudWatch: {exc}") from exc


def _ensure_log_group(log_group: str) -> None:
    """Cria o log group se não existir (idempotente)."""
    try:
        logs.create_log_group(logGroupName=log_group)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        # ResourceAlreadyExistsException é esperado e ignorado
        if code != "ResourceAlreadyExistsException":
            raise ServiceError(
                f"Falha ao criar log group '{log_group}': {exc}"
            ) from exc


def _ensure_log_stream(log_group: str, log_stream: str) -> None:
    """Cria o log stream se não existir (idempotente)."""
    try:
        logs.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code != "ResourceAlreadyExistsException":
            raise ServiceError(
                f"Falha ao criar log stream '{log_stream}': {exc}"
            ) from exc
