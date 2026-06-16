# ============================================================
# PaySentinelIQ — OCR Models (Structured Extraction)
# ============================================================

from dataclasses import dataclass, field


@dataclass
class ExtractedField:
    """A single field extracted from OCR text."""

    name: str
    value: str
    confidence: float = 1.0
    position: tuple[int, int] | None = None  # (line, column) in OCR text


@dataclass
class ExtractionResult:
    """Structured data extracted from OCR text via regex/pattern matching."""

    # ── Entity identification ──
    cnpj: str | None = None
    cpf: str | None = None
    razao_social: str | None = None
    nome_funcionario: str | None = None

    # ── Financial ──
    amounts: list[float] = field(default_factory=list)
    salario_bruto: float | None = None
    salario_liquido: float | None = None
    inss: float | None = None
    irrf: float | None = None
    fgts: float | None = None

    # ── Dates ──
    dates: list[str] = field(default_factory=list)
    data_emissao: str | None = None
    data_vencimento: str | None = None
    periodo: str | None = None

    # ── Document identifiers ──
    numero_documento: str | None = None
    codigo_barras: str | None = None
    linha_digitavel: str | None = None
    chave_acesso: str | None = None

    # ── Bank / Payment ──
    codigo_banco: str | None = None
    agencia: str | None = None
    conta: str | None = None
    pix_key: str | None = None

    # ── Metadata ──
    raw_fields: list[ExtractedField] = field(default_factory=list)
    extraction_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "cnpj": self.cnpj,
            "cpf": self.cpf,
            "razao_social": self.razao_social,
            "nome_funcionario": self.nome_funcionario,
            "amounts": self.amounts,
            "salario_bruto": self.salario_bruto,
            "salario_liquido": self.salario_liquido,
            "inss": self.inss,
            "irrf": self.irrf,
            "fgts": self.fgts,
            "dates": self.dates,
            "data_emissao": self.data_emissao,
            "data_vencimento": self.data_vencimento,
            "periodo": self.periodo,
            "numero_documento": self.numero_documento,
            "codigo_barras": self.codigo_barras,
            "linha_digitavel": self.linha_digitavel,
            "chave_acesso": self.chave_acesso,
            "codigo_banco": self.codigo_banco,
            "agencia": self.agencia,
            "conta": self.conta,
            "pix_key": self.pix_key,
            "extraction_confidence": round(self.extraction_confidence, 4),
        }
