# ============================================================
# PaySentinelIQ — Unit Test Example
# Domain logic tests for auth, payroll, risk scoring
# ============================================================

import uuid
from datetime import datetime, timezone

import pytest

from app.shared.domain_primitives import Money, RiskScore, RiskLevel


class TestMoneyValueObject:
    def test_money_creation(self):
        money = Money(amount=100.0, currency="USD")
        assert money.amount == 100.0
        assert money.currency == "USD"

    def test_money_cannot_be_negative(self):
        with pytest.raises(ValueError):
            Money(amount=-50.0)

    def test_money_addition(self):
        m1 = Money(100.0)
        m2 = Money(50.0)
        result = m1 + m2
        assert result.amount == 150.0

    def test_money_subtraction(self):
        m1 = Money(100.0)
        m2 = Money(30.0)
        result = m1 - m2
        assert result.amount == 70.0

    def test_money_cannot_subtract_below_zero(self):
        m1 = Money(50.0)
        m2 = Money(100.0)
        with pytest.raises(ValueError):
            m1 - m2

    def test_money_different_currencies(self):
        m1 = Money(100.0, "USD")
        m2 = Money(50.0, "EUR")
        with pytest.raises(ValueError):
            m1 + m2


class TestRiskScore:
    def test_risk_score_low(self):
        score = RiskScore(value=20.0, confidence=0.95)
        assert score.level == RiskLevel.LOW

    def test_risk_score_medium(self):
        score = RiskScore(value=50.0, confidence=0.85)
        assert score.level == RiskLevel.MEDIUM

    def test_risk_score_high(self):
        score = RiskScore(value=75.0, confidence=0.90)
        assert score.level == RiskLevel.HIGH

    def test_risk_score_critical(self):
        score = RiskScore(value=90.0, confidence=0.88)
        assert score.level == RiskLevel.CRITICAL

    def test_risk_score_invalid_range(self):
        with pytest.raises(ValueError):
            RiskScore(value=150.0, confidence=0.5)

    def test_risk_score_invalid_confidence(self):
        with pytest.raises(ValueError):
            RiskScore(value=50.0, confidence=1.5)


class TestAuthDomain:
    def test_user_creation(self):
        from app.auth.domain import User
        user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_xxx",
            role="fraud_analyst",
        )
        assert user.is_active is True
        assert user.mfa_enabled is False
        assert user.email == "test@example.com"

    def test_user_deactivation(self):
        from app.auth.domain import User
        user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_xxx",
            role="viewer",
        )
        user.deactivate()
        assert user.is_active is False

    def test_refresh_token_validity(self):
        from app.auth.domain import RefreshToken
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            token_hash="abc123",
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        assert token.is_valid is True
        assert token.is_expired is False

        token.revoke()
        assert token.is_valid is False
