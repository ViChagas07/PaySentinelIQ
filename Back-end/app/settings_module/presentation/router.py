# ============================================================
# PaySentinelIQ — User Settings / Preferences Router
# Persists user preferences (theme, notifications, accessibility)
# ============================================================


from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import get_current_tenant_id, get_current_user_id

router = APIRouter()


class UserSettingsRequest(BaseModel):
    """User preferences schema matching front-end SettingsState."""

    model_config = ConfigDict(strict=True)

    # Appearance
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    primary_color: str | None = Field(default=None, pattern="^(blue|green|purple|orange|red|teal)$")
    background_color: str | None = Field(
        default=None, pattern="^(navy|charcoal|slate|midnight|espresso|forest)$"
    )
    bold_text: bool | None = None
    font_size: str | None = Field(default=None, pattern="^(small|medium|large|xlarge)$")
    element_size: str | None = Field(default=None, pattern="^(compact|comfortable|spacious)$")

    # Language
    locale: str | None = None

    # Accessibility
    high_contrast: bool | None = None
    screen_reader_optimized: bool | None = None
    keyboard_nav: bool | None = None
    focus_indicator: bool | None = None
    dyslexia_font: bool | None = None
    reduced_motion: bool | None = None

    # Notifications
    email_alerts: bool | None = None
    push_notifications: bool | None = None
    desktop_alerts: bool | None = None
    sound_alerts: bool | None = None
    whatsapp_alerts: bool | None = None
    telegram_alerts: bool | None = None
    slack_alerts: bool | None = None
    in_app_alerts: bool | None = None
    alert_threshold: int | None = Field(default=None, ge=0, le=100)
    fraud_alert_email: str | None = None
    digest_frequency: str | None = Field(default=None, pattern="^(daily|weekly|monthly|never)$")

    # Notification destinations
    telegram_username: str | None = Field(default=None, max_length=64)
    whatsapp_number: str | None = Field(default=None, max_length=32)
    slack_destination: str | None = Field(default=None, max_length=128)

    # Account
    timezone: str | None = None

    # Developer
    developer_mode: bool | None = None


class UserSettingsResponse(BaseModel):
    """Full user settings response."""

    model_config = ConfigDict(strict=True)

    # Appearance
    theme: str = "dark"
    primary_color: str = "blue"
    background_color: str = "navy"
    bold_text: bool = False
    font_size: str = "medium"
    element_size: str = "comfortable"

    # Language
    locale: str = "en"

    # Accessibility
    high_contrast: bool = False
    screen_reader_optimized: bool = False
    keyboard_nav: bool = True
    focus_indicator: bool = True
    dyslexia_font: bool = False
    reduced_motion: bool = False

    # Notifications
    email_alerts: bool = True
    push_notifications: bool = False
    desktop_alerts: bool = False
    sound_alerts: bool = False
    whatsapp_alerts: bool = False
    telegram_alerts: bool = False
    slack_alerts: bool = False
    in_app_alerts: bool = False
    alert_threshold: int = 70
    fraud_alert_email: str = ""
    digest_frequency: str = "daily"

    # Notification destinations
    telegram_username: str | None = None
    whatsapp_number: str | None = None
    slack_destination: str | None = None

    # Account
    timezone: str = "America/Sao_Paulo"

    # Developer
    developer_mode: bool = False


# ── In-memory settings store (production: PostgreSQL or Redis) ──
_user_settings: dict[str, dict[str, Any]] = {}


def _get_defaults() -> dict[str, Any]:
    return UserSettingsResponse().model_dump()


def _get_or_create_settings(user_id: str) -> dict[str, Any]:
    if user_id not in _user_settings:
        _user_settings[user_id] = _get_defaults()
    return _user_settings[user_id]


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> UserSettingsResponse:
    """Get current user preferences/settings."""
    settings = _get_or_create_settings(user_id)
    return UserSettingsResponse(**settings)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    body: UserSettingsRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> UserSettingsResponse:
    """Update user preferences. Only provided fields are changed."""
    current = _get_or_create_settings(user_id)

    # Merge only provided (non-None) fields
    update_data = body.model_dump(exclude_none=True)
    current.update(update_data)

    _user_settings[user_id] = current

    return UserSettingsResponse(**current)


@router.post("/reset", response_model=UserSettingsResponse)
async def reset_settings(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> UserSettingsResponse:
    """Reset all user preferences to defaults."""
    defaults = _get_defaults()
    _user_settings[user_id] = defaults
    return UserSettingsResponse(**defaults)
