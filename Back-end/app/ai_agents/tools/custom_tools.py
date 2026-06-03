# ============================================================
# PaySentinelIQ — AI Agent Tools (LangChain)
# Custom tools for fraud detection, OCR processing, compliance checks
# ============================================================

from typing import Any, Optional

from langchain_core.tools import tool


@tool
def analyze_payroll_discrepancy(
    employee_salary: float,
    department_median: float,
    department_std_dev: float,
) -> dict[str, Any]:
    """
    Analyze whether a salary deviates significantly from department norms.
    Returns standard deviations from median and a risk assessment.
    """
    if department_std_dev == 0:
        return {"deviation": 0.0, "risk": "low", "detail": "Cannot calculate — zero variance"}

    deviation = (employee_salary - department_median) / department_std_dev

    if deviation > 3.0:
        risk = "critical"
    elif deviation > 2.0:
        risk = "high"
    elif deviation > 1.0:
        risk = "medium"
    else:
        risk = "low"

    return {
        "deviation_sigma": round(deviation, 2),
        "risk": risk,
        "detail": f"Salary is {deviation:.1f} standard deviations {'above' if deviation > 0 else 'below'} median",
    }


@tool
def check_tax_id_format(tax_id: str) -> dict[str, Any]:
    """
    Validate tax ID format and check for known patterns of invalid IDs.
    """
    # Strip non-digits for analysis
    digits = "".join(c for c in tax_id if c.isdigit())

    issues = []

    if len(digits) != 9:
        issues.append(f"Invalid length: expected 9 digits, got {len(digits)}")

    # Check for all-same digits (common fake pattern)
    if len(set(digits)) == 1:
        issues.append("All digits identical — likely fabricated")

    # Check for sequential pattern
    if digits in "123456789" or digits in "987654321":
        issues.append("Sequential digits — likely fabricated")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "masked": f"***-**-{tax_id[-4:]}" if len(tax_id) >= 4 else "***",
    }


@tool
def analyze_metadata_integrity(
    file_created: str,
    file_modified: str,
    payroll_period_start: str,
    software: str,
) -> dict[str, Any]:
    """
    Check document metadata for inconsistencies and suspicious patterns.
    """
    anomalies = []
    risk_score = 0

    # Check creation date vs payroll period
    if file_created > payroll_period_start:
        anomalies.append("Document created AFTER payroll period start — possible backdating")
        risk_score += 30

    # Check for suspicious PDF producers
    suspicious_software = ["wkhtmltopdf", "phantomjs", "puppeteer"]
    if any(sw in software.lower() for sw in suspicious_software):
        anomalies.append(f"Unusual PDF producer for payroll: {software}")
        risk_score += 20

    # Check modification gap
    from datetime import datetime
    try:
        created = datetime.fromisoformat(file_created.replace("Z", "+00:00"))
        modified = datetime.fromisoformat(file_modified.replace("Z", "+00:00"))
        gap_hours = (modified - created).total_seconds() / 3600
        if gap_hours > 24:
            anomalies.append(f"Large gap between creation and modification: {gap_hours:.0f} hours")
            risk_score += 10
    except (ValueError, TypeError):
        pass

    return {
        "anomalies": anomalies,
        "integrity_risk": min(risk_score, 100),
        "verdict": "clean" if risk_score == 0 else "suspicious" if risk_score < 50 else "tampered",
    }
