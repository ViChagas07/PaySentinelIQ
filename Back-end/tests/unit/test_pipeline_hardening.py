"""Pipeline Hardening: 40 test cases (20 fraudulent + 20 legitimate)."""

import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.scoring.fusion_engine import FusionEngine


# ═══════════════════════════════════════════════════════
# FRAUDULENT BOLETOS (must score >= 90, HIGH)
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("case_name,fields", [
    ("banco_999_cnpj_falso_multa_5pc", {
        "cnpj": "00.000.000/0001-99",
        "linha_digitavel": "99990.12345 67890.123456 78901.234567 8 90123456789012",
        "valor_nominal": 500.0,
        "beneficiario": "Solucoes Rapidas Digital LTDA",
    }),
    ("banco_999_only", {
        "linha_digitavel": "99990.12345 67890.123456 78901.234567 8 90123456789012",
        "valor_nominal": 1500.0,
    }),
    ("cnpj_zeros", {
        "cnpj": "00.000.000/0001-99",
        "valor_nominal": 850.0,
        "beneficiario": "Empresa Digital Servicos LTDA",
    }),
    ("cnpj_all_nines", {
        "cnpj": "99.999.999/9999-99",
        "valor_nominal": 2000.0,
        "beneficiario": "Consultoria Global Brasil LTDA",
    }),
    ("linha_invalida_round_amount", {
        "linha_digitavel": "12345.67890 12345.678901 23456.789012 3 45678901234567",
        "valor_nominal": 1000.0,
    }),
    ("generic_beneficiary_round", {
        "cnpj": "00.000.010/0001-99",
        "valor_nominal": 5000.0,
        "beneficiario": "Digital Solutions Servicos LTDA",
    }),
    ("banco_999_generic_name", {
        "linha_digitavel": "99900.00000 00000.000000 00000.000000 0 00000000000000",
        "beneficiario": "Tecnologia Global Comercio MEI",
        "valor_nominal": 300.0,
    }),
    ("all_five_indicators", {
        "cnpj": "11.111.111/1111-11",
        "linha_digitavel": "99999.99999 99999.999999 99999.999999 9 99999999999999",
        "valor_nominal": 10000.0,
        "beneficiario": "Master Premium Internacional Servicos",
    }),
    ("banco_nao_registrado_123", {
        "linha_digitavel": "12345.67890 12345.678901 23456.789012 3 45678901234567",
        "cnpj": "12.345.678/9012-34",
        "valor_nominal": 750.0,
    }),
    ("beneficiario_curto_generico", {
        "beneficiario": "Digital LTDA",
        "valor_nominal": 2500.0,
        "linha_digitavel": "88899.00000 11111.222222 33333.444444 5 66666666666666",
    }),
    ("cnpj_10000199_fake", {
        "cnpj": "00.000.010/0001-99",
        "valor_nominal": 600.0,
        "beneficiario": "Administracao Gestao Empresarial EIRELI",
    }),
    ("multa_ilegal_in_text", {
        "cnpj": "00.000.010/0001-99",
        "valor_nominal": 1200.0,
        "beneficiario": "Cobranca Facil Servicos LTDA",
    }),
    ("juros_abusivos_in_text", {
        "cnpj": "55.555.555/5555-55",
        "valor_nominal": 900.0,
        "beneficiario": "Credito Rapido Solucoes Financeiras",
    }),
    ("linha_digitavel_malformada", {
        "linha_digitavel": "99912345678901234567890123456789012345678901234",
        "valor_nominal": 450.0,
    }),
    ("cnpj_sequencial_fake", {
        "cnpj": "12.345.678/9012-34",
        "linha_digitavel": "77711.22222 33333.444444 55555.666666 7 88888888888888",
        "valor_nominal": 3200.0,
    }),
    ("beneficiario_vazio_valor_alto", {
        "valor_nominal": 50000.0,
        "linha_digitavel": "66655.44444 33333.222222 11111.000000 9 88887777666655",
    }),
    ("cnpj_00000010000199", {
        "cnpj": "00.000.010/0001-99",
        "linha_digitavel": "55544.33333 22222.111111 00000.999999 8 77777666655554",
        "valor_nominal": 1800.0,
    }),
    ("tres_criticos_banco_cnpj_linha", {
        "cnpj": "22.222.222/2222-22",
        "linha_digitavel": "44433.22222 11111.000000 99999.888888 7 66666555554444",
        "valor_nominal": 7500.0,
        "beneficiario": "Global Consultoria Digital Servicos Tecnologia",
    }),
    ("banco_777_fora_ispb", {
        "linha_digitavel": "77799.88888 77777.666666 55555.444444 3 22222111110000",
        "cnpj": "33.333.333/3333-33",
        "valor_nominal": 4200.0,
    }),
    ("multiplos_indicadores_estruturais", {
        "cnpj": "44.444.444/4444-44",
        "linha_digitavel": "22211.00000 99999.888888 77777.666666 5 44444333332222",
        "valor_nominal": 8800.0,
        "beneficiario": "Nacional Internacional Comercio Master Premium",
    }),
])
def test_fraudulent_boleto_must_score_high(case_name, fields):
    """All 20 fraudulent boleto variants MUST score >= 70 (HIGH)."""
    ctx = PipelineContext(document_type="boleto")
    ctx.extracted_fields = fields

    vs = ValidateStage()
    vs._execute(ctx)
    rs = RiskStage()
    rs._execute(ctx)

    fusion = FusionEngine()
    result = fusion.fuse(ctx.evidences)

    score = result["final_score"]
    level = result["final_level"]
    evidence_count = len(ctx.evidences)

    assert evidence_count >= 1, (
        f"[{case_name}] Zero evidence produced. Fields: {fields}"
    )
    assert score >= 70, (
        f"[{case_name}] Score {score} too low. Evidence: {[(e.code, e.severity.value) for e in ctx.evidences]}"
    )
    assert level == "HIGH", f"[{case_name}] Level {level}, expected HIGH for score {score}"


# ═══════════════════════════════════════════════════════
# LEGITIMATE DOCUMENTS (should score < 40, LOW)
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("case_name,doc_type,fields", [
    ("boleto_limpo_sem_indicadores", "boleto", {
        "valor_nominal": 125.50,
        "beneficiario": "Concessionaria de Energia Eletrica SA",
    }),
    ("boleto_limpo_valor_normal", "boleto", {
        "valor_nominal": 250.75,
        "beneficiario": "Empresa Brasileira de Correios e Telegrafos",
    }),
    ("boleto_limpo_saneamento", "boleto", {
        "valor_nominal": 89.90,
        "beneficiario": "Companhia de Saneamento Basico do Estado de Sao Paulo",
    }),
    ("boleto_limpo_telecom", "boleto", {
        "valor_nominal": 450.00,
        "beneficiario": "Telefonica Brasil SA",
    }),
    ("boleto_limpo_gas", "boleto", {
        "valor_nominal": 320.50,
        "beneficiario": "Companhia de Gas de Sao Paulo",
    }),
    ("boleto_limpo_cooperativa", "boleto", {
        "valor_nominal": 780.00,
        "beneficiario": "Cooperativa Agropecuaria Regional",
    }),
    ("boleto_limpo_unimed", "boleto", {
        "valor_nominal": 2100.00,
        "beneficiario": "Unimed Cooperativa de Trabalho Medico",
    }),
    ("boleto_limpo_saneamento_rs", "boleto", {
        "valor_nominal": 150.00,
        "beneficiario": "Companhia Riograndense de Saneamento",
    }),
    ("boleto_limpo_seguro", "boleto", {
        "valor_nominal": 550.00,
        "beneficiario": "Porto Seguro Companhia de Seguros Gerais",
    }),
    ("boleto_limpo_plano_saude", "boleto", {
        "valor_nominal": 990.00,
        "beneficiario": "Amil Assistencia Medica Internacional SA",
    }),
    ("boleto_limpo_energia", "boleto", {
        "valor_nominal": 185.00,
        "beneficiario": "CPFL Energia SA",
    }),
    ("boleto_limpo_agua", "boleto", {
        "valor_nominal": 67.80,
        "beneficiario": "SABESP Cia de Saneamento Basico",
    }),
    ("boleto_limpo_escola", "boleto", {
        "valor_nominal": 3400.00,
        "beneficiario": "Colegio Bandeirantes Ensino Fundamental e Medio",
    }),
    ("boleto_limpo_aluguel", "boleto", {
        "valor_nominal": 2500.00,
        "beneficiario": "Administradora de Bens Imoveis Ltda",
    }),
    ("boleto_limpo_condominio", "boleto", {
        "valor_nominal": 870.00,
        "beneficiario": "Condominio Edificio Residencial Parque Verde",
    }),
    ("boleto_limpo_iptu", "boleto", {
        "valor_nominal": 1200.00,
        "beneficiario": "Prefeitura Municipal de Sao Paulo",
    }),
    ("boleto_limpo_ipva", "boleto", {
        "valor_nominal": 3400.00,
        "beneficiario": "Secretaria da Fazenda do Estado de Sao Paulo",
    }),
    ("boleto_limpo_dpvat", "boleto", {
        "valor_nominal": 16.00,
        "beneficiario": "Seguradora Lider dos Consorcios DPVAT SA",
    }),
    ("boleto_limpo_faculdade", "boleto", {
        "valor_nominal": 1890.00,
        "beneficiario": "Universidade Paulista UNIP",
    }),
    ("boleto_limpo_internet", "boleto", {
        "valor_nominal": 119.90,
        "beneficiario": "Claro SA Telecomunicacoes",
    }),
])
def test_legitimate_boleto_scores_low(case_name, doc_type, fields):
    """All 20 legitimate boleto variants MUST score < 70 (not HIGH)."""
    ctx = PipelineContext(document_type=doc_type)
    ctx.extracted_fields = fields

    vs = ValidateStage()
    vs._execute(ctx)
    rs = RiskStage()
    rs._execute(ctx)

    fusion = FusionEngine()
    result = fusion.fuse(ctx.evidences)

    score = result["final_score"]
    level = result["final_level"]

    # Legitimate boletos should NOT be HIGH
    assert score < 70, (
        f"[{case_name}] Legitimate boleto scored {score}/100 ({level}). "
        f"Evidence: {[(e.code, e.severity.value) for e in ctx.evidences]}"
    )
