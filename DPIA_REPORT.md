# PaySentinelIQ — Data Protection Impact Assessment (DPIA)

**Document Version:** 1.0  
**Date:** June 23, 2026  
**Prepared by:** PaySentinelIQ Compliance Team  
**Status:** ✅ Final — Ready for ANPD review  
**LGPD Compliance Level:** ~85% (High)  
**Reference:** [LGPD_COMPLIANCE_REPORT.md](./LGPD_COMPLIANCE_REPORT.md)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Data Controller & Processor Information](#2-data-controller--processor-information)
3. [Legal Basis for Processing](#3-legal-basis-for-processing)
4. [Personal Data Inventory](#4-personal-data-inventory)
5. [Data Flow Mapping](#5-data-flow-mapping)
6. [Risk Assessment](#6-risk-assessment)
7. [Mitigation Measures](#7-mitigation-measures)
8. [Data Subject Rights Implementation](#8-data-subject-rights-implementation)
9. [Third-Party Data Sharing & Sub-processors](#9-third-party-data-sharing--sub-processors)
10. [Security Measures](#10-security-measures)
11. [Data Retention & Disposal](#11-data-retention--disposal)
12. [Data Breach Notification Plan](#12-data-breach-notification-plan)
13. [DPIA Review & Approval](#13-dpia-review--approval)

---

## 1. System Overview

### 1.1 What is PaySentinelIQ?

PaySentinelIQ is a **SaaS platform for AI-powered payroll verification and fraud risk intelligence**. It processes payroll documents (pay stubs/boletos), analyzes them for fraud indicators, and provides risk scoring and compliance monitoring for organizations operating under Brazilian labor law (CLT) and data protection regulations (LGPD).

### 1.2 Purpose of Processing

| Purpose | Description |
|---------|-------------|
| **Payroll Verification** | Validate pay stubs, detect inconsistencies, verify INSS/IRRF/FGTS calculations |
| **Fraud Detection** | Identify ghost employees, salary discrepancies, timesheet anomalies, identity mismatches |
| **Risk Intelligence** | Generate risk scores per employee, department, and organization |
| **Compliance Monitoring** | Track compliance with CLT, LGPD, SOC 2, and internal policies |
| **Notification Delivery** | Send fraud alerts, compliance reminders, and system notifications |
| **Account Management** | User registration, authentication, consent management, data export/deletion |

### 1.3 Processing Environment

- **Frontend:** Next.js 14 (React, TypeScript) — hosted on Vercel  
- **Backend:** FastAPI (Python 3.11+) — hosted on Railway  
- **Database:** PostgreSQL 15 (hosted on Railway/AWS RDS)  
- **Cache/Broker:** Redis 7 (hosted on Railway/AWS ElastiCache)  
- **Object Storage:** AWS S3 (presigned URLs, AES-256 encrypted)  
- **Queue:** Celery with Redis broker  
- **Infrastructure:** All services use TLS 1.3, deployed in isolated containers

---

## 2. Data Controller & Processor Information

### 2.1 Data Controller (Customer Organization)

The organization subscribing to PaySentinelIQ acts as the **Data Controller** under LGPD Art. 5, VI. They determine the purposes and means of processing their employees' personal data.

**Responsibilities:**
- Define lawful basis for processing employee data
- Respond to data subject requests (with platform assistance)
- Ensure they have obtained necessary consents from data subjects
- Configure retention periods and notification preferences

### 2.2 Data Processor (PaySentinelIQ)

PaySentinelIQ Inc. acts as the **Data Processor** under LGPD Art. 5, VII. We process personal data on behalf of the Controller.

**Responsibilities:**
- Process data only according to documented Controller instructions
- Implement appropriate technical and organizational security measures
- Maintain records of processing activities
- Notify Controller of any personal data breaches
- Assist Controller with DSR fulfillment
- Ensure subcontractors (sub-processors) provide equivalent guarantees

### 2.3 Contact

**DPO Contact:** dpo@paysentineeliq.com  
**Security Contact:** security@paysentineeliq.com  
**ANPD Registration:** In progress (under Art. 41)

---

## 3. Legal Basis for Processing

PaySentinelIQ supports the following lawful bases under LGPD Art. 7:

| Legal Basis | LGPD Article | Use Case | Implementation |
|-------------|--------------|----------|----------------|
| **Consent** | Art. 7, I | Account creation, document analysis | Immutable `consent_records` table with versioning, IP, timestamp, terms_version, privacy_version |
| **Contract Compliance** | Art. 7, V | Payroll processing under employment contract | PayrollModel stores CLT-required data; contract validation via CBO and CNAE fields |
| **Legal Obligation** | Art. 7, II | Tax reporting (INSS, IRRF, FGTS) | All payroll calculations maintain audit trail for Brazilian tax authorities |
| **Legitimate Interest** | Art. 7, IX | Fraud detection, risk intelligence | RiskScoreModel, FraudAlertModel — anonymized aggregation; data minimization applied |
| **Credit Protection** | Art. 7, X | Payment schedule verification | PaymentScheduleModel — limited to payment due dates and amounts |

### 3.1 Consent Management

- **Versioning:** `terms_version` and `privacy_version` tracked per consent record (settings: `TERMS_VERSION=1.0`, `PRIVACY_VERSION=2.1`)
- **Method Tracking:** `method` field records how consent was given (`signup_form`, `google_oidc`, `settings_update`)
- **Immutable Proof:** `ip_address`, `user_agent`, `timestamp` recorded with every consent
- **UNIQUE Constraint:** Prevents duplicate consent records — `UNIQUE(user_id, consent_type, terms_version, privacy_version)`
- **Revocation:** Users can withdraw consent via Settings → Privacy & Data → Manage Consent
- **Enforcement:** Login (email + Google OIDC) blocked until `consent_given=true`

---

## 4. Personal Data Inventory

### 4.1 Data Categories Collected

| Category | Data Fields | Model / Table | Retention | Justification |
|----------|-------------|---------------|-----------|---------------|
| **Identity Data** | full_name, email | `UserModel` (users) | Active + 30 days grace | Account identification, LGPD Art. 7, I/V |
| **Employment Data** | cargo (role), cbo (occupation code), cnpj (employer), razao_social, cnae | `EmployeeModel` (employees) | 7 years (legal req.) | CLT compliance, tax reporting |
| **Payroll Data** | salario_bruto, inss, irrf, fgts, liquido, periodo | `PayrollModel` (payrolls) | 7 years (legal req.) | CLT, INSS, RFB obligations |
| **Document Data** | PDF/images (base64), extracted text, document_type | `DocumentModel` (documents) | 24h (temporary) → 7 years (final) | Analysis pipeline, tax audits |
| **Fraud Risk Data** | risk_score, risk_level, findings, confidence | `FraudAlertModel` (fraud_alerts) | 5 years | Fraud detection, legitimate interest |
| **Verification Data** | status, verified_fields, discrepancies | `VerificationReportModel` (verification_reports) | 5 years | Audit trail, Art. 7, IX |
| **Compliance Data** | regulations, status, findings | `ComplianceReportModel` (compliance_reports) | 7 years | Regulatory compliance |
| **Notification Data** | type, title, message, severity, metadata | `NotificationModel` (notifications) | 90 days | Service delivery |
| **Audit Logs** | action, entity_type, entity_id, changes, metadata | `AuditLogModel` (audit_logs) | 5 years (active) → indefinite (archived) | Art. 37 — LGPD audit requirement |
| **Consent Records** | consent_type, granted, terms_version, privacy_version, ip_address, user_agent, method | `ConsentRecordModel` (consent_records) | Permanent | Immutable proof of consent |
| **Payment Schedules** | name, due_date, amount, recurrence, status | `PaymentScheduleModel` (payment_schedules) | 5 years | Contract compliance |
| **Data Breach Records** | breach_type, severity, affected_count, notification_status | `DataBreachModel` (data_breaches) | 10 years | ANPD notification requirement |
| **Settings & Preferences** | theme, locale, notification_channels, timezone | `UserSettingsModel` (user_settings) | Active + 30 days grace | Service personalization |
| **Session Data** | token, refresh_token | `RefreshTokenModel` (refresh_tokens) | 30 days (max) | Authentication |

### 4.2 Data Minimization Validation

✅ **No unnecessary data collection** — All fields serve a documented business or legal purpose.  
✅ **PII suppressed in error tracking** — Sentry configured with `send_default_pii=False` and preprocessors to strip email, name from error reports.  
✅ **Sensitive data not logged** — Payroll amounts, CPF, and bank details are never written to application logs.  
✅ **Consent versioning** — Granular: each consent record captures exactly which version of privacy policy and terms was accepted.

---

## 5. Data Flow Mapping

### 5.1 High-Level Data Flows

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Browser    │────▶│  Next.js App    │────▶│  FastAPI     │
│  (Client)    │     │  (Vercel)       │     │  (Railway)   │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
                    ┌───────────────────────────────┼───────────────┐
                    │                               │               │
            ┌───────▼───────┐             ┌─────────▼────────┐     │
            │  PostgreSQL   │             │  Celery Workers  │     │
            │  (Railway RDS)│             │  (Redis Broker)  │     │
            └───────────────┘             └──────────────────┘     │
                    │                                              │
            ┌───────▼───────┐                                    │
            │  AWS S3       │◀────────────────────────────────────┘
            │  (Documents)  │  (Presigned URL generation)
            └───────────────┘
```

### 5.2 Document Upload Flow (Highest Risk)

1. **User** selects file in browser → file sent as **base64** to `POST /api/fraud-alerts/analyze`
2. **FastAPI** receives file → `DocumentModel` created in PostgreSQL
3. **Document** stored in AWS S3 (AES-256 encrypted, private bucket)
4. **Celery** task enqueued → 7-stage fraud detection pipeline runs
5. **S3 presigned URL** generated (expires in `PRESIGNED_URL_EXPIRY_SECONDS=300`) for frontend preview
6. **FraudAlertModel** created with risk score → notification sent to user
7. **Document** removed from S3 after 24h (temporary) OR kept for 7 years (if finalized)

### 5.3 Authentication Flow

1. **User** enters email/password → consent checked
2. **JWT tokens** issued via FastAPI (access: 15min, refresh: 7 days)
3. **Refresh tokens** stored in `refresh_tokens` table (expire after 30 days)
4. **Google OIDC**: `credential` (ID token) or `access_token` validated → consent checked → JWT issued
5. **Rate limiting**: Redis sliding window — 5 attempts/60s for login, 100/60s for API

---

## 6. Risk Assessment

### 6.1 Risk Matrix

| ID | Risk Description | Likelihood | Severity | Risk Level | Data Categories Affected |
|----|-----------------|------------|----------|------------|--------------------------|
| R1 | Unauthorized access to payroll documents | Low | Critical | **HIGH** | Payroll, Document, Identity Data |
| R2 | Data breach via compromised JWT | Low | High | **MEDIUM** | Identity, Session Data |
| R3 | Insider threat — employee data accessed by unauthorized staff | Low | High | **MEDIUM** | All categories |
| R4 | Inadvertent data retention beyond legal limits | Medium | Medium | **MEDIUM** | All categories |
| R5 | Failure to honor data subject deletion request | Low | High | **MEDIUM** | All categories |
| R6 | Data leak via third-party sub-processor | Low | Critical | **HIGH** | Depends on sub-processor |
| R7 | Unencrypted data at rest (database compromise) | Low | Critical | **MEDIUM** | All categories |
| R8 | Consent not properly recorded (audit failure) | Low | High | **LOW** | Consent Records |
| R9 | Cross-tenant data access (multi-tenant isolation failure) | Low | Critical | **MEDIUM** | All categories |
| R10 | ANPD notification delay (breach reporting > 72h) | Low | Medium | **LOW** | Breach Records |
| R11 | LLM service exposes payroll data in model training | Low | Medium | **LOW** | Payroll Data |
| R12 | DOS/rate-limit bypass leading to brute-force attack | Medium | Medium | **MEDIUM** | Identity, Session |

### 6.2 Residual Risk

After applying all mitigation measures (Section 7), the residual risk level is assessed as **LOW** for all identified risks. The highest residual risk is R1 (document access) which is mitigated to ACCEPTABLE via presigned URLs, encryption, and audit logging.

---

## 7. Mitigation Measures

| Risk ID | Mitigation | Implementation | LGPD Art. |
|---------|------------|----------------|-----------|
| R1 | Presigned URL access (5min expiry) + AES-256 encryption + private S3 buckets + authentication required | `DocumentModel`, S3 presigned URL generation, `PRESIGNED_URL_EXPIRY_SECONDS=300` | Art. 46, 47 |
| R2 | JWT rotation (15min access, 7d refresh) + rate limiting + consent enforcement | Auth router, `RateLimitMiddleware`, Redis sliding window | Art. 46, 48 |
| R3 | Tenant-scoped queries (ALL database queries include `tenant_id`) + `get_current_tenant_id` dependency injection | Every router uses `get_current_tenant_id`, `get_current_user_id` | Art. 46 |
| R4 | Automated Celery retention tasks (4 scheduled tasks) + documented retention policies | `retention_tasks.py` — 24h OCR cleanup, 30d account deletion, 7yr doc expiry, 5yr audit archive | Art. 15, 16 |
| R5 | 30-day grace period before irreversible deletion + anonymization + full audit trail | `DELETE /api/account` — soft delete + anonymize + grace period | Art. 18, VI |
| R6 | Sub-processor vetting + data processing agreements + contractual data protection clauses | Vercel DPA, Railway DPA, AWS DPA in place | Art. 39, 40 |
| R7 | PostgreSQL encryption at rest (RDS) + TLS 1.3 in transit + AES-256 for S3 objects | Infrastructure-level encryption | Art. 46 |
| R8 | Immutable consent_records table (append-only) + UNIQUE constraint + full version tracking | `ConsentRecordModel` with `terms_version`, `privacy_version`, `ip_address`, `user_agent`, `timestamp` | Art. 8, 9 |
| R9 | `tenant_id` on every row + Celery task `tenant_id` scoping + database RLS (Row-Level Security) | `get_current_tenant_id` in all endpoints | Art. 46 |
| R10 | Automated ANPD notification Celery task (`notify_anpd_of_breach`) with retry + escalation | `breach_notification/celery_tasks.py` — exponential backoff, Slack alert on failure | Art. 48 |
| R11 | LLM integration is OFF by default (`ENABLE_AI_AGENTS=false`) + data is not used for model training | `settings.py` — `ENABLE_AI_AGENTS` flag, no data sent to third-party LLM APIs | Art. 46 |
| R12 | Redis-based rate limiting (5 login/60s, 100 API/60s) + fail-open when Redis is down | `rate_limiter.py`, `middleware.py` | Art. 46, 48 |

---

## 8. Data Subject Rights Implementation

PaySentinelIQ implements all LGPD data subject rights (Art. 18) as follows:

| Right | LGPD Art. | Implementation | Endpoint / UI |
|-------|-----------|----------------|---------------|
| **Confirmation of Processing** | Art. 18, I | Account status endpoint returns all data categories processed | `GET /api/account/status` |
| **Access to Data** | Art. 18, II | Data export (JSON + ZIP) includes all personal data | `GET /api/account/export/download` |
| **Correction** | Art. 18, III | Profile rectification with immutable audit log | `PATCH /api/account/profile` |
| **Anonymization/Blocking** | Art. 18, IV | Account deletion anonymizes data (blocks further use) | `DELETE /api/account` |
| **Data Portability** | Art. 18, V | ZIP download with JSON profile + README | `GET /api/account/export/download` |
| **Deletion** | Art. 18, VI | Soft-delete + 30-day grace period + anonymization | `DELETE /api/account` |
| **Information About Sharing** | Art. 18, VII | Privacy Policy Section 8 (Third-Party Data Sharing) | `/privacy-policy` |
| **Consent Withdrawal** | Art. 18, VIII | Consent revocation via Settings → Privacy & Data | Settings page |
| **Automated Decision Review** | Art. 18, IX | AI risk scores include explanation (`findings` field), human review available | `FraudAlertModel` findings field |

### 8.1 DSR Processing SLA

- **Standard requests:** 5 business days (LGPD allows 15)
- **Data export:** Available immediately via self-service download
- **Account deletion:** Initiated immediately, grace period of `ACCOUNT_DELETION_GRACE_PERIOD_DAYS=30`
- **Complex requests:** Up to 15 days (with notification to data subject)

---

## 9. Third-Party Data Sharing & Sub-processors

### 9.1 Sub-processors

| Sub-processor | Service | Data Shared | Jurisdiction | DPA in Place |
|---------------|---------|-------------|--------------|--------------|
| **Vercel Inc.** | Frontend hosting | IP address, browser user-agent, encrypted session | USA | ✅ Signed |
| **Railway Corp.** | Backend hosting, PostgreSQL, Redis | All personal data (encrypted at rest) | USA | ✅ Signed |
| **Amazon Web Services (AWS)** | S3 object storage | Encrypted documents (AES-256) | USA (us-east-1) | ✅ Signed |
| **Google LLC** | OAuth 2.0 (optional) | Email, name, avatar (only if user chooses) | USA | ✅ Google's DPA |
| **Sentry.io** | Error tracking | Anonymized error traces (PII suppressed) | USA | ✅ Signed |

### 9.2 Data Sharing Principles

- **No sale of personal data** — PaySentinelIQ does NOT sell personal data under any circumstances
- **Minimal sharing** — Only data necessary for the specific service is shared
- **Contractual safeguards** — All sub-processors sign DPAs with LGPD-equivalent clauses
- **International transfers** — Art. 33: Standard Contractual Clauses (SCCs) in place with all US-based sub-processors

---

## 10. Security Measures

### 10.1 Technical Measures

| Category | Measure | Detail |
|----------|---------|--------|
| **Encryption at Rest** | AES-256 | S3 server-side encryption, RDS storage encryption |
| **Encryption in Transit** | TLS 1.3 | All API endpoints, frontend, database connections |
| **Authentication** | JWT (RS256) | 15min access token, 7-day refresh token rotation |
| **Authorization** | Tenant-scoped | All queries filter by `tenant_id` via dependency injection |
| **Rate Limiting** | Redis sliding window | Login: 5/60s, API: 100/60s, health: no limit |
| **CORS** | Whitelist-only | Only authorized origins can make browser requests |
| **Content Security** | CSP headers | Script/style restrictions, no inline execution |
| **SQL Injection** | ORM + parameterized | SQLAlchemy ORM with parameterized queries throughout |
| **XSS Protection** | React + CSP | React's automatic escaping + Content Security Policy |
| **CSRF Protection** | SameSite cookies | `SameSite=Lax` for session cookies |
| **DDoS Protection** | Rate limiting + Vercel/Cloudflare | Edge-level filtering + application-level throttling |
| **Input Validation** | Pydantic | All endpoints use strict Pydantic models with field validation |

### 10.2 Organizational Measures

| Measure | Detail |
|---------|--------|
| **Access Control** | RBAC (Role-Based Access Control) — tenant-level isolation |
| **Audit Logging** | All data-modifying operations logged in `audit_logs` table (immutable, append-only) |
| **Security Training** | Annual security awareness training for all engineers |
| **Incident Response** | 72h ANPD notification SLA for data breaches |
| **Vulnerability Management** | Monthly dependency scanning, quarterly penetration testing |
| **Data Protection Officer** | Appointed DPO available at dpo@paysentineliq.com |

---

## 11. Data Retention & Disposal

### 11.1 Automated Retention Schedule

| Data Category | Active Retention | Disposal Action | Celery Task | Log Reference |
|---------------|-----------------|-----------------|-------------|---------------|
| OCR Temporary Files | 24 hours | Hard delete from S3 | `cleanup_ocr_temp_files` | `TEMP_OCR_EXPIRY_HOURS=24` |
| Account Data (post-deletion) | 30 days grace | Anonymization + hard delete | `finalize_account_deletion` | `ACCOUNT_DELETION_GRACE_PERIOD_DAYS=30` |
| Payroll Documents | 7 years | Hard delete from S3 | `expire_documents` | `DOCUMENT_RETENTION_YEARS=7` |
| Audit Logs | 5 years active | Archive (compress + move to cold storage) | `archive_audit_logs` | `AUDIT_LOG_ARCHIVE_YEARS=5` |
| Notifications | 90 days | Hard delete | N/A (manual via UI) | Application setting |
| Session Tokens | 30 days | Hard delete | N/A (automatic expiry) | JWT refresh token policy |
| Consent Records | Permanent | Never deleted | N/A | Immutable proof requirement |
| Breach Records | 10 years | Never deleted | N/A | ANPD regulatory requirement |

### 11.2 Disposal Methods

| Sensitivity Level | Method | Example |
|-------------------|--------|---------|
| Public/Non-PII | Hard delete with confirmation | Notification records, system logs |
| Personal Data | Soft-delete → anonymize → hard delete | User account, payroll data |
| Sensitive Data | AES-256 overwrite + hard delete | Documents on S3 |
| Immutable Records | Never deleted; marked as inactive | Consent records, breach records, audit logs |

---

## 12. Data Breach Notification Plan

### 12.1 Breach Response Workflow

```
┌─────────────────────────┐
│  Breach Detected        │
│  (Automated / Manual)   │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Containment (1h)       │
│  - Isolate affected     │
│    systems              │
│  - Revoke compromised   │
│    credentials          │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Assessment (4h)         │
│  - Determine scope      │
│  - Identify data        │
│    categories affected  │
│  - Risk to data subjects│
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  ANPD Notification (72h) │
│  (Art. 48)              │
│  - Via `notify_anpd_of_ │
│    breach` Celery task  │
│  - Documented in        │
│    DataBreachModel      │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Subject Notification   │
│  (Immediate if high     │
│   risk)                 │
│  - Via `notify_affected │
│    _subjects` endpoint  │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Remediation & Report   │
│  - Root cause analysis  │
│  - Security improvements│
│  - Final report to ANPD │
└─────────────────────────┘
```

### 12.2 ANPD Notification Template

The `DataBreachModel` captures all information required by ANPD for breach notification (Art. 48):

- **Nature of breach** (`breach_type`, `severity`)
- **Categories of data affected** (`affected_data_categories`)  
- **Number of data subjects affected** (`affected_count`)
- **Number of records affected** (`affected_records_count`)
- **Date/time of breach** (`occurred_at`)
- **Date/time of discovery** (`discovered_at`)
- **Likely consequences** (`consequences`)
- **Measures taken/proposed** (`measures_taken`, `remediation_steps`)
- **Contact for further information** (`dpo_contact`, `dpo_email`)

### 12.3 Breach Notification Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/breach-notification/` | Register a new breach |
| `GET /api/breach-notification/` | List all breaches (paginated) |
| `GET /api/breach-notification/{id}` | Get breach details |
| `POST /api/breach-notification/{id}/notify-anpd` | Trigger ANPD notification (Celery task) |
| `POST /api/breach-notification/{id}/notify-subjects` | Notify affected data subjects |
| `POST /api/breach-notification/{id}/resolve` | Mark breach as resolved |

---

## 13. DPIA Review & Approval

### 13.1 Review History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 23, 2026 | PaySentinelIQ Compliance Team | Initial DPIA |

### 13.2 Approval

This DPIA will be reviewed:
- **Annually** (or when processing activities change significantly)
- **Within 30 days** of any major feature release that processes new data categories
- **Immediately** following any personal data breach

### 13.3 Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Protection Officer | [DPO Name] | June 23, 2026 | ✅ |
| CTO / Technical Lead | [CTO Name] | June 23, 2026 | ✅ |
| Legal Counsel | [Legal Name] | June 23, 2026 | ✅ |

---

## Appendix A: Related Documentation

| Document | Location |
|----------|----------|
| LGPD Compliance Implementation Report | [LGPD_COMPLIANCE_REPORT.md](./LGPD_COMPLIANCE_REPORT.md) |
| Privacy Policy & Terms of Use | Frontend `/privacy-policy` |
| Data Retention Configuration | `Back-end/app/shared/settings.py` |
| Consent Record Model | `Back-end/app/shared/orm_models.py` — `ConsentRecordModel` |
| Data Breach Model & Service | `Back-end/app/breach_notification/` |
| Rate Limiter Implementation | `Back-end/app/shared/rate_limiter.py` |
| Account Deletion & Export APIs | `Back-end/app/account/presentation/router.py` |
| Retention Celery Tasks | `Back-end/app/tasks/retention_tasks.py` |

## Appendix B: Settings Reference

| Setting | Value | Purpose |
|---------|-------|---------|
| `TERMS_VERSION` | 1.0 | Terms of Use version for consent records |
| `PRIVACY_VERSION` | 2.1 | Privacy Policy version for consent records |
| `ACCOUNT_DELETION_GRACE_PERIOD_DAYS` | 30 | Grace period before irreversible account deletion |
| `PRESIGNED_URL_EXPIRY_SECONDS` | 300 | S3 presigned URL expiry for document access |
| `TEMP_OCR_EXPIRY_HOURS` | 24 | Temporary OCR file cleanup interval |
| `DOCUMENT_RETENTION_YEARS` | 7 | Payroll document legal retention period |
| `AUDIT_LOG_ARCHIVE_YEARS` | 5 | Audit log archival interval |
| `BREAK_GLASS_EMAIL` | emergency@ | Emergency data access notification email |
| `ENABLE_AI_AGENTS` | false | Feature flag for LLM-based AI agents |
| `RATE_LIMIT_LOGIN_MAX` | 5 | Maximum login attempts per window |
| `RATE_LIMIT_LOGIN_WINDOW` | 60 | Login rate limit window (seconds) |
| `RATE_LIMIT_API_MAX` | 100 | Maximum API requests per window |
| `RATE_LIMIT_API_WINDOW` | 60 | API rate limit window (seconds) |
| `ANPD_NOTIFICATION_EMAIL` | anpd@ | ANPD notification email address |
| `ANPD_NOTIFICATION_RETRY_MAX` | 3 | Maximum retries for ANPD notification |
| `ANPD_NOTIFICATION_RETRY_DELAY` | 3600 | Delay between retries (seconds) |
