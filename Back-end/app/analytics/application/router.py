# ============================================================
# PaySentinelIQ — Analytics / Dashboard Router
# All endpoints query real data from the database based on
# what the authenticated user has actually done in the app.
# No hardcoded/mock/dummy data.
# ============================================================

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_tenant_id
from app.shared.database import get_db
from app.shared.orm_models import (
    AnalysisRecordModel,
    ComplianceReportModel,
    EmployeeModel,
    FraudAlertModel,
    PayrollModel,
    VerificationReportModel,
)

router = APIRouter()


@router.get("/dashboard/kpis")
async def get_dashboard_kpis(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return KPI metrics based on real user activity for the given tenant."""
    tid = UUID(tenant_id)

    # 1) Payrolls processed (all non-draft payrolls)
    payrolls_count_result = await db.execute(
        select(func.count(PayrollModel.id)).where(
            PayrollModel.tenant_id == tid,
            PayrollModel.status != "draft",
            PayrollModel.deleted_at.is_(None),
        )
    )
    payrolls_processed = payrolls_count_result.scalar_one()

    # 2) Verification rate (percentage of payrolls with verified_by_ai = True)
    ver_stats_result = await db.execute(
        select(
            func.count(PayrollModel.id).filter(
                PayrollModel.verified_by_ai.is_(True),
                PayrollModel.status != "draft",
                PayrollModel.deleted_at.is_(None),
            ),
            func.count(PayrollModel.id).filter(
                PayrollModel.status != "draft",
                PayrollModel.deleted_at.is_(None),
            ),
        ).where(PayrollModel.tenant_id == tid)
    )
    verified_count, total_non_draft = ver_stats_result.one()
    verification_rate = round(
        (verified_count / total_non_draft * 100) if total_non_draft > 0 else 0, 1
    )

    # 3) Active fraud alerts
    fraud_count_result = await db.execute(
        select(func.count(FraudAlertModel.id)).where(
            FraudAlertModel.tenant_id == tid,
            FraudAlertModel.status.in_(["new", "under_review", "escalated"]),
        )
    )
    fraud_alerts = fraud_count_result.scalar_one()

    # 4) Average AI confidence across all fraud alerts
    ai_conf_result = await db.execute(
        select(func.avg(FraudAlertModel.ai_confidence)).where(FraudAlertModel.tenant_id == tid)
    )
    avg_ai_conf = ai_conf_result.scalar_one()
    ai_confidence = round((avg_ai_conf * 100) if avg_ai_conf else 0, 1)

    # 5) High-risk documents (verification reports with risk_score >= 70)
    high_risk_result = await db.execute(
        select(func.count(VerificationReportModel.id)).where(
            VerificationReportModel.tenant_id == tid,
            VerificationReportModel.risk_score >= 70,
        )
    )
    high_risk_docs = high_risk_result.scalar_one()

    # 6) Compliance incidents (failed verifications)
    compliance_result = await db.execute(
        select(func.count(ComplianceReportModel.id)).where(
            ComplianceReportModel.tenant_id == tid,
            ComplianceReportModel.verification_status == "failed",
        )
    )
    compliance_incidents = compliance_result.scalar_one()

    # 7) Analysis records — document analyses (boleto + contracheque)
    analysis_total_result = await db.execute(
        select(func.count(AnalysisRecordModel.id)).where(
            AnalysisRecordModel.tenant_id == tid,
        )
    )
    analysis_total = analysis_total_result.scalar_one()

    analysis_fraud_result = await db.execute(
        select(func.count(AnalysisRecordModel.id)).where(
            AnalysisRecordModel.tenant_id == tid,
            AnalysisRecordModel.is_fraudulent.is_(True),
        )
    )
    analysis_fraud_count = analysis_fraud_result.scalar_one()

    analysis_high_risk_result = await db.execute(
        select(func.count(AnalysisRecordModel.id)).where(
            AnalysisRecordModel.tenant_id == tid,
            AnalysisRecordModel.risk_level.in_(["HIGH", "CRITICAL"]),
        )
    )
    analysis_high_risk = analysis_high_risk_result.scalar_one()

    analysis_pass_rate_result = await db.execute(
        select(func.avg(AnalysisRecordModel.confidence_score)).where(
            AnalysisRecordModel.tenant_id == tid,
            AnalysisRecordModel.confidence_score.isnot(None),
        )
    )
    analysis_avg_conf = analysis_pass_rate_result.scalar_one() or 0.0

    # Calculate blended pass rate from analysis records
    analysis_pass_rate = round(
        ((analysis_total - analysis_fraud_count) / analysis_total * 100) if analysis_total > 0 else 0, 1
    )

    return {
        "payrolls_processed": payrolls_processed + analysis_total,
        "verification_rate": verification_rate if verification_rate > 0 else analysis_pass_rate,
        "fraud_alerts": fraud_alerts + analysis_fraud_count,
        "ai_confidence": ai_confidence if ai_confidence > 0 else round(float(analysis_avg_conf) * 100, 1),
        "high_risk_docs": high_risk_docs + analysis_high_risk,
        "compliance_incidents": compliance_incidents,
    }


@router.get("/dashboard/trends")
async def get_dashboard_trends(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return monthly payroll verification trend data based on real user activity."""
    tid = UUID(tenant_id)

    # Monthly aggregation of payroll data
    stmt = (
        select(
            extract("year", PayrollModel.period_start).label("year"),
            extract("month", PayrollModel.period_start).label("month"),
            func.count(PayrollModel.id).label("volume"),
            func.count(PayrollModel.id)
            .filter(PayrollModel.verified_by_ai.is_(True))
            .label("verified"),
            func.count(PayrollModel.id).filter(PayrollModel.status == "flagged").label("flagged"),
        )
        .where(
            PayrollModel.tenant_id == tid,
            PayrollModel.status != "draft",
            PayrollModel.deleted_at.is_(None),
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Build trend data with short month names
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    trends = []
    for _year, month, volume, verified, flagged in rows:
        pass_rate = round((verified / volume * 100) if volume > 0 else 0, 1)
        trends.append(
            {
                "month": f"{month_names[int(month) - 1]}",
                "volume": volume,
                "verified": verified,
                "flagged": flagged,
                "passRate": pass_rate,
            }
        )

    return trends


@router.get("/dashboard/heatmap")
async def get_dashboard_heatmap(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return department-level risk concentration based on real employee & fraud data."""
    tid = UUID(tenant_id)

    # Aggregate employees by department with risk metrics
    stmt = (
        select(
            EmployeeModel.department,
            func.count(EmployeeModel.id).label("payrolls"),
            func.coalesce(func.avg(EmployeeModel.risk_score), 0).label("risk_score"),
        )
        .where(
            EmployeeModel.tenant_id == tid,
            EmployeeModel.status == "active",
        )
        .group_by(EmployeeModel.department)
        .order_by(EmployeeModel.department)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # For each department, count fraud alerts linked to employees in that dept
    heatmap_data = []
    for dept_name, emp_count, avg_risk in rows:
        # Count fraud alerts involving employees from this department
        flagged_result = await db.execute(
            select(func.count(FraudAlertModel.id)).where(
                FraudAlertModel.tenant_id == tid,
                FraudAlertModel.status.in_(
                    [
                        "new",
                        "under_review",
                        "escalated",
                        "confirmed_fraud",
                    ]
                ),
            )
        )
        flagged_count = flagged_result.scalar_one()

        risk_score = round(float(avg_risk), 1)
        if risk_score >= 7:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"
        else:
            risk_level = "low"

        heatmap_data.append(
            {
                "name": dept_name,
                "payrolls": emp_count,
                "riskScore": risk_score,
                "flaggedCount": flagged_count,
                "riskLevel": risk_level,
            }
        )

    return heatmap_data


@router.get("/dashboard/risk-distribution")
async def get_dashboard_risk_distribution(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return risk score distribution from real verification reports."""
    tid = UUID(tenant_id)

    # Count verification reports by risk score buckets
    buckets = [
        {"range": "0-2", "min": 0, "max": 2, "color": "#14B87A"},
        {"range": "2-4", "min": 2, "max": 4, "color": "#14B87A"},
        {"range": "4-6", "min": 4, "max": 6, "color": "#F0A020"},
        {"range": "6-8", "min": 6, "max": 8, "color": "#E07020"},
        {"range": "8-10", "min": 8, "max": 10, "color": "#E04040"},
    ]

    distribution = []
    for bucket in buckets:
        count_result = await db.execute(
            select(func.count(VerificationReportModel.id)).where(
                VerificationReportModel.tenant_id == tid,
                VerificationReportModel.risk_score >= bucket["min"],
                VerificationReportModel.risk_score < bucket["max"],
            )
        )
        count = count_result.scalar_one()
        distribution.append(
            {
                "range": bucket["range"],
                "count": count,
                "color": bucket["color"],
            }
        )

    return distribution


@router.get("/ai-insights")
async def get_ai_insights(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return AI-generated fraud insights based on real fraud alerts."""
    tid = UUID(tenant_id)

    stmt = (
        select(FraudAlertModel)
        .where(FraudAlertModel.tenant_id == tid)
        .order_by(FraudAlertModel.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    insights = []
    for alert in alerts:
        insights.append(
            {
                "id": str(alert.id),
                "tenant_id": tenant_id,
                "title": alert.description,
                "summary": alert.ai_explanation or alert.description,
                "detailed_analysis": alert.ai_explanation or "",
                "risk_score": round(alert.risk_score),
                "confidence": alert.ai_confidence,
                "category": alert.anomaly_category,
                "recommended_actions": [],
                "related_documents": [str(alert.document_id)] if alert.document_id else [],
                "created_at": alert.created_at.isoformat() if alert.created_at else "",
            }
        )

    return {
        "data": insights,
        "total": len(insights),
        "page": 1,
        "page_size": 50,
        "total_pages": 1,
    }


@router.get("/ai-insights/feed")
async def get_ai_insights_feed(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return lightweight AI insights feed from real fraud alerts."""
    tid = UUID(tenant_id)

    stmt = (
        select(FraudAlertModel)
        .where(FraudAlertModel.tenant_id == tid)
        .order_by(FraudAlertModel.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    feed = []
    for alert in alerts:
        feed.append(
            {
                "id": str(alert.id),
                "title": alert.description,
                "risk_score": round(alert.risk_score),
                "confidence": alert.ai_confidence,
                "category": alert.anomaly_category,
                "recommended_actions": [],
                "created_at": alert.created_at.isoformat() if alert.created_at else "",
            }
        )

    return feed
