#!/usr/bin/env python3
"""
PaySentinelIQ — Knowledge Base Generator v2.0
Generates all RAG knowledge PDFs + metadata for AI antifraud agents.

Usage:
    python generate_knowledge.py              # Generate all
    python generate_knowledge.py --only febraban   # Single category
    python generate_knowledge.py --only bacen --only fraud_patterns
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# ── PDF generation dependencies ──
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ═══════════════════════════════════════════════════════════════
# Knowledge Document Contract
# ═══════════════════════════════════════════════════════════════

@dataclass
class KnowledgeDocument:
    title: str
    filename: str
    version: str
    authority: str
    category: str
    weight: float
    description: str
    output_dir: str
    pages: int = 0
    sha256: str = ""
    file_size: int = 0
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Color Palette & Styles (shared helpers)
# ═══════════════════════════════════════════════════════════════

BLUE_DARK   = HexColor("#0D1B2A")
BLUE_MED    = HexColor("#1B3A5C")
BLUE_LIGHT  = HexColor("#2563EB")
GREEN       = HexColor("#16A34A")
RED         = HexColor("#DC2626")
AMBER       = HexColor("#D97706")
GRAY_LIGHT  = HexColor("#F1F5F9")
GRAY_BORDER = HexColor("#CBD5E1")
WHITE       = HexColor("#FFFFFF")
TEXT_DARK   = HexColor("#0F172A")
TEXT_GRAY   = HexColor("#475569")

W, H = A4

def _make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", fontSize=26, textColor=WHITE,
            fontName="Helvetica-Bold", spaceAfter=6, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontSize=13, textColor=HexColor("#93C5FD"),
            fontName="Helvetica", spaceAfter=4, alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", fontSize=16, textColor=BLUE_LIGHT,
            fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontSize=13, textColor=BLUE_MED,
            fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "h3": ParagraphStyle("h3", fontSize=11, textColor=TEXT_DARK,
            fontName="Helvetica-Bold", spaceBefore=7, spaceAfter=3),
        "body": ParagraphStyle("body", fontSize=9.5, textColor=TEXT_DARK,
            fontName="Helvetica", spaceAfter=5, leading=14, alignment=TA_JUSTIFY),
        "body_small": ParagraphStyle("body_small", fontSize=8.5, textColor=TEXT_GRAY,
            fontName="Helvetica", spaceAfter=4, leading=12),
        "bullet": ParagraphStyle("bullet", fontSize=9.5, textColor=TEXT_DARK,
            fontName="Helvetica", spaceAfter=3, leading=13, leftIndent=14, bulletIndent=4),
        "code": ParagraphStyle("code", fontSize=8.5, textColor=HexColor("#1E293B"),
            fontName="Courier", spaceAfter=4, leading=12, leftIndent=10,
            backColor=GRAY_LIGHT, borderPad=6),
        "alert": ParagraphStyle("alert", fontSize=9, textColor=HexColor("#7C2D12"),
            fontName="Helvetica-Bold", spaceAfter=3, leading=13, leftIndent=10),
    }

STYLES = _make_styles()

# ── PDF builder helpers ──

def _header(title, subtitle, category, color=BLUE_DARK):
    data = [[Paragraph(f'<font size="9" color="#93C5FD">{category}</font>', STYLES["subtitle"]),
             Paragraph(title, STYLES["title"]),
             Paragraph(subtitle, STYLES["subtitle"])]]
    t = Table(data, colWidths=[W - 80*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), color),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 18),
        ("BOTTOMPADDING", (0,0), (-1,-1), 18),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    return t

def _hr():
    return HRFlowable(width="100%", thickness=1, color=BLUE_LIGHT, spaceAfter=6, spaceBefore=6)

def _box(items, bg=GRAY_LIGHT, border=GRAY_BORDER):
    t = Table([[c] for c in items], colWidths=[W - 80*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LINEABOVE", (0,0), (-1,0), 1, border),
        ("LINEBELOW", (0,-1), (-1,-1), 1, border),
        ("LINEBEFORE", (0,0), (0,-1), 3, BLUE_LIGHT),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    return t

def _alert(text, level="warning"):
    colors = {
        "warning": (HexColor("#FEF3C7"), HexColor("#D97706"), HexColor("#92400E")),
        "danger":  (HexColor("#FEE2E2"), HexColor("#DC2626"), HexColor("#7F1D1D")),
        "info":    (HexColor("#DBEAFE"), HexColor("#2563EB"), HexColor("#1E3A5F")),
        "success": (HexColor("#DCFCE7"), HexColor("#16A34A"), HexColor("#14532D")),
    }
    bg, bc, tc = colors.get(level, colors["info"])
    ps = ParagraphStyle("ab_tmp", fontSize=9, textColor=tc, fontName="Helvetica", leading=13, leftIndent=8, rightIndent=8)
    t = Table([[Paragraph(text, ps)]], colWidths=[W - 80*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LINEABOVE", (0,0), (-1,0), 2, bc),
        ("LINEBELOW", (0,-1), (-1,-1), 1, bc),
        ("LINEBEFORE", (0,0), (0,-1), 4, bc),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
    ]))
    return t

def _table(headers, rows, widths=None):
    if widths is None:
        widths = [(W - 80*mm) / len(headers)] * len(headers)
    hdr = [Paragraph(f"<b>{h}</b>", ParagraphStyle("th", fontSize=8.5, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_CENTER)) for h in headers]
    data = [hdr]
    for i, row in enumerate(rows):
        data.append([Paragraph(str(c), ParagraphStyle("td", fontSize=8.5, textColor=TEXT_DARK,
            fontName="Helvetica", leading=12)) for c in row])
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE_MED),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [GRAY_LIGHT, WHITE]),
        ("GRID", (0,0), (-1,-1), 0.4, GRAY_BORDER),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def _h1(text): return Paragraph(text, STYLES["h1"])
def _h2(text): return Paragraph(text, STYLES["h2"])
def _h3(text): return Paragraph(text, STYLES["h3"])
def _p(text, style="body"): return Paragraph(text, STYLES[style])
def _bp(text): return Paragraph(f"• {text}", STYLES["bullet"])
def _sp(n=6): return Spacer(1, n)
def _b(text): return f"<b>{text}</b>"


# ═══════════════════════════════════════════════════════════════
# Knowledge Generator
# ═══════════════════════════════════════════════════════════════

class KnowledgeGenerator:
    """Generates all knowledge base PDFs with metadata and validation."""

    def __init__(self, base_dir: str = "knowledge"):
        self.base = Path(base_dir)
        self.docs: list[KnowledgeDocument] = []
        self.errors: list[str] = []
        self.start_time = time.monotonic()

    # ── Public API ──

    def run(self, categories: list[str] | None = None) -> None:
        """Generate knowledge base. If categories is None, generate all."""
        self._ensure_dirs()
        all_cats = {
            "febraban": self.generate_febraban,
            "bacen": self.generate_bacen,
            "fraud_patterns": self.generate_fraud_patterns,
            "layouts": self.generate_layouts,
            "entities": self.generate_entities,
            "historical_cases": self.generate_historical,
            "faq": self.generate_faq,
            "glossary": self.generate_glossary,
        }
        targets = {k: v for k, v in all_cats.items() if categories is None or k in categories}

        for name, func in targets.items():
            print(f"[{name.upper()}] ", end="", flush=True)
            try:
                func()
            except Exception as e:
                self.errors.append(f"[{name}] {e}")
                print(f"ERROR: {e}")

        self._print_report()

    # ── Directory Setup ──

    def _ensure_dirs(self):
        dirs = [
            "pdfs/febraban", "pdfs/bacen", "pdfs/fraud_patterns",
            "pdfs/layouts", "pdfs/entities", "pdfs/historical_cases",
            "pdfs/faq", "pdfs/glossary",
            "metadata", "templates", "assets",
        ]
        for d in dirs:
            (self.base / d).mkdir(parents=True, exist_ok=True)

    # ── PDF Build + Metadata ──

    def _build(self, doc: KnowledgeDocument, story: list) -> None:
        path = self.base / doc.output_dir / doc.filename
        pdf = SimpleDocTemplate(str(path), pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
        pdf.build(story)
        doc.generated_at = datetime.now(timezone.utc).isoformat()
        doc.file_size = path.stat().st_size
        doc.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.docs.append(doc)
        self._write_metadata(doc)
        print(f"OK  ({doc.file_size//1024} KB)")

    def _write_metadata(self, doc: KnowledgeDocument) -> None:
        meta = {
            "title": doc.title, "filename": doc.filename, "version": doc.version,
            "authority": doc.authority, "category": doc.category, "weight": doc.weight,
            "description": doc.description, "generated_at": doc.generated_at,
            "sha256": doc.sha256, "file_size": doc.file_size,
            "output_dir": doc.output_dir,
        }
        meta_path = self.base / "metadata" / f"{Path(doc.filename).stem}.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    # ═══════════════════════════════════════════════════════
    # Category Generators
    # ═══════════════════════════════════════════════════════

    def generate_febraban(self):
        doc = KnowledgeDocument(
            title="Manual FEBRABAN — Boleto Bancário",
            filename="manual_febraban_v1.pdf", version="v1",
            authority="FEBRABAN", category="febraban", weight=1.0,
            description="Referência técnica completa para análise de autenticidade e detecção de fraude em boletos",
            output_dir="pdfs/febraban",
        )
        story = []
        story.append(_header(doc.title, "Referência técnica completa para análise de autenticidade e detecção de fraude",
                            "FEBRABAN • Base de Conhecimento RAG • PaySentinelIQ v1.0"))
        story.append(_sp(10))

        story.append(_h1("1. Estrutura do Boleto Bancário"))
        story.append(_p("O boleto bancário é um documento de cobrança regulamentado pela FEBRABAN e pelo BACEN. Sua estrutura é padronizada — qualquer desvio é indicador de fraude."))
        story.append(_sp(4))
        story.append(_h2("1.1 Campos Obrigatórios"))
        story.append(_table(
            ["Campo", "Descrição", "Prioridade"],
            [
                ["Beneficiário (Cedente)", "Nome e CNPJ/CPF de quem emitiu o boleto", "CRÍTICO"],
                ["Pagador (Sacado)", "Nome e CPF/CNPJ de quem paga", "CRÍTICO"],
                ["Banco Emissor", "Nome e código do banco (3 dígitos)", "CRÍTICO"],
                ["Agência / Conta", "Agência e conta do beneficiário", "ALTO"],
                ["Nosso Número", "Identificador único do título no banco", "CRÍTICO"],
                ["Valor do Documento", "Valor em R$ a ser pago", "CRÍTICO"],
                ["Data de Vencimento", "Data limite de pagamento sem multa", "CRÍTICO"],
                ["Linha Digitável", "47 ou 48 dígitos para digitação manual", "CRÍTICO"],
                ["Código de Barras", "67 barras codificando o boleto completo", "CRÍTICO"],
                ["CNPJ do Beneficiário", "Deve constar impresso no boleto", "ALTO"],
                ["Carteira / Modalidade", "Tipo de cobrança bancária", "MÉDIO"],
                ["Instrução de Cobrança", "Juros, multa, desconto, protesto", "MÉDIO"],
            ], [65*mm, 80*mm, 42*mm]
        ))
        story.append(_sp(8))

        story.append(_h2("1.2 Linha Digitável — Estrutura Completa"))
        story.append(_p("A linha digitável é a representação numérica do código de barras. Deve ter 47 dígitos (boleto comum) ou 48 dígitos (tributos/guias)."))
        story.append(_alert("REGRA CRÍTICA: A linha digitável e o código de barras DEVEM ser matematicamente consistentes. Divergência = fraude confirmada.", "danger"))
        story.append(_sp(6))
        story.append(_h3("Formato (Boleto Bancário — 47 dígitos)"))
        story.append(_p("AAABC.CCCCX DDDDD.DDDDDY EEEEE.EEEEEZ K FFFFFFFFFFFFFFFFF"))
        story.append(_table(
            ["Posição", "Tamanho", "Significado"],
            [
                ["AAA", "3 dígitos", "Código do banco emissor"],
                ["B", "1 dígito", "Código da moeda (9 = BRL)"],
                ["CCCC+X", "5 dígitos", "Campo livre parte 1 + DAC"],
                ["DDDDD+Y", "11 dígitos", "Campo livre parte 2 + DAC"],
                ["EEEEE+Z", "11 dígitos", "Campo livre parte 3 + DAC"],
                ["K", "1 dígito", "DAC geral do código de barras"],
                ["FFFF...F", "14 dígitos", "Fator vencimento (4) + Valor (10)"],
            ], [25*mm, 25*mm, 130*mm]
        ))
        story.append(_sp(8))

        story.append(_h2("1.3 Cálculo do DAC / Dígito Verificador"))
        story.append(_h3("Módulo 10 (campos 1, 2, 3 da linha digitável)"))
        story.append(_p("1. Multiplique cada dígito alternadamente por 2 e 1 (da direita para a esquerda). 2. Some os algarismos dos produtos. 3. Some todos. 4. DAC = (10 - (soma MOD 10)) MOD 10."))
        story.append(_h3("Módulo 11 (DAC geral do código de barras)"))
        story.append(_p("1. Multiplique cada dígito por sequência cíclica 2-9. 2. Some todos. 3. Resto = soma MOD 11. 4. Se resto 0 ou 1 → DAC = 1, senão → DAC = 11 - resto."))
        story.append(_alert("O agente DEVE rejeitar qualquer boleto cujo DAC calculado não corresponda ao DAC impresso.", "danger"))
        story.append(_sp(8))

        story.append(_h2("1.4 Códigos de Banco Válidos (principais)"))
        story.append(_table(
            ["Código", "Banco", "Tipo"],
            [
                ["001", "Banco do Brasil S.A.", "Público Federal"],
                ["033", "Banco Santander (Brasil) S.A.", "Privado"],
                ["104", "Caixa Econômica Federal", "Público Federal"],
                ["237", "Banco Bradesco S.A.", "Privado"],
                ["341", "Banco Itaú S.A.", "Privado"],
                ["077", "Banco Inter S.A.", "Digital"],
                ["260", "Nu Pagamentos S.A. (Nubank)", "Fintech"],
                ["336", "Banco C6 S.A.", "Digital"],
                ["380", "PicPay Serviços S.A.", "Fintech"],
                ["748", "Sicredi", "Cooperativa"],
                ["756", "Sicoob", "Cooperativa"],
            ], [20*mm, 110*mm, 50*mm]
        ))
        story.append(_alert("Qualquer código fora desta lista (ex: 999, 000, 888) = indicador FORTE de boleto falso.", "danger"))
        story.append(_sp(8))

        story.append(_h2("1.5 Regras Oficiais FEBRABAN"))
        for r in [
            "CNPJ/CPF do beneficiário deve ser idêntico ao registrado na CIP.",
            "Banco emissor (3 primeiros dígitos) deve ser autorizado pelo BACEN.",
            "Data de vencimento calculada pelo fator deve igualar data impressa.",
            "Valor no código de barras deve coincidir com valor impresso.",
            "DAC geral e DACs dos campos devem estar matematicamente corretos.",
            "Multa máxima: 2% ao mês. Juros: 1% ao mês (taxa Selic).",
            "Código de barras: exatamente 44 dígitos. Linha: 47 ou 48.",
        ]:
            story.append(_bp(r))
        story.append(_sp(8))

        story.append(PageBreak())
        story.append(_h1("2. Guia de Detecção de Fraude por Campo"))
        story.append(_table(
            ["Campo", "Indicador de Fraude", "Ação"],
            [
                ["Banco", "Código não existe no BACEN (000, 999)", "CRÍTICO — Rejeitar"],
                ["Linha Digitável", "DAC inválido / < 47 dígitos", "CRÍTICO — Rejeitar"],
                ["Código de Barras", "Não corresponde à linha digitável", "CRÍTICO — Rejeitar"],
                ["CNPJ Beneficiário", "CNPJ zerado ou inválido", "ALTO — Investigar"],
                ["Valor", "Diverge entre texto e código de barras", "CRÍTICO — Rejeitar"],
                ["Vencimento", "Fator não corresponde à data", "ALTO — Investigar"],
                ["Multa/Juros", "> 2% ao mês ou > 0,033%/dia", "MÉDIO — Alertar"],
                ["PIX + Boleto", "QR Code PIX com beneficiário diferente", "CRÍTICO — Rejeitar"],
            ], [35*mm, 90*mm, 55*mm]
        ))
        story.append(_alert(f"PESO RAG: {doc.weight}. Em qualquer consulta sobre boleto, este manual é a primeira fonte.", "info"))
        self._build(doc, story)

    def generate_bacen(self):
        for sub in [
            ("normas_pix.pdf", "Normas PIX — BACEN",
             "Manual de validação de QR Code EMV, chaves PIX e fluxos de pagamento instantâneo",
             "BACEN • Circular 4.027/2020", self._story_bacen_pix),
            ("boletos.pdf", "Regulação BACEN — Boletos e Cobrança",
             "Normas de registro, liquidação e cobrança bancária no Brasil",
             "BACEN • Resolução 4.569/2017", self._story_bacen_boletos),
            ("instituicoes.pdf", "Instituições Financeiras Autorizadas — BACEN",
             "Lista de referência para validação de bancos emissores",
             "BACEN • IF.data", self._story_bacen_instituicoes),
        ]:
            fn, title, subtitle, cat, method = sub
            doc = KnowledgeDocument(
                title=title, filename=fn, version="v1",
                authority="BACEN", category="bacen", weight=0.90,
                description=subtitle, output_dir="pdfs/bacen",
            )
            story = method(title, subtitle, cat)
            self._build(doc, story)

    def _story_bacen_pix(self, title, subtitle, cat):
        story = [_header(title, subtitle, cat, BLUE_MED), _sp(10)]
        story.append(_h1("1. O que é o PIX"))
        story.append(_p("Sistema de pagamentos instantâneos do Brasil (Circular 4.027/2020). Liquidação em até 10 segundos, 24/7."))
        story.append(_h2("1.1 Tipos de Chave PIX"))
        story.append(_table(
            ["Tipo", "Formato", "Regras"],
            [["CPF", "000.000.000-00", "11 dígitos. 1 chave por IF."],
             ["CNPJ", "00.000.000/0000-00", "14 dígitos."],
             ["E-mail", "usuario@dominio.com", "Máx 77 caracteres."],
             ["Telefone", "+5511999999999", "Formato E.164 com DDI."],
             ["EVP (aleatória)", "UUID v4", "32 hex + 4 hífens."]],
            [22*mm, 45*mm, 113*mm]
        ))
        story.append(_h2("1.2 Estrutura do QR Code PIX (EMV)"))
        story.append(_table(
            ["ID EMV", "Campo", "Regra"],
            [["00", "Payload Format Indicator", "Sempre '01'"],
             ["26>00", "GUI do arranjo PIX", "Sempre: 'br.gov.bcb.pix'"],
             ["26>01", "Chave PIX", "CPF, CNPJ, e-mail, telefone ou EVP"],
             ["53", "Transaction Currency", "986 = BRL (ISO 4217)"],
             ["54", "Transaction Amount", "Valor em R$ com 2 casas"],
             ["59", "Merchant Name", "Nome do recebedor (máx 25 chars)"],
             ["63", "CRC16", "4 dígitos hex de verificação"]],
            [18*mm, 60*mm, 102*mm]
        ))
        story.append(_h2("1.3 Validação do QR Code PIX"))
        for r in [
            "Campo 26>00 DEVE ser 'br.gov.bcb.pix'. Qualquer outro = QR falso.",
            "CRC16 (campo 63) deve ser válido (CRC-16/CCITT-FALSE).",
            "Campo 53 deve ser '986' (BRL). Campo 58 deve ser 'BR'.",
            "Nome do recebedor (59) deve corresponder ao titular da chave no DICT.",
        ]: story.append(_bp(r))
        story.append(_alert("FRAUDE COMUM — QR Code Falso: golpista substitui QR legítimo. Campo 26>01 aponta para conta do fraudador.", "danger"))
        return story

    def _story_bacen_boletos(self, title, subtitle, cat):
        story = [_header(title, subtitle, cat, BLUE_MED), _sp(10)]
        story.append(_h1("1. Registro Obrigatório de Boletos (desde 2018)"))
        story.append(_p("Desde novembro/2018 (Resolução BACEN 4.569), TODOS os boletos devem ser registrados na CIP."))
        for i in ["Autenticidade: banco valida beneficiário contra CNPJ.", "Pagamento ao beneficiário legítimo.", "Rastreabilidade total.", "Proteção contra golpe do boleto."]:
            story.append(_bp(i))
        story.append(_h2("1.2 Prazos e Regras"))
        story.append(_table(
            ["Situação", "Regra"],
            [["Vencimento", "Obrigatório para boletos de cobrança."],
             ["Atraso", "Aceito até D+60 do vencimento."],
             ["Vencido > 60 dias", "Consultar banco emissor."],
             ["Cancelamento", "Beneficiário pode cancelar via banco."]],
            [55*mm, 125*mm]
        ))
        story.append(_alert("Boletos > R$ 50.000 liquidados no STR mesmo dia. Abaixo, COMPE (D+1).", "info"))
        return story

    def _story_bacen_instituicoes(self, title, subtitle, cat):
        story = [_header(title, subtitle, cat, BLUE_MED), _sp(10)]
        story.append(_h1("1. Como Verificar Banco Legítimo"))
        story.append(_p("BACEN mantém IF.data (bcb.gov.br/estabilidadefinanceira/ifdata). Use API ISPB para validação automatizada."))
        story.append(_table(
            ["Tipo", "Características"],
            [["Banco Múltiplo", "Carteiras comercial, investimento, crédito..."],
             ["Cooperativa", "SICOOB (756), SICREDI (748), UNICRED (136)"],
             ["Inst. Pagamento", "Nubank (260), Inter (77), PicPay (380)"],
             ["INSTITUIÇÃO INEXISTENTE", "Código ISPB fora do IF.data = FRAUDE"]],
            [55*mm, 125*mm]
        ))
        story.append(_alert("REGRA: Banco com código fora da lista BACEN = 100% falso. Ex: 000, 999, 888.", "danger"))
        return story

    def generate_fraud_patterns(self):
        patterns = [
            ("boleto_falso.pdf", "Golpe do Boleto Falso", "Padrões e indicadores de detecção", self._story_boleto_falso),
            ("qr_code_falso.pdf", "Golpe do QR Code Falso (PIX)", "Detecção de QR Codes PIX fraudulentos", self._story_qr_falso),
            ("beneficiario_divergente.pdf", "Beneficiário Divergente", "Nome/CNPJ do pagamento não corresponde", self._story_benef_div),
            ("banco_inexistente.pdf", "Banco Inexistente / Código Inválido", "Código de banco não autorizado pelo BACEN", self._story_banco_inex),
            ("folha_pagamento.pdf", "Fraude em Folha de Pagamento", "Adulteração de folhas e holerites", self._story_folha),
            ("holerite.pdf", "Holerite / Contracheque — Validação", "Estrutura, campos obrigatórios, detecção de adulterações", self._story_holerite),
        ]
        for fn, title, desc, method in patterns:
            doc = KnowledgeDocument(
                title=title, filename=fn, version="v1",
                authority="PaySentinelIQ", category="fraud_patterns", weight=0.95,
                description=desc, output_dir="pdfs/fraud_patterns",
            )
            story = method(title, desc)
            self._build(doc, story)

    def _story_boleto_falso(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Como Funciona"))
        story.append(_p("Criação ou modificação de boleto legítimo para redirecionar pagamento ao fraudador. Prejuízo de bilhões anuais."))
        story.append(_h2("1.1 Modalidades Principais"))
        story.append(_table(
            ["Modalidade", "Descrição", "Risco"],
            [["Substituição Linha Digitável", "Linha alterada. Código de barras pode ser legítimo.", "MUITO ALTO"],
             ["Clonagem", "Cópia com beneficiário e código alterados.", "MUITO ALTO"],
             ["Empresa Falsa", "CNPJ falso/inexistente.", "ALTO"],
             ["Phishing + Boleto", "E-mail/SMS falso com PDF de boleto falso.", "ALTO"]],
            [45*mm, 100*mm, 35*mm]
        ))
        story.append(_h2("1.2 Indicadores de Fraude — Checklist"))
        for sev, text in [
            ("CRÍTICO", "DAC da linha digitável não confere."),
            ("CRÍTICO", "Banco emissor não existe no BACEN."),
            ("CRÍTICO", "CNPJ do beneficiário zerado ou inválido."),
            ("ALTO", "Fator de vencimento incompatível com data impressa."),
            ("ALTO", "CNPJ não encontrado na Receita Federal."),
            ("MÉDIO", "Multa > 2% ao mês."),
            ("MÉDIO", "Beneficiário com nome genérico ('Cobrança', 'Pagamentos')."),
        ]:
            c = "#DC2626" if sev == "CRÍTICO" else "#D97706" if sev == "ALTO" else "#2563EB"
            story.append(_p(f'<font color="{c}"><b>[{sev}]</b></font> {text}'))
        story.append(_alert("Peso RAG: 0.95. Combinar com manual_febraban_v1.pdf. CRÍTICO = bloquear automaticamente.", "info"))
        return story

    def _story_qr_falso(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Modalidades"))
        story.append(_table(
            ["Modalidade", "Descrição", "Risco"],
            [["Sobreposição Física", "Adesivo com QR falso sobre original em comércios.", "CRÍTICO"],
             ["PDF Adulterado", "QR Code substituído no PDF de cobrança.", "CRÍTICO"],
             ["Site Falso", "Site imita banco/empresa e gera QR para fraudador.", "ALTO"],
             ["QR Estático Adulterado", "Chave PIX alterada no QR Copia e Cola.", "CRÍTICO"]],
            [45*mm, 100*mm, 35*mm]
        ))
        story.append(_alert("REGRA DE OURO: Nome no campo 59 do QR DEVE corresponder ao beneficiário esperado. Divergência = NÃO PAGAR.", "danger"))
        return story

    def _story_benef_div(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Tipos de Divergência"))
        story.append(_table(
            ["Tipo", "Descrição", "Risco"],
            [["CNPJ diferente do contrato", "Contrato empresa A, boleto empresa B.", "CRÍTICO"],
             ["CNPJ inexistente", "Não consta na Receita Federal.", "CRÍTICO"],
             ["Empresa recém-criada", "CNPJ < 6 meses recebendo valor alto.", "ALTO"],
             ["Nome genérico", "'Pagamentos Online Ltda' sem histórico.", "ALTO"],
             ["Conta PF em boleto PJ", "Boleto corporativo creditando em CPF.", "CRÍTICO"]],
            [45*mm, 100*mm, 35*mm]
        ))
        return story

    def _story_banco_inex(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Códigos Fraudulentos Mais Comuns"))
        story.append(_table(
            ["Código", "Situação"],
            [["000", "Código nulo — banco inexistente"],
             ["999", "Código genérico — banco inexistente"],
             ["888", "Não existe no BACEN"],
             ["123", "Não existe no BACEN"],
             ["Qualquer 3 dígitos fora da lista", "= FRAUDE CONFIRMADA"]],
            [60*mm, 120*mm]
        ))
        story.append(_alert("REGRA: Rejeitar automaticamente boleto cujo código de banco não conste no IF.data do BACEN.", "danger"))
        return story

    def _story_folha(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Modalidades"))
        story.append(_table(
            ["Modalidade", "Descrição", "Risco"],
            [["Funcionário Fantasma", "Empregado inexistente na folha.", "CRÍTICO"],
             ["Salário Inflado", "Salário real X, folha X+Y.", "CRÍTICO"],
             ["Holerite Falso p/ Crédito", "Holerite adulterado com salário maior.", "ALTO"],
             ["FGTS/INSS não recolhido", "Descontos não repassados ao governo.", "ALTO"]],
            [45*mm, 100*mm, 35*mm]
        ))
        return story

    def _story_holerite(self, title, desc):
        story = [_header(title, desc, "Fraud Patterns • PaySentinelIQ v1.0", HexColor("#7F1D1D")), _sp(10)]
        story.append(_h1("1. Campos Obrigatórios (CLT Art. 464)"))
        story.append(_table(
            ["Campo", "Conteúdo", "Prioridade"],
            [["Empregador", "Razão social, CNPJ", "CRÍTICO"],
             ["Empregado", "Nome, CPF, matrícula, CBO", "CRÍTICO"],
             ["Período", "Mês/ano competência", "CRÍTICO"],
             ["Salário Base", "Valor contratual", "CRÍTICO"],
             ["Descontos", "INSS, IRRF, VT, VR", "CRÍTICO"],
             ["Salário Líquido", "Bruto - descontos (exato)", "CRÍTICO"],
             ["FGTS (informativo)", "8% do bruto (não descontado)", "ALTO"]],
            [50*mm, 90*mm, 40*mm]
        ))
        story.append(_h2("1.1 Fórmulas de Validação"))
        for f in [
            "Salario_Liquido = Salario_Bruto - INSS - IRRF - Descontos + Vantagens",
            "FGTS = Salario_Bruto * 0.08 (informativo, não descontado)",
            "INSS = calculado progressivamente pela tabela vigente",
        ]: story.append(_p(f, "code"))
        story.append(_alert("INSS descontado deve corresponder à tabela progressiva. Divergência = holerite adulterado.", "warning"))
        return story

    def generate_layouts(self):
        bancos = [
            ("boleto_bb.pdf", "001", "Banco do Brasil S.A.", "Carteiras 11, 12, 31, 51. Nosso Número: 10 dígitos."),
            ("boleto_itau.pdf", "341", "Banco Itaú S.A.", "Carteira 109, 119, 121. Nosso Número: até 8 dígitos."),
            ("boleto_caixa.pdf", "104", "Caixa Econômica Federal", "Carteiras RG, SR, CS, CR. Nosso Número: 15 dígitos."),
            ("boleto_bradesco.pdf", "237", "Banco Bradesco S.A.", "Carteiras 02, 04, 09, 26. Nosso Número: 11 dígitos."),
            ("boleto_santander.pdf", "033", "Banco Santander S.A.", "Carteiras 101, 102, 201. IOS: 13 dígitos."),
        ]
        for fn, code, name, details in bancos:
            doc = KnowledgeDocument(
                title=f"Layout Oficial — {name}", filename=fn, version="v1",
                authority="Layouts Bancários", category="layouts", weight=0.90,
                description=f"Código {code} | Estrutura técnica para validação de autenticidade",
                output_dir="pdfs/layouts",
            )
            story = [_header(doc.title, f"Código {code} | Estrutura técnica para validação", "Layouts Bancários • PaySentinelIQ v1.0", GREEN), _sp(10)]
            story.append(_h1(f"1. Identificação do Banco"))
            story.append(_table(
                ["Campo", "Valor", "Observação"],
                [["Código ISPB", code, "3 dígitos na linha digitável"],
                 ["Nome Oficial", name, ""],
                 ["Regulador", "BACEN", ""]],
                [40*mm, 75*mm, 65*mm]
            ))
            story.append(_h1("2. Estrutura Técnica"))
            story.append(_p(details))
            story.append(_h2("2.1 Verificações Prioritárias"))
            for ch in [
                f"3 primeiros dígitos devem ser '{code}'.",
                "DAC geral (posição 5) deve ser válido.",
                "Nosso Número deve ter comprimento padrão do banco.",
                "Layout visual (logotipo, cores, fontes) deve corresponder ao oficial.",
            ]: story.append(_bp(ch))
            story.append(_alert(f"Boleto com código '{code}' mas layout visual diferente = fortemente suspeito.", "warning"))
            self._build(doc, story)

    def generate_entities(self):
        for fn, title, rows, cat_label in [
            ("bancos.pdf", "Bancos e Instituições — Referência", [
                ["001", "Banco do Brasil S.A.", "Público Federal"],
                ["033", "Santander", "Privado (Espanhol)"],
                ["104", "Caixa Econômica Federal", "Público Federal"],
                ["237", "Bradesco", "Privado Nacional"],
                ["341", "Itaú", "Privado Nacional"],
            ], "Bancos"),
            ("fintechs.pdf", "Fintechs e Pagadoras", [
                ["077", "Banco Inter", "Digital"],
                ["260", "Nubank", "Fintech"],
                ["290", "PagSeguro", "Fintech"],
                ["336", "C6 Bank", "Digital"],
                ["380", "PicPay", "Fintech"],
            ], "Fintechs"),
            ("orgaos_publicos.pdf", "Órgãos Públicos — Guias e Tributos", [
                ["DARF", "Impostos federais", "Receita Federal"],
                ["GPS", "INSS autônomo/MEI", "INSS/DATAPREV"],
                ["FGTS", "Recolhimento FGTS", "CAIXA (104)"],
                ["GRU", "Taxas federais", "Tesouro Nacional"],
            ], "Órgãos Públicos"),
        ]:
            doc = KnowledgeDocument(
                title=title, filename=fn, version="v1",
                authority="BACEN/Receita", category="entities", weight=0.80,
                description=f"Lista de referência — {cat_label}",
                output_dir="pdfs/entities",
            )
            story = [_header(doc.title, f"Referência — {cat_label}", "Entidades • PaySentinelIQ v1.0", HexColor("#065F46")), _sp(10)]
            story.append(_h1(f"1. {cat_label}"))
            story.append(_table(["Código/Nome", "Descrição", "Tipo"], rows, [35*mm, 90*mm, 55*mm]))
            self._build(doc, story)

    def generate_historical(self):
        doc = KnowledgeDocument(
            title="Casos Históricos de Fraude — Template", filename="template_historico.pdf", version="v1",
            authority="PaySentinelIQ", category="historical_cases", weight=0.75,
            description="Estrutura para registro de casos analisados e confirmados",
            output_dir="pdfs/historical_cases",
        )
        story = [_header(doc.title, "Estrutura para registro de casos confirmados", "Historical Cases • PaySentinelIQ v1.0", HexColor("#4C1D95")), _sp(10)]
        story.append(_h1("1. Propósito"))
        story.append(_p("Repositório de casos de fraude analisados. O sistema RAG usará como 'memória' para identificar padrões similares."))
        story.append(_table(
            ["Campo", "Descrição"],
            [["case_id", "UUID único"], ["document_type", "BOLETO | HOLERITE | PIX"],
             ["risk_score", "Score 0-100"], ["resultado", "FRAUDE_CONFIRMADA | LEGITIMO"],
             ["evidencias", "Lista de indicadores"], ["valor", "Valor em R$"],
             ["similaridade", "Hash para busca por casos parecidos"]],
            [45*mm, 135*mm]
        ))
        story.append(_alert("Score de similaridade > 0.85 com caso FRAUDE_CONFIRMADA = elevar risco automaticamente.", "info"))
        self._build(doc, story)

    def generate_faq(self):
        doc = KnowledgeDocument(
            title="FAQ Antifraude — Perguntas e Respostas", filename="antifraud_faq.pdf", version="v1",
            authority="PaySentinelIQ", category="faq", weight=0.70,
            description="Base Q&A para agentes de IA e analistas humanos",
            output_dir="pdfs/faq",
        )
        story = [_header(doc.title, "Base Q&A para agentes de IA e analistas", "FAQ • PaySentinelIQ v1.0", HexColor("#1E3A5F")), _sp(10)]
        faqs = [
            ("Multa de 5% ao dia é válida?", "NÃO. Limite: 2% sobre o valor (CDC Art. 52). Juros: 1%/mês. Boleto com 5%/dia é ilegal e suspeito."),
            ("Banco 999 existe?", "NÃO. BACEN nunca autorizou esse código. 100% falso."),
            ("CNPJ zerado (00.000.000/0000-00) é válido?", "NÃO. Não existe na Receita. Boleto inválido ou fraudulento."),
            ("Linha digitável pode ter 46 caracteres?", "NÃO. Exatamente 47 (bancário) ou 48 (tributos). Qualquer outro comprimento = inválido."),
            ("Código de barras e linha podem ter valores diferentes?", "NÃO. São o mesmo boleto. Divergência = adulterado."),
            ("Boleto sem CNPJ do beneficiário?", "NÃO (desde 2018). Todos boletos registrados têm CNPJ/CPF."),
            ("FGTS aparece descontado no holerite?", "NÃO. FGTS é encargo patronal (8%), não descontado do empregado."),
            ("CBO incompatível com cargo é indicador de fraude?", "SIM. CBO deve corresponder ao cargo. Inconsistência = suspeito."),
            ("PIX agendado pode ser cancelado?", "SIM. Pode ser cancelado antes da liquidação."),
        ]
        for i, (q, a) in enumerate(faqs, 1):
            story.append(KeepTogether([_p(f"<b>P{i:02d}: {q}</b>", "h3"), _sp(3), _alert(f"R: {a}", "info"), _sp(8)]))
        self._build(doc, story)

    def generate_glossary(self):
        doc = KnowledgeDocument(
            title="Glossário Antifraude — Termos Técnicos", filename="glossary.pdf", version="v1",
            authority="PaySentinelIQ", category="glossary", weight=0.60,
            description="Dicionário completo de termos bancários e de cobrança",
            output_dir="pdfs/glossary",
        )
        story = [_header(doc.title, "Dicionário de termos para agentes de IA", "Glossário • PaySentinelIQ v1.0", HexColor("#374151")), _sp(10)]
        termos = [
            ("Sacado", "Pessoa/empresa que deve pagar o boleto."),
            ("Cedente / Beneficiário", "Empresa que emitiu e irá receber."),
            ("Carteira", "Código do banco que define o tipo de cobrança."),
            ("Nosso Número", "Identificador único do boleto no banco emissor."),
            ("Fator de Vencimento", "4 dígitos = dias desde 07/10/1997."),
            ("DAC / DV", "Dígito verificador calculado por Módulo 10 ou 11."),
            ("CIP", "Câmara Interbancária de Pagamentos — registra boletos."),
            ("ISPB", "Identificador único de instituição financeira no BACEN."),
            ("QR Code EMV", "QR Code PIX em formato Tag-Length-Value."),
            ("EVP", "Endereço Virtual de Pagamento — chave PIX aleatória."),
        ]
        for termo, definicao in termos:
            story.append(KeepTogether([_p(f"<b>{termo}</b>", "h3"), _p(definicao), _sp(6)]))
        self._build(doc, story)

    # ── Report ──

    def _print_report(self):
        elapsed = time.monotonic() - self.start_time
        print(f"\n=== Knowledge Base Report ===")
        print(f"Total PDFs:        {len(self.docs)}")
        print(f"Total size:        {sum(d.file_size for d in self.docs)//1024} KB")
        print(f"Metadatas created: {len(self.docs)}")
        print(f"Errors:            {len(self.errors)}")
        print(f"Time elapsed:      {elapsed:.1f}s")
        if self.errors:
            for e in self.errors:
                print(f"  ERROR: {e}")
        print(f"\nKnowledge Base successfully generated.")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaySentinelIQ Knowledge Base Generator")
    parser.add_argument("--only", action="append", dest="categories",
                        choices=["febraban", "bacen", "fraud_patterns", "layouts",
                                 "entities", "historical_cases", "faq", "glossary"],
                        help="Generate only specific category (repeatable)")
    parser.add_argument("--base-dir", default="knowledge",
                        help="Base directory for knowledge files (default: knowledge)")
    args = parser.parse_args()

    gen = KnowledgeGenerator(base_dir=args.base_dir)
    gen.run(categories=args.categories)
