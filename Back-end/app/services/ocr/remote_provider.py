from __future__ import annotations

from pathlib import Path

import httpx

from app.services.ocr.base import OCRPageResult, OCRProvider, OCRResult
from app.services.ocr.exceptions import OCRProcessingException

_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class RemoteOCRProvider(OCRProvider):
    @property
    def supports_hard_timeout(self) -> bool:
        return True

    def __init__(
        self,
        url: str,
        timeout: float = 120.0,
        api_key: str | None = None,
        engine: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._api_key = api_key
        self._engine_override = engine
        self._transport = transport

    def _configured_engine(self) -> str:
        if self._engine_override is not None:
            return self._engine_override
        try:
            from app.shared.settings import get_settings

            return get_settings().OCR_SERVICE_ENGINE
        except Exception:
            return "auto"

    async def extract_text(self, file_path: str) -> OCRResult:
        if not self._url:
            raise OCRProcessingException(
                "OCR_SERVICE_URL is not configured",
                provider="remote",
            )

        path = Path(file_path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise OCRProcessingException(
                f"Could not read file: {exc}",
                provider="remote",
            ) from exc

        mime_type = _MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")
        headers = {}
        if self._api_key:
            headers["X-OCR-Key"] = self._api_key

        response: httpx.Response | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    transport=self._transport,
                    timeout=httpx.Timeout(self._timeout, connect=5.0),
                ) as client:
                    response = await client.post(
                        f"{self._url}/ocr",
                        files={"file": (path.name, data, mime_type)},
                        data={"engine": self._configured_engine()},
                        headers=headers,
                    )
                break
            except httpx.ConnectError as exc:
                if attempt == 0:
                    continue
                raise OCRProcessingException(
                    "Could not connect to OCR service",
                    provider="remote",
                ) from exc
            except httpx.TimeoutException as exc:
                raise OCRProcessingException(
                    "OCR service request timed out",
                    provider="remote",
                ) from exc
            except httpx.HTTPError as exc:
                raise OCRProcessingException(
                    f"OCR service request failed: {exc}",
                    provider="remote",
                ) from exc

        if response is None:
            raise OCRProcessingException(
                "OCR service returned no response",
                provider="remote",
            )
        if response.status_code >= 400:
            raise OCRProcessingException(
                "OCR service returned HTTP "
                f"{response.status_code}: {response.text[:200]}",
                provider="remote",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise OCRProcessingException(
                "OCR service returned invalid JSON",
                provider="remote",
            ) from exc
        if not isinstance(payload, dict):
            raise OCRProcessingException(
                "OCR service returned an invalid payload",
                provider="remote",
            )

        pages: list[OCRPageResult] = []
        for index, page in enumerate(payload.get("pages", []), start=1):
            if not isinstance(page, dict):
                continue
            pages.append(
                OCRPageResult(
                    page_number=int(page.get("page_number", index)),
                    text=str(page.get("text", "")),
                    confidence=max(
                        0.0,
                        min(1.0, float(page.get("confidence", 0.0))),
                    ),
                    width=page.get("width"),
                    height=page.get("height"),
                )
            )

        raw_metadata = payload.get("metadata") or {}
        metadata = (
            {str(key): str(value) for key, value in raw_metadata.items()}
            if isinstance(raw_metadata, dict)
            else {}
        )
        text = payload.get("text")
        if not isinstance(text, str):
            text = "\n\n".join(page.text for page in pages)

        return OCRResult(
            text=text,
            pages=pages,
            confidence=max(
                0.0,
                min(1.0, float(payload.get("confidence", 0.0))),
            ),
            provider=str(payload.get("provider", "remote")),
            processing_time_seconds=float(
                payload.get("processing_time_seconds", 0.0)
            ),
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        if not self._url:
            return False
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(5.0, connect=2.0),
            ) as client:
                response = await client.get(f"{self._url}/ready")
            return response.status_code == 200
        except Exception:
            return False

    def get_info(self) -> dict[str, str]:
        return {
            "provider": "remote",
            "url": self._url,
            "timeout": str(self._timeout),
            "engine": self._configured_engine(),
        }
