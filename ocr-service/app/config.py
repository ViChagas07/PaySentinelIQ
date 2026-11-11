from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass
class ServiceSettings:
    max_mb: float = 25.0
    max_pages: int = 10
    dpi: int = 300
    api_key: str | None = None
    force_fallback: bool = False

    @classmethod
    def from_env(cls) -> ServiceSettings:
        api_key = os.getenv("OCR_SERVICE_API_KEY") or None
        force_fallback = os.getenv(
            "OCR_SERVICE_FORCE_FALLBACK",
            "",
        ).lower() in {"1", "true", "yes", "on"}
        return cls(
            max_mb=_float_env("OCR_SERVICE_MAX_MB", 25.0),
            max_pages=_int_env("OCR_SERVICE_MAX_PAGES", 10),
            dpi=_int_env("OCR_SERVICE_DPI", 300),
            api_key=api_key,
            force_fallback=force_fallback,
        )
