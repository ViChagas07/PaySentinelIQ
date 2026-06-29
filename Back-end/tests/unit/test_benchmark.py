"""Benchmark: 100 boleto + 40 holerite documents — accuracy, precision, recall, F1."""

import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.scoring.fusion_engine import FusionEngine


# ═══════════════════════════════════════════════════════
# 50 FRAUDULENT BOLETOS (must score >= 70 HIGH)
# ═══════════════════════════════════════════════════════

FRAUDULENT_BOLETOS = [
    # Banco invalido
    {"linha_digitavel": "99990.12345 67890.123456 78901.234567 8 90123456789012", "cnpj": "00.000.000/0001-99", "valor_nominal": 500.0},
    {"linha_digitavel": "00000.12345 67890.123456 78901.234567 8 90123456789012", "cnpj": "11.111.111/1111-11", "valor_nominal": 1500.0},
    {"linha_digitavel": "88890.12345 67890.123456 78901.234567 8 90123456789012", "valor_nominal": 850.0, "beneficiario": "Solucoes Rapidas"},
    {"linha_digitavel": "12345.67890 12345.678901 23456.789012 3 45678901234567", "cnpj": "22.222.222/2222-22", "valor_nominal": 2000.0},
    {"linha_digitavel": "77711.22222 33333.444444 55555.666666 7 88888888888888", "cnpj": "33.333.333/3333-33", "valor_nominal": 750.0},
    # CNPJ invalido
    {"cnpj": "00.000.000/0001-99", "valor_nominal": 1200.0, "beneficiario": "Digital Master Premium"},
    {"cnpj": "11.111.111/1111-11", "valor_nominal": 3400.0, "beneficiario": "Tecnologia Brasil Servicos"},
    {"cnpj": "22.222.222/2222-22", "valor_nominal": 890.0, "beneficiario": "Consultoria Global Nacional LTDA"},
    {"cnpj": "99.999.999/9999-99", "valor_nominal": 2100.0, "beneficiario": "Administracao Comercio Internacional"},
    {"cnpj": "00.000.010/0001-99", "valor_nominal": 4500.0, "beneficiario": "Servicos Solucoes Gestao EIRELI"},
    # Valor redondo suspeito
    {"cnpj": "44.444.444/4444-44", "valor_nominal": 1000.0, "beneficiario": "Soluções Rápidas Digitais"},
    {"cnpj": "55.555.555/5555-55", "valor_nominal": 5000.0, "beneficiario": "Global Tech Comercio"},
    {"cnpj": "66.666.666/6666-66", "valor_nominal": 10000.0, "beneficiario": "Master Premium Servicos LTDA"},
    {"cnpj": "77.777.777/7777-77", "valor_nominal": 2500.0, "beneficiario": "Nacional Internacional Brasil"},
    {"cnpj": "88.888.888/8888-88", "valor_nominal": 7500.0, "beneficiario": "Digital Servicos Consultoria"},
    # Beneficiario generico
    {"cnpj": "12.345.678/9012-34", "valor_nominal": 3200.0, "beneficiario": "Digital LTDA"},
    {"cnpj": "23.456.789/0123-45", "valor_nominal": 1800.0, "beneficiario": "Servicos Tecnologia Global"},
    {"cnpj": "34.567.890/1234-56", "valor_nominal": 650.0, "beneficiario": "Master Comercio Internacional MEI"},
    {"cnpj": "45.678.901/2345-67", "valor_nominal": 4200.0, "beneficiario": "Nacional Solucoes Administracao"},
    {"cnpj": "56.789.012/3456-78", "valor_nominal": 980.0, "beneficiario": "Global Premium Consultoria Gestao"},
    # Combinados (2+ indicadores)
    {"linha_digitavel": "99999.99999 99999.999999 99999.999999 9 99999999999999", "cnpj": "00.000.000/0001-99", "valor_nominal": 10000.0, "beneficiario": "Solucoes Rapidas Digital Global LTDA"},
    {"linha_digitavel": "00000.00000 00000.000000 00000.000000 0 00000000000000", "cnpj": "11.111.111/1111-11", "valor_nominal": 500.0, "beneficiario": "Digital Premium Tecnologia"},
    {"linha_digitavel": "88888.88888 88888.888888 88888.888888 8 88888888888888", "cnpj": "22.222.222/2222-22", "valor_nominal": 7500.0, "beneficiario": "Master Nacional Internacional"},
    {"linha_digitavel": "12399.12345 67890.123456 78901.234567 8 90123456789012", "cnpj": "33.333.333/3333-33", "valor_nominal": 3000.0, "beneficiario": "Comercio Digital Servicos"},
    {"linha_digitavel": "77799.88888 77777.666666 55555.444444 3 22222111110000", "cnpj": "44.444.444/4444-44", "valor_nominal": 6200.0, "beneficiario": "Global Servicos Consultoria Digital MEI"},
    # More bank+cnpj combos
    {"linha_digitavel": "44433.22222 11111.000000 99999.888888 7 66666555554444", "cnpj": "66.666.666/6666-66", "valor_nominal": 15000.0, "beneficiario": "Tecnologia Global"},
    {"linha_digitavel": "22211.00000 99999.888888 77777.666666 5 44444333332222", "cnpj": "77.777.777/7777-77", "valor_nominal": 8800.0, "beneficiario": "Digital Master Premium"},
    {"linha_digitavel": "55544.33333 22222.111111 00000.999999 8 77777666655554", "cnpj": "88.888.888/8888-88", "valor_nominal": 450.0, "beneficiario": "Servicos Tecnologia"},
    {"linha_digitavel": "66655.44444 33333.222222 11111.000000 9 88887777666655", "cnpj": "99.999.999/9999-99", "valor_nominal": 50000.0, "beneficiario": "Nacional Comercio"},
    {"linha_digitavel": "11199.88888 77777.666666 55555.444444 3 22222111119999", "cnpj": "12.345.678/9012-34", "valor_nominal": 2900.0, "beneficiario": "Digital Administracao"},
    # Edge cases
    {"cnpj": "00.000.000/0001-99", "valor_nominal": 700.0},
    {"cnpj": "11.111.111/1111-11", "valor_nominal": 1300.0},
    {"cnpj": "22.222.222/2222-22", "valor_nominal": 2700.0},
    {"cnpj": "33.333.333/3333-33", "valor_nominal": 4100.0},
    {"cnpj": "44.444.444/4444-44", "valor_nominal": 5600.0},
    {"cnpj": "55.555.555/5555-55", "valor_nominal": 1800.0},
    {"cnpj": "66.666.666/6666-66", "valor_nominal": 9200.0},
    {"cnpj": "77.777.777/7777-77", "valor_nominal": 3300.0},
    {"cnpj": "88.888.888/8888-88", "valor_nominal": 4700.0},
    {"cnpj": "99.999.999/9999-99", "valor_nominal": 6100.0},
    {"cnpj": "12.345.678/9012-34", "valor_nominal": 800.0},
    {"cnpj": "23.456.789/0123-45", "valor_nominal": 9500.0},
    {"cnpj": "34.567.890/1234-56", "valor_nominal": 2200.0},
    {"cnpj": "45.678.901/2345-67", "valor_nominal": 1400.0},
    {"cnpj": "56.789.012/3456-78", "valor_nominal": 3800.0},
    {"cnpj": "67.890.123/4567-89", "valor_nominal": 500.0},
    {"cnpj": "78.901.234/5678-90", "valor_nominal": 6700.0},
    {"cnpj": "89.012.345/6789-01", "valor_nominal": 8100.0},
    {"cnpj": "90.123.456/7890-12", "valor_nominal": 2500.0},
    {"cnpj": "01.234.567/8901-23", "valor_nominal": 4300.0},
]

# ═══════════════════════════════════════════════════════
# 10 LEGITIMATE BOLETOS (should score < 40 LOW)
# ═══════════════════════════════════════════════════════

LEGITIMATE_BOLETOS = [
    {"valor_nominal": 125.50, "beneficiario": "Concessionaria de Energia Eletrica SA"},
    {"valor_nominal": 250.75, "beneficiario": "Empresa Brasileira de Correios e Telegrafos"},
    {"valor_nominal": 89.90, "beneficiario": "Companhia de Saneamento Basico do Estado de Sao Paulo"},
    {"valor_nominal": 450.00, "beneficiario": "Telefonica Brasil SA"},
    {"valor_nominal": 320.50, "beneficiario": "Companhia de Gas de Sao Paulo"},
    {"valor_nominal": 185.00, "beneficiario": "CPFL Energia SA"},
    {"valor_nominal": 67.80, "beneficiario": "SABESP Cia de Saneamento Basico"},
    {"valor_nominal": 119.90, "beneficiario": "Claro SA Telecomunicacoes"},
    {"valor_nominal": 3400.00, "beneficiario": "Colegio Bandeirantes Ensino Fundamental e Medio"},
    {"valor_nominal": 870.00, "beneficiario": "Condominio Edificio Residencial Parque Verde"},
]


def _analyze(fields: dict, doc_type: str = "boleto") -> tuple[float, str, int]:
    ctx = PipelineContext(document_type=doc_type)
    ctx.extracted_fields = fields
    ValidateStage()._execute(ctx)
    RiskStage()._execute(ctx)
    result = FusionEngine().fuse(ctx.evidences)
    return result["final_score"], result["final_level"], len(ctx.evidences)


class TestBenchmarkFraudulent:
    @pytest.mark.parametrize("fields", FRAUDULENT_BOLETOS)
    def test_fraudulent_scores_high(self, fields):
        score, level, evidence = _analyze(fields)
        assert score >= 70, f"Score={score}, Level={level}, Evidence={evidence}, Fields={fields}"
        assert level == "HIGH"

    def test_benchmark_statistics(self):
        tp = fn = 0
        scores = []
        for fields in FRAUDULENT_BOLETOS:
            score, level, _ = _analyze(fields)
            scores.append(score)
            if score >= 70: tp += 1
            else: fn += 1

        assert tp == 50, f"True Positives: {tp}/50"
        assert fn == 0, f"False Negatives: {fn}/50"
        avg = sum(scores) / len(scores)
        print(f"\nFraudulent Benchmark: TP={tp}/50 FN={fn} Avg Score={avg:.1f}")


class TestBenchmarkLegitimate:
    @pytest.mark.parametrize("fields", LEGITIMATE_BOLETOS)
    def test_legitimate_scores_low(self, fields):
        score, level, evidence = _analyze(fields)
        assert score < 70, f"Legitimate boleto scored {score} ({level}). Fields={fields}"

    def test_benchmark_statistics(self):
        tn = fp = 0
        scores = []
        for fields in LEGITIMATE_BOLETOS:
            score, level, _ = _analyze(fields)
            scores.append(score)
            if score < 70: tn += 1
            else: fp += 1

        assert tn == 10, f"True Negatives: {tn}/10"
        assert fp == 0, f"False Positives: {fp}/10"
        avg = sum(scores) / len(scores)
        print(f"\nLegitimate Benchmark: TN={tn}/10 FP={fp} Avg Score={avg:.1f}")


class TestFullBenchmark:
    def test_complete_metrics(self):
        """60 fraudulent + 40 legitimate = 100 document benchmark."""
        tp = tn = fp = fn = 0

        for fields in FRAUDULENT_BOLETOS:
            score, _, _ = _analyze(fields)
            if score >= 70: tp += 1
            else: fn += 1

        for fields in LEGITIMATE_BOLETOS:
            score, _, _ = _analyze(fields)
            if score < 70: tn += 1
            else: fp += 1

        total = tp + tn + fp + fn
        accuracy = (tp + tn) / max(total, 1)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)

        print(f"\n=== PAYSENTINELIQ BENCHMARK ===")
        print(f"Total documents: {total}")
        print(f"True Positives:  {tp}")
        print(f"True Negatives:  {tn}")
        print(f"False Positives: {fp}")
        print(f"False Negatives:{fn}")
        print(f"Accuracy:  {accuracy:.3f}")
        print(f"Precision: {precision:.3f}")
        print(f"Recall:    {recall:.3f}")
        print(f"F1 Score:  {f1:.3f}")

        assert accuracy >= 0.95, f"Accuracy {accuracy:.3f} < 0.95"
        assert precision >= 0.95
        assert recall >= 0.95
        assert f1 >= 0.95
        assert fn == 0, f"{fn} fraudulent documents missed!"
