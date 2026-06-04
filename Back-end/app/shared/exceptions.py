# ============================================================
# PaySentinelIQ — Domain Exceptions
# Typed exception hierarchy for clean error handling
# ============================================================

from typing import Any


class PSIDomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self, message: str, code: str = "DOMAIN_ERROR", details: dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


# ── Auth Errors ──


class AuthenticationError(PSIDomainError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(PSIDomainError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, code="AUTHORIZATION_ERROR")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid email or password")


class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__("Token has expired")


class MFARequiredError(AuthenticationError):
    def __init__(self, user_id: str):
        super().__init__("MFA verification required", details={"user_id": user_id})


# ── Entity Errors ──


class NotFoundError(PSIDomainError):
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            f"{entity} not found: {identifier}",
            code="NOT_FOUND",
            details={"entity": entity, "identifier": identifier},
        )


class AlreadyExistsError(PSIDomainError):
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            f"{entity} with {field}='{value}' already exists",
            code="ALREADY_EXISTS",
            details={"entity": entity, "field": field, "value": value},
        )


class ValidationError(PSIDomainError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


# ── Business Errors ──


class PayrollProcessingError(PSIDomainError):
    def __init__(self, message: str, payroll_id: str | None = None):
        super().__init__(
            message,
            code="PAYROLL_PROCESSING_ERROR",
            details={"payroll_id": payroll_id} if payroll_id else {},
        )


class FraudDetectionError(PSIDomainError):
    def __init__(self, message: str, document_id: str | None = None):
        super().__init__(
            message,
            code="FRAUD_DETECTION_ERROR",
            details={"document_id": document_id} if document_id else {},
        )


class VerificationError(PSIDomainError):
    def __init__(self, message: str, document_id: str | None = None):
        super().__init__(
            message,
            code="VERIFICATION_ERROR",
            details={"document_id": document_id} if document_id else {},
        )


class ComplianceCheckError(PSIDomainError):
    def __init__(self, message: str, entity_id: str | None = None):
        super().__init__(
            message,
            code="COMPLIANCE_CHECK_ERROR",
            details={"entity_id": entity_id} if entity_id else {},
        )


# ── Rate Limiting ──


class RateLimitExceededError(PSIDomainError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after},
        )


# ── Infrastructure / Service Errors ──


class ServiceError(PSIDomainError):
    """Erro em serviços de infraestrutura (AWS, Redis, etc.)."""

    def __init__(self, message: str, service: str | None = None):
        super().__init__(
            message,
            code="SERVICE_ERROR",
            details={"service": service} if service else {},
        )
