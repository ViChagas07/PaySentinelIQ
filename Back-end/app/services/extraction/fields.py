from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.services.extraction.language import LanguageGuess


class ExtractedValue(BaseModel):
    value: Decimal | date | str
    raw: str
    line_no: int = Field(ge=1)
    method: Literal["label_same_line", "label_next_line", "regex"]
    confidence: float = Field(ge=0.0, le=1.0)


class CanonicalFields(BaseModel):
    language: LanguageGuess
    warnings: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)

    beneficiario: ExtractedValue | None = None
    pagador: ExtractedValue | None = None
    data_vencimento: ExtractedValue | None = None
    valor_nominal: ExtractedValue | None = None
    valor_cobrado: ExtractedValue | None = None
    nosso_numero: ExtractedValue | None = None
    numero_documento: ExtractedValue | None = None
    data_documento: ExtractedValue | None = None
    local_pagamento: ExtractedValue | None = None
    carteira: ExtractedValue | None = None
    agencia_codigo_beneficiario: ExtractedValue | None = None
    multa: ExtractedValue | None = None
    juros: ExtractedValue | None = None

    razao_social: ExtractedValue | None = None
    nome_funcionario: ExtractedValue | None = None
    cargo: ExtractedValue | None = None
    cbo: ExtractedValue | None = None
    periodo: ExtractedValue | None = None
    data_admissao: ExtractedValue | None = None
    salario_base: ExtractedValue | None = None
    salario_bruto: ExtractedValue | None = None
    total_descontos: ExtractedValue | None = None
    salario_liquido: ExtractedValue | None = None
    inss: ExtractedValue | None = None
    irrf: ExtractedValue | None = None
    fgts: ExtractedValue | None = None
    base_inss: ExtractedValue | None = None
    base_irrf: ExtractedValue | None = None
    base_fgts: ExtractedValue | None = None
    dependentes: ExtractedValue | None = None

    cnpj: ExtractedValue | None = None
    cpf: ExtractedValue | None = None
    linha_digitavel: ExtractedValue | None = None
    codigo_barras: ExtractedValue | None = None
    codigo_banco: ExtractedValue | None = None
