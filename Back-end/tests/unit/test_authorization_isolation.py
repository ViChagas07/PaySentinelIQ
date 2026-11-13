# ============================================================
# PaySentinelIQ — Authorization / tenant isolation tests
# ============================================================

import hashlib
import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from unittest.mock import patch

import fitz
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.auth.services import AuthService
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_result import PipelineResult
from app.main import create_app
from app.shared.database import get_db
from app.shared.orm_models import (
    AnalysisRecordModel,
    DocumentModel,
    FraudAlertModel,
    TenantModel,
    UserModel,
    VerificationReportModel,
)
from app.shared.settings import Settings
from tests.unit._storage_fakes import InMemoryStorageProvider


class _NoOpInstrumentator:
    def instrument(self, app):
        return self

    def expose(self, app, **kwargs):
        return self


async def _allow_rate_limit(self, **kwargs):
    return {"limit": 1000, "remaining": 1000, "reset": 0}


@pytest_asyncio.fixture(scope="module")
async def authz_app(test_engine):
    with patch(
        "app.main.Instrumentator",
        new=lambda *args, **kwargs: _NoOpInstrumentator(),
    ):
        app = create_app()

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with patch("app.shared.rate_limiter.RateLimiter.check", new=_allow_rate_limit):
        yield app
    app.dependency_overrides.clear()


async def _seed_tenant(db_session, label: str = "tenant") -> uuid.UUID:
    tenant_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name=f"{label}-{tenant_id}",
            slug=f"{label}-{tenant_id}",
            plan="starter",
            is_active=True,
        )
    )
    await db_session.commit()
    return tenant_id


async def _seed_user(
    db_session,
    tenant_id: uuid.UUID,
    *,
    label: str = "user",
    role: str = "viewer",
    is_active: bool = True,
) -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"{label}-{user_id}@example.com",
            full_name=f"{label.title()} User",
            hashed_password=AuthService.hash_password("correct-password"),
            role=role,
            is_active=is_active,
        )
    )
    await db_session.commit()
    return user_id


async def _seed_document(
    db_session,
    tenant_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    *,
    file_name: str = "document.pdf",
) -> uuid.UUID:
    document_id = uuid.uuid4()
    db_session.add(
        DocumentModel(
            id=document_id,
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            document_type="boleto",
            file_name=file_name,
            file_size_bytes=123,
            s3_key=f"receipts/{tenant_id}/{document_id}.pdf",
            s3_bucket="test-bucket",
            file_hash="b" * 64,
            ocr_status="pending",
        )
    )
    await db_session.commit()
    return document_id


async def _seed_alert(
    db_session,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    *,
    status: str = "new",
) -> uuid.UUID:
    alert_id = uuid.uuid4()
    db_session.add(
        FraudAlertModel(
            id=alert_id,
            tenant_id=tenant_id,
            document_id=document_id,
            risk_level="high",
            risk_score=85.0,
            ai_confidence=0.91,
            anomaly_category="document_fraud",
            description="Tenant isolation test alert",
            ai_explanation="Test explanation",
            flagged_fields=[],
            status=status,
        )
    )
    await db_session.commit()
    return alert_id


async def _seed_analysis(
    db_session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    file_name: str,
    fraudulent: bool = True,
    risk_level: str = "HIGH",
) -> uuid.UUID:
    record_id = uuid.uuid4()
    db_session.add(
        AnalysisRecordModel(
            id=record_id,
            user_id=user_id,
            tenant_id=tenant_id,
            document_type="BOLETO",
            file_name=file_name,
            file_size=123,
            risk_level=risk_level,
            risk_score=85.0 if risk_level == "HIGH" else 20.0,
            confidence_score=0.91,
            is_fraudulent=fraudulent,
            fraud_indicators=["test"] if fraudulent else [],
            analysis_result={"test": True},
            status="flagged" if fraudulent else "completed",
            analyzed_at=datetime.now(UTC),
        )
    )
    await db_session.commit()
    return record_id


async def _seed_report(
    db_session,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
) -> uuid.UUID:
    report_id = uuid.uuid4()
    db_session.add(
        VerificationReportModel(
            id=report_id,
            tenant_id=tenant_id,
            document_id=document_id,
            status="verified",
            risk_score=85.0,
            extracted_fields={},
            metadata_analysis={},
            fraud_indicators=[],
            ocr_confidence=0.9,
            ai_explanation="Test verification report",
        )
    )
    await db_session.commit()
    return report_id


def _pdf_bytes() -> bytes:
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "Authorization isolation test")
        return document.tobytes()
    finally:
        document.close()


def _login_payload(email: str) -> dict[str, object]:
    return {
        "email": email,
        "password": "correct-password",
        "consent_given": True,
        "terms_version": "1.0.0",
        "privacy_version": "1.0.0",
    }


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/auth/login", json=_login_payload(email))
    assert response.status_code == 200
    return response.json()["access_token"]


# ── Alerts: tenant-shared, cross-tenant hidden ──────────────


@pytest.mark.asyncio
async def test_alert_reads_are_tenant_scoped_and_shared_in_tenant(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "alert-a")
    tenant_b = await _seed_tenant(db_session, "alert-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="alert-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="alert-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="alert-b1", role="fraud_analyst"
    )

    doc_a = await _seed_document(db_session, tenant_a, a1)
    alert_a = await _seed_alert(db_session, tenant_a, doc_a)
    doc_b = await _seed_document(db_session, tenant_b, b1)
    alert_b = await _seed_alert(db_session, tenant_b, doc_b)

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a1 = await _login(
            client,
            f"alert-a1-{a1}@example.com",
        )
        token_a2 = await _login(
            client,
            f"alert-a2-{a2}@example.com",
        )
        token_b1 = await _login(
            client,
            f"alert-b1-{b1}@example.com",
        )

        # B1 cannot read A1's alert by ID.
        response = await client.get(
            f"/api/fraud-alerts/{alert_a}",
            headers=_bearer(token_b1),
        )
        assert response.status_code == 404

        # A2 can read A1's alert: alerts are tenant-shared for reads.
        response = await client.get(
            f"/api/fraud-alerts/{alert_a}",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        assert response.json()["document_id"] == str(doc_a)

        # B1's list contains only tenant B alerts.
        response = await client.get(
            "/api/fraud-alerts?page=1&page_size=10",
            headers=_bearer(token_b1),
        )
        assert response.status_code == 200
        body = response.json()
        ids = {item["id"] for item in body["data"]}
        assert str(alert_b) in ids
        assert str(alert_a) not in ids
        assert body["total"] == 1

        # Tenant A stats do not include tenant B alerts.
        response = await client.get(
            "/api/fraud-alerts/stats",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # A1 remains able to read its own tenant's shared alert.
        response = await client.get(
            f"/api/fraud-alerts/{alert_a}",
            headers=_bearer(token_a1),
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_alert_write_requires_tenant_scope_and_role(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "write-a")
    tenant_b = await _seed_tenant(db_session, "write-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="write-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="write-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="write-b1", role="fraud_analyst"
    )

    doc_a = await _seed_document(db_session, tenant_a, a1)
    alert_a = await _seed_alert(db_session, tenant_a, doc_a)

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a1 = await _login(client, f"write-a1-{a1}@example.com")
        token_a2 = await _login(client, f"write-a2-{a2}@example.com")
        token_b1 = await _login(client, f"write-b1-{b1}@example.com")

        body = {
            "resolution": "confirmed_fraud",
            "notes": "Tenant isolation test",
        }

        # Other tenant: cannot mutate, and the status stays unchanged.
        response = await client.patch(
            f"/api/fraud-alerts/{alert_a}/resolve",
            json=body,
            headers=_bearer(token_b1),
        )
        assert response.status_code == 404

        # Same tenant, insufficient role: 403, status unchanged.
        response = await client.patch(
            f"/api/fraud-alerts/{alert_a}/resolve",
            json=body,
            headers=_bearer(token_a2),
        )
        assert response.status_code == 403

        # Same tenant, authorized role: mutation allowed.
        response = await client.patch(
            f"/api/fraud-alerts/{alert_a}/resolve",
            json=body,
            headers=_bearer(token_a1),
        )
        assert response.status_code == 200

        db_session.expire_all()
        alert = (
            await db_session.execute(
                select(FraudAlertModel).where(FraudAlertModel.id == alert_a)
            )
        ).scalar_one()
        assert alert.status == "confirmed_fraud"

        # Invalid IDs are treated as absent, not as 500.
        response = await client.get(
            "/api/fraud-alerts/not-a-uuid",
            headers=_bearer(token_a1),
        )
        assert response.status_code == 404

        response = await client.patch(
            "/api/fraud-alerts/not-a-uuid/resolve",
            json=body,
            headers=_bearer(token_a1),
        )
        assert response.status_code == 404


# ── Analysis history/stats: user-private within tenant ─────


@pytest.mark.asyncio
async def test_analysis_history_and_stats_are_user_private(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "analysis-a")
    tenant_b = await _seed_tenant(db_session, "analysis-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="analysis-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="analysis-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="analysis-b1", role="fraud_analyst"
    )

    record_a1 = await _seed_analysis(
        db_session, tenant_a, a1, file_name="a1.pdf"
    )
    record_a2 = await _seed_analysis(
        db_session, tenant_a, a2, file_name="a2.pdf", fraudulent=False,
        risk_level="LOW",
    )
    record_b1 = await _seed_analysis(
        db_session, tenant_b, b1, file_name="b1.pdf"
    )

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a2 = await _login(client, f"analysis-a2-{a2}@example.com")
        token_b1 = await _login(client, f"analysis-b1-{b1}@example.com")

        response = await client.get(
            "/api/analysis/history?page=1&per_page=1",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()}
        assert str(record_a2) in ids
        assert str(record_a1) not in ids
        assert str(record_b1) not in ids

        # Filters and pagination cannot bypass the user/tenant scope.
        response = await client.get(
            "/api/analysis/history?page=1&per_page=1"
            "&document_type=BOLETO&risk_level=HIGH",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        assert response.json() == []

        response = await client.get(
            "/api/analysis/history",
            headers=_bearer(token_b1),
        )
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()}
        assert str(record_b1) in ids
        assert str(record_a1) not in ids
        assert str(record_a2) not in ids


@pytest.mark.asyncio
async def test_analysis_stats_excludes_other_users_and_tenants(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "stats-a")
    tenant_b = await _seed_tenant(db_session, "stats-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="stats-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="stats-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="stats-b1", role="fraud_analyst"
    )

    await _seed_analysis(db_session, tenant_a, a1, file_name="stats-a1.pdf")
    await _seed_analysis(db_session, tenant_b, b1, file_name="stats-b1.pdf")

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a2 = await _login(client, f"stats-a2-{a2}@example.com")

        response = await client.get(
            "/api/analysis/stats",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_documents"] == 0
        assert stats["fraudulent_count"] == 0
        assert stats["recent_analyses"] == []


@pytest.mark.asyncio
async def test_dashboard_aggregates_are_tenant_scoped(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "dashboard-a")
    tenant_b = await _seed_tenant(db_session, "dashboard-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="dashboard-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="dashboard-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="dashboard-b1", role="fraud_analyst"
    )

    await _seed_analysis(db_session, tenant_a, a1, file_name="a1.pdf")
    await _seed_analysis(
        db_session,
        tenant_a,
        a2,
        file_name="a2.pdf",
        fraudulent=False,
        risk_level="LOW",
    )
    await _seed_analysis(db_session, tenant_b, b1, file_name="b1.pdf")

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a2 = await _login(client, f"dashboard-a2-{a2}@example.com")

        response = await client.get(
            "/api/dashboard/kpis",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        kpis = response.json()

        # Tenant A has two analyses; tenant B's analysis is excluded.
        assert kpis["payrolls_processed"] == 2
        assert kpis["fraud_alerts"] == 1
        assert kpis["high_risk_docs"] == 1


# ── /analysis/save: identity comes from the principal ──────


@pytest.mark.asyncio
async def test_analysis_save_ignores_spoofed_identity(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "save-a")
    tenant_b = await _seed_tenant(db_session, "save-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="save-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="save-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="save-b1", role="fraud_analyst"
    )

    spoofed = {
        "user_id": str(a1),
        "tenant_id": str(tenant_b),
        "document_id": str(uuid.uuid4()),
        "alert_id": str(uuid.uuid4()),
    }
    payload = {
        "document_type": "BOLETO",
        "file_name": "spoof.pdf",
        "file_size": 123,
        "risk_level": "HIGH",
        "risk_score": 85.0,
        "confidence_score": 0.91,
        "fraud_probability": 0.9,
        "is_fraudulent": True,
        "fraud_indicators": ["test"],
        "analysis_result": {"source": "authz-test"},
        "amount": 100.0,
        "ai_summary": "test",
        "processing_duration": 1.0,
        "status": "flagged",
        **spoofed,
    }

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a2 = await _login(client, f"save-a2-{a2}@example.com")

        response = await client.post(
            "/api/analysis/save",
            json=payload,
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200

        db_session.expire_all()
        records = (
            await db_session.execute(
                select(AnalysisRecordModel).where(
                    AnalysisRecordModel.user_id == a2,
                    AnalysisRecordModel.tenant_id == tenant_a,
                    AnalysisRecordModel.file_name == "spoof.pdf",
                )
            )
        ).scalars().all()
        assert len(records) == 1
        record = records[0]

        assert record.user_id == a2
        assert record.tenant_id == tenant_a
        assert record.user_id != a1
        assert record.tenant_id != tenant_b
        assert record.tenant_id != b1


# ── Account export: reports follow document ownership ──────


@pytest.mark.asyncio
async def test_account_export_does_not_leak_other_users_reports(
    authz_app,
    db_session,
):
    tenant_a = await _seed_tenant(db_session, "export-a")
    tenant_b = await _seed_tenant(db_session, "export-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="export-a1", role="fraud_analyst"
    )
    a2 = await _seed_user(
        db_session, tenant_a, label="export-a2", role="viewer"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="export-b1", role="fraud_analyst"
    )

    doc_a1 = await _seed_document(db_session, tenant_a, a1, file_name="a1.pdf")
    doc_a2 = await _seed_document(db_session, tenant_a, a2, file_name="a2.pdf")
    doc_b1 = await _seed_document(db_session, tenant_b, b1, file_name="b1.pdf")

    report_a1 = await _seed_report(db_session, tenant_a, doc_a1)
    report_a2 = await _seed_report(db_session, tenant_a, doc_a2)
    report_b1 = await _seed_report(db_session, tenant_b, doc_b1)

    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a2 = await _login(client, f"export-a2-{a2}@example.com")

        response = await client.get(
            "/api/account/export",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        export = response.json()

        document_ids = {doc["id"] for doc in export["documents"]}
        assert str(doc_a2) in document_ids
        assert str(doc_a1) not in document_ids
        assert str(doc_b1) not in document_ids

        report_ids = {
            report["id"] for report in export["verification_reports"]
        }
        assert str(report_a2) in report_ids
        assert str(report_a1) not in report_ids
        assert str(report_b1) not in report_ids

        # The ZIP download follows the same document ownership scope.
        response = await client.get(
            "/api/account/export/download",
            headers=_bearer(token_a2),
        )
        assert response.status_code == 200
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            profile = json.loads(archive.read("profile_data.json"))

        download_doc_ids = {doc["id"] for doc in profile["documents"]}
        assert str(doc_a2) in download_doc_ids
        assert str(doc_a1) not in download_doc_ids
        assert str(doc_b1) not in download_doc_ids


# ── Canonical analysis: persistence uses principal tenant/user ─


@pytest.mark.asyncio
async def test_canonical_analysis_persists_to_principal_scope(
    authz_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_a = await _seed_tenant(db_session, "canonical-a")
    tenant_b = await _seed_tenant(db_session, "canonical-b")
    a1 = await _seed_user(
        db_session, tenant_a, label="canonical-a1", role="fraud_analyst"
    )
    b1 = await _seed_user(
        db_session, tenant_b, label="canonical-b1", role="fraud_analyst"
    )

    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: Settings(
            _env_file=None,
            USE_CANONICAL_PIPELINE=True,
            ENABLE_OCR=False,
            ENABLE_CANONICAL_EXTRACTION=False,
            ENABLE_SHADOW_PIPELINE=False,
        ),
    )
    monkeypatch.setattr(
        "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
        lambda self, ctx: PipelineResult(
            risk_score=85.0,
            risk_level="HIGH",
            confidence=91.0,
            evidence=[
                Evidence(
                    code="AUTHZ_CANONICAL_TEST",
                    description="Test evidence",
                    severity=Severity.HIGH,
                    source=EvidenceSource.DETERMINISTIC,
                    confidence=0.99,
                )
            ],
            reasoning_summary="Test reasoning",
        ),
    )

    storage = InMemoryStorageProvider()
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        lambda: storage,
    )

    async def no_event(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.api.documents.router._publish_analysis_event",
        no_event,
    )
    monkeypatch.setattr(
        "app.api.documents.router._send_analysis_notification",
        no_event,
    )

    pdf_bytes = _pdf_bytes()
    async with AsyncClient(
        transport=ASGITransport(app=authz_app),
        base_url="http://test",
    ) as client:
        token_a1 = await _login(client, f"canonical-a1-{a1}@example.com")

        response = await client.post(
            "/api/documents/analyze",
            data={
                "document_type": "boleto",
                "tenant_id": str(tenant_b),
                "user_id": str(b1),
            },
            files={
                "file": (
                    "boleto.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
            headers=_bearer(token_a1),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "saved"
    assert body["confidence"] == 91.0

    document_id = uuid.UUID(body["document_id"])
    db_session.expire_all()

    document = (
        await db_session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
    ).scalar_one()
    alert = (
        await db_session.execute(
            select(FraudAlertModel).where(
                FraudAlertModel.document_id == document_id
            )
        )
    ).scalar_one()

    assert document.tenant_id == tenant_a
    assert document.uploaded_by == a1
    assert document.s3_key
    assert document.s3_bucket == storage.bucket
    assert document.file_hash == hashlib.sha256(pdf_bytes).hexdigest()
    assert await storage.download_file(document.s3_key) == pdf_bytes

    assert alert.tenant_id == tenant_a
    assert alert.ai_confidence == pytest.approx(0.91)
    assert alert.risk_score == pytest.approx(85.0)
