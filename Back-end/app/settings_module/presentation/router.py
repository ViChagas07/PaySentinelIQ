# ============================================================
# PaySentinelIQ — User Settings / Preferences Router
# Persists user preferences (theme, notifications, accessibility)
# ============================================================

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.auth.dependencies import get_current_user_id, get_current_tenant_id

router = APIRouter()


class UserSettingsRequest(BaseModel):
    """User preferences schema matching front-end SettingsState."""
    model_config = ConfigDict(strict=True)

    # Appearance
    theme: Optional[str] = Field(default=None, pattern="^(dark|light|system)$")
    primary_color: Optional[str] = Field(default=None, pattern="^(blue|green|purple|orange|red|teal)$")
    background_color: Optional[str] = Field(default=None, pattern="^(navy|charcoal|slate|midnight|espresso|forest)$")
    bold_text: Optional[bool] = None
    font_size: Optional[str] = Field(default=None, pattern="^(small|medium|large|xlarge)$")
    element_size: Optional[str] = Field(default=None, pattern="^(compact|comfortable|spacious)$")

    # Language
    locale: Optional[str] = None

    # Accessibility
    high_contrast: Optional[bool] = None
    screen_reader_optimized: Optional[bool] = None
    keyboard_nav: Optional[bool] = None
    focus_indicator: Optional[bool] = None
    dyslexia_font: Optional[bool] = None
    reduced_motion: Optional[bool] = None

    # Notifications
    email_alerts: Optional[bool] = None
    push_notifications: Optional[bool] = None
    desktop_alerts: Optional[bool] = None
    sound_alerts: Optional[bool] = None
    alert_threshold: Optional[int] = Field(default=None, ge=0, le=100)
    fraud_alert_email: Optional[str] = None
    digest_frequency: Optional[str] = Field(default=None, pattern="^(daily|weekly|monthly|never)$")

    # Account
    timezone: Optional[str] = None

    # Developer
    developer_mode: Optional[bool] = None


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
    alert_threshold: int = 70
    fraud_alert_email: str = ""
    digest_frequency: str = "daily"

    # Account
    timezone: str = "America/Sao_Paulo"

    # Developer
    developer_mode: bool = False


# ── In-memory settings store (production: PostgreSQL or Redis) ──
_user_settings: dict[str, dict] = {}


def _get_defaults() -> dict:
    return UserSettingsResponse().model_dump()


def _get_or_create_settings(user_id: str) -> dict:
    if user_id not in _user_settings:
        _user_settings[user_id] = _get_defaults()
    return _user_settings[user_id]


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get current user preferences/settings."""
    settings = _get_or_create_settings(user_id)
    return UserSettingsResponse(**settings)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    body: UserSettingsRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
):
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
):
    """Reset all user preferences to defaults."""
    defaults = _get_defaults()
    _user_settings[user_id] = defaults
    return UserSettingsResponse(**defaults)
