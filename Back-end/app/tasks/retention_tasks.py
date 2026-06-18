# ============================================================
# PaySentinelIQ — Data Retention & Cleanup Tasks (LGPD)
# Periodic tasks for data lifecycle management:
# - OCR temp file cleanup (24h TTL)
# - Document retention expiry (7 years default)
# - Account deletion finalization (grace period)
# - Audit log archival
# ============================================================

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select, update

from app.tasks import celery_app
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# OCR TEMP FILE CLEANUP (runs hourly)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    name="cleanup_ocr_temp_files",
)
def cleanup_ocr_temp_files(self: Any) -> dict[str, Any]:
    """Remove temporary OCR files older than OCR_TEMP_FILE_RETENTION_HOURS.

    This task should be scheduled hourly via Celery Beat.
    Ensures intermediate OCR processing artifacts are not retained indefinitely.
    """
    logger.info("Starting OCR temp file cleanup...")

    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=settings.OCR_TEMP_FILE_RETENTION_HOURS
    )

    try:
        from app.services.storage import S3StorageProvider

        storage = S3StorageProvider()

        # List all objects in the temp/ prefix
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=(
                settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
                if settings.AWS_SECRET_ACCESS_KEY
                else None
            ),
            region_name=settings.AWS_REGION,
        )

        deleted_count = 0
        bucket = settings.S3_BUCKET

        # List and delete old temp files
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix="temp/"):
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                if obj["LastModified"].replace(tzinfo=timezone.utc) < cutoff:
                    s3.delete_object(Bucket=bucket, Key=obj["Key"])
                    deleted_count += 1
                    logger.debug("Deleted temp file: %s", obj["Key"])

        logger.info("OCR temp cleanup complete: %d files deleted", deleted_count)
        return {"status": "completed", "deleted_count": deleted_count}

    except Exception as exc:
        logger.error("OCR temp cleanup failed: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# ACCOUNT DELETION FINALIZATION (runs daily)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=1,
    default_retry_delay=3600,
    name="finalize_account_deletions",
)
def finalize_account_deletions(self: Any) -> dict[str, Any]:
    """Permanently delete accounts that have passed the grace period.

    This task should be scheduled daily via Celery Beat.
    Implements the irreversible final step of LGPD-compliant account deletion.
    """
    logger.info("Starting account deletion finalization...")

    grace_days = settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=grace_days)

    try:
        import asyncio
        from app.shared.database import AsyncSessionLocal
        from app.shared.orm_models import (
            UserModel, DocumentModel, NotificationModel,
            ConsentRecordModel, UserSettingsModel, AuditLogModel,
        )

        async def _finalize():
            finalized = 0
            docs_removed = 0

            async with AsyncSessionLocal() as session:
                # Find inactive users past grace period
                stmt = select(UserModel).where(
                    UserModel.is_active == False,
                    UserModel.updated_at < cutoff,
                )
                result = await session.execute(stmt)
                users = result.scalars().all()

                for user in users:
                    logger.info(
                        "Finalizing deletion for user: %s (email: %s)",
                        user.id, user.email,
                    )

                    # Remove user's documents from S3
                    docs_stmt = select(DocumentModel).where(
                        DocumentModel.uploaded_by == user.id,
                    )
                    docs_result = await session.execute(docs_stmt)
                    documents = docs_result.scalars().all()

                    try:
                        from app.services.storage import S3StorageProvider
                        storage = S3StorageProvider()
                        for doc in documents:
                            await storage.delete_file(doc.s3_key)
                            docs_removed += 1
                            await session.delete(doc)
                    except Exception as s3_err:
                        logger.warning(
                            "S3 deletion error for user %s: %s", user.id, s3_err
                        )

                    # Delete consent records
                    await session.execute(
                        delete(ConsentRecordModel).where(
                            ConsentRecordModel.user_id == user.id
                        )
                    )

                    # Delete notifications
                    await session.execute(
                        delete(NotificationModel).where(
                            NotificationModel.user_id == user.id
                        )
                    )

                    # Delete settings
                    await session.execute(
                        delete(UserSettingsModel).where(
                            UserSettingsModel.user_id == user.id
                        )
                    )

                    # Record final audit entry
                    audit = AuditLogModel(
                        tenant_id=user.tenant_id,
                        user_id=user.id,
                        user_name=user.full_name,
                        action="account_permanently_deleted",
                        entity_type="user",
                        entity_id=str(user.id),
                        details={
                            "reason": "grace_period_expired",
                            "grace_period_days": grace_days,
                        },
                        ip_address=None,
                        user_agent=None,
                    )
                    session.add(audit)

                    # Hard delete the user
                    await session.delete(user)
                    finalized += 1

                await session.commit()

            return {"finalized_accounts": finalized, "documents_removed": docs_removed}

        result = asyncio.run(_finalize())
        logger.info(
            "Account deletion finalization complete: %d accounts, %d documents",
            result["finalized_accounts"], result["documents_removed"],
        )
        return {"status": "completed", **result}

    except Exception as exc:
        logger.error("Account deletion finalization failed: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# DOCUMENT RETENTION EXPIRY (runs weekly)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=1,
    default_retry_delay=3600,
    name="cleanup_expired_documents",
)
def cleanup_expired_documents(self: Any) -> dict[str, Any]:
    """Remove documents and S3 objects past their retention period.

    This task should be scheduled weekly via Celery Beat.
    Respects Brazilian labor law minimum retention (7 years default).
    """
    logger.info("Starting expired document cleanup...")

    retention_days = settings.DOCUMENT_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    try:
        import asyncio
        from app.shared.database import AsyncSessionLocal
        from app.shared.orm_models import DocumentModel, AuditLogModel

        async def _cleanup():
            removed = 0
            async with AsyncSessionLocal() as session:
                stmt = select(DocumentModel).where(
                    DocumentModel.created_at < cutoff,
                    DocumentModel.deleted_at == None,  # not already soft-deleted
                )
                result = await session.execute(stmt)
                documents = result.scalars().all()

                from app.services.storage import S3StorageProvider
                storage = S3StorageProvider()

                for doc in documents:
                    try:
                        # Remove from S3
                        await storage.delete_file(doc.s3_key)
                        # Soft-delete the record
                        doc.s3_key = f"EXPIRED/{doc.s3_key}"
                        session.add(doc)
                        removed += 1

                        # Audit log
                        audit = AuditLogModel(
                            tenant_id=doc.tenant_id,
                            user_id=None,
                            user_name="system",
                            action="document_retention_expired",
                            entity_type="document",
                            entity_id=str(doc.id),
                            details={
                                "file_name": doc.file_name,
                                "retention_days": retention_days,
                                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                            },
                            ip_address=None,
                            user_agent=None,
                        )
                        session.add(audit)

                    except Exception as doc_err:
                        logger.warning(
                            "Failed to clean document %s: %s", doc.id, doc_err
                        )

                await session.commit()
            return removed

        removed = asyncio.run(_cleanup())
        logger.info("Expired document cleanup complete: %d documents removed", removed)
        return {"status": "completed", "documents_removed": removed}

    except Exception as exc:
        logger.error("Expired document cleanup failed: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# AUDIT LOG ARCHIVAL (runs monthly)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=1,
    default_retry_delay=3600,
    name="archive_old_audit_logs",
)
def archive_old_audit_logs(self: Any) -> dict[str, Any]:
    """Archive audit logs older than AUDIT_RETENTION_DAYS to cold storage.

    This task should be scheduled monthly via Celery Beat.
    In production, audit logs would be exported to S3 Glacier/Deep Archive
    for long-term retention while freeing database space.
    """
    logger.info("Starting audit log archival...")

    retention_days = settings.AUDIT_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    try:
        import asyncio
        import json
        from app.shared.database import AsyncSessionLocal
        from app.shared.orm_models import AuditLogModel

        async def _archive():
            async with AsyncSessionLocal() as session:
                stmt = select(AuditLogModel).where(
                    AuditLogModel.created_at < cutoff,
                )
                result = await session.execute(stmt)
                old_logs = result.scalars().all()

                if not old_logs:
                    return 0

                # In production: export to S3 Glacier, then delete from DB
                # For now, we simply count and log
                archive_data = {
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "count": len(old_logs),
                    "cutoff_date": cutoff.isoformat(),
                    "logs": [
                        {
                            "id": str(log.id),
                            "action": log.action,
                            "entity_type": log.entity_type,
                            "entity_id": log.entity_id,
                            "user_name": log.user_name,
                            "created_at": log.created_at.isoformat() if log.created_at else None,
                        }
                        for log in old_logs
                    ],
                }

                logger.info(
                    "Audit log archival: %d logs ready for archival (cutoff: %s)",
                    len(old_logs), cutoff.isoformat(),
                )

                return len(old_logs)

        count = asyncio.run(_archive())
        return {"status": "completed", "logs_candidates_for_archival": count}

    except Exception as exc:
        logger.error("Audit log archival failed: %s", exc)
        raise self.retry(exc=exc) from exc
