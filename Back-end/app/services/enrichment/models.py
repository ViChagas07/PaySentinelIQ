# ============================================================
# PaySentinelIQ — Enrichment Models
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CompanyEnrichment:
    """Enriched company data from BrasilAPI + computed risk signals."""

    # ── BrasilAPI data ──
    cnpj: str
    razao_social: str | None = None
    nome_fantasia: str | None = None
    situacao_cadastral: str | None = None
    cnae: str | None = None
    cnae_descricao: str | None = None
    municipio: str | None = None
    uf: str | None = None
    porte: str | None = None
    natureza_juridica: str | None = None
    capital_social: float | None = None
    data_abertura: str | None = None
    data_situacao_cadastral: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None

    # ── Computed fields ──
    idade_empresa_dias: int | None = None
    idade_empresa_anos: float | None = None
    empresa_ativa: bool = False
    empresa_baixada: bool = False

    # ── Risk signals ──
    risk_signals: list[dict[str, Any]] = field(default_factory=list)

    # ── Metadata ──
    fetched_at: str | None = None
    source: str = "brasilapi"

    @property
    def is_valid(self) -> bool:
        return bool(self.cnpj and self.razao_social)

    def compute_age(self) -> None:
        """Calculate company age from data_abertura."""
        if not self.data_abertura:
            return
        try:
            abertura = datetime.fromisoformat(self.data_abertura.replace("Z", "+00:00"))
            agora = datetime.now(timezone.utc)
            delta = agora - abertura
            self.idade_empresa_dias = delta.days
            self.idade_empresa_anos = round(delta.days / 365.25, 1)
        except (ValueError, TypeError):
            pass

    def compute_status(self) -> None:
        """Determine if company is active or closed."""
        if not self.situacao_cadastral:
            return
        status = self.situacao_cadastral.upper()
        self.empresa_ativa = "ATIVA" in status
        self.empresa_baixada = "BAIXADA" in status

    def to_dict(self) -> dict[str, Any]:
        return {
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "nome_fantasia": self.nome_fantasia,
            "situacao_cadastral": self.situacao_cadastral,
            "cnae": self.cnae,
            "cnae_descricao": self.cnae_descricao,
            "municipio": self.municipio,
            "uf": self.uf,
            "porte": self.porte,
            "natureza_juridica": self.natureza_juridica,
            "capital_social": self.capital_social,
            "data_abertura": self.data_abertura,
            "idade_empresa_dias": self.idade_empresa_dias,
            "idade_empresa_anos": self.idade_empresa_anos,
            "empresa_ativa": self.empresa_ativa,
            "empresa_baixada": self.empresa_baixada,
            "risk_signals": self.risk_signals,
            "fetched_at": self.fetched_at,
            "source": self.source,
        }
