# ============================================================
# PaySentinelIQ — BrasilAPI Client
# Async HTTP client for BrasilAPI with Redis caching, retry,
# exponential backoff, and graceful degradation.
# ============================================================

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.shared.redis_client import RedisCache

logger = logging.getLogger(__name__)

BRASIL_API_BASE = "https://brasilapi.com.br/api"


class BrasilApiError(Exception):
    """Raised when BrasilAPI returns an error or is unreachable."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


@dataclass
class BrasilApiCompany:
    """Parsed CNPJ data from BrasilAPI."""

    cnpj: str
    razao_social: str
    nome_fantasia: str | None = None
    situacao_cadastral: str | None = None
    cnae_fiscal_descricao: str | None = None
    cnae_fiscal: str | None = None
    municipio: str | None = None
    uf: str | None = None
    porte: str | None = None
    natureza_juridica: str | None = None
    capital_social: float | None = None
    data_abertura: str | None = None
    data_situacao_cadastral: str | None = None
    cep: str | None = None
    ddd_telefone_1: str | None = None
    email: str | None = None
    raw: dict[str, Any] | None = None


class BrasilApiClient:
    """Async client for BrasilAPI with caching, retry, and timeout."""

    CACHE_PREFIX = "cnpj"
    CACHE_TTL = 86400  # 24 hours

    def __init__(
        self,
        base_url: str = BRASIL_API_BASE,
        timeout: float = 10.0,
        max_retries: int = 3,
        enable_cache: bool = True,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._enable_cache = enable_cache
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={"User-Agent": "PaySentinelIQ/1.0"},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Public API ──

    async def get_cnpj(self, cnpj: str) -> BrasilApiCompany | None:
        """Fetch company data from BrasilAPI by CNPJ.

        Returns None if CNPJ is not found (404).
        Raises BrasilApiError on server errors or network issues.
        """
        cnpj = self.sanitize_cnpj(cnpj)
        if not cnpj:
            raise BrasilApiError(f"Invalid CNPJ format after sanitization")

        # Check cache
        cache_key = f"{self.CACHE_PREFIX}:{cnpj}"
        if self._enable_cache:
            cached = await RedisCache.get(cache_key)
            if cached:
                logger.debug("BrasilAPI cache hit for %s", cnpj)
                return BrasilApiCompany(**cached) if isinstance(cached, dict) else None

        # Fetch from API with retry
        result = await self._fetch_with_retry(cnpj)

        # Cache result
        if self._enable_cache and result:
            await RedisCache.set(cache_key, result.__dict__, ttl=self.CACHE_TTL)

        return result

    async def health_check(self) -> bool:
        """Check if BrasilAPI is reachable."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self._base_url}/status")
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def sanitize_cnpj(cnpj: str) -> str:
        """Remove non-digit characters from CNPJ string."""
        if not cnpj:
            return ""
        return re.sub(r"[^\d]", "", cnpj)[:14]

    # ── Private ──

    async def _fetch_with_retry(self, cnpj: str) -> BrasilApiCompany | None:
        """Fetch CNPJ from BrasilAPI with exponential backoff retry."""
        last_error = None
        url = f"{self._base_url}/cnpj/v1/{cnpj}"

        for attempt in range(self._max_retries + 1):
            try:
                client = await self._get_client()
                resp = await client.get(url)

                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_response(data)

                if resp.status_code == 404:
                    return None  # CNPJ not found — not an error

                if resp.status_code >= 500:
                    raise BrasilApiError(
                        f"BrasilAPI server error: {resp.status_code}",
                        status_code=resp.status_code,
                    )

                # 4xx errors (except 404)
                raise BrasilApiError(
                    f"BrasilAPI returned {resp.status_code}: {resp.text[:200]}",
                    status_code=resp.status_code,
                )

            except httpx.TimeoutException as e:
                last_error = BrasilApiError(f"BrasilAPI timeout after {self._timeout}s")
            except httpx.ConnectError as e:
                last_error = BrasilApiError("BrasilAPI connection failed")
            except BrasilApiError:
                raise
            except Exception as e:
                last_error = BrasilApiError(f"BrasilAPI request failed: {e}")

            if attempt < self._max_retries:
                wait = 2 ** attempt
                logger.warning(
                    "BrasilAPI retry %d/%d for %s after %ds",
                    attempt + 1, self._max_retries, cnpj, wait,
                )
                time.sleep(wait)

        raise last_error or BrasilApiError(f"Failed to fetch CNPJ {cnpj} after {self._max_retries} retries")

    def _parse_response(self, data: dict[str, Any]) -> BrasilApiCompany:
        """Parse BrasilAPI JSON response into BrasilApiCompany."""
        return BrasilApiCompany(
            cnpj=data.get("cnpj", ""),
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia"),
            situacao_cadastral=data.get("descricao_situacao_cadastral"),
            cnae_fiscal_descricao=data.get("cnae_fiscal_descricao"),
            cnae_fiscal=str(data.get("cnae_fiscal", "")),
            municipio=data.get("municipio"),
            uf=data.get("uf"),
            porte=data.get("descricao_porte"),
            natureza_juridica=data.get("descricao_natureza_juridica"),
            capital_social=float(data.get("capital_social", 0)) if data.get("capital_social") else None,
            data_abertura=data.get("data_inicio_atividade"),
            data_situacao_cadastral=data.get("data_situacao_cadastral"),
            cep=data.get("cep"),
            ddd_telefone_1=data.get("ddd_telefone_1"),
            email=data.get("email"),
            raw=data,
        )
