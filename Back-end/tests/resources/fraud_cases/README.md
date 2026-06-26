# PaySentinelIQ — Golden Dataset

## Purpose
This directory contains curated test documents used for regression testing
the fraud detection pipeline. Every time the pipeline is modified, these
documents MUST be analyzed and the results compared against expected outcomes.

## Structure

```
fraud_cases/
├── legitimate/
│   ├── boleto_bb_real.pdf        # Real boleto from Banco do Brasil
│   ├── boleto_itau_real.pdf      # Real boleto from Itaú
│   ├── contracheque_real.pdf     # Real payslip
│   └── ...
├── fraudulent/
│   ├── boleto_banco_invalido.pdf # Bank code 999 (not in BACEN)
│   ├── boleto_cnpj_falso.pdf     # CNPJ 00.000.000/0001-99
│   ├── boleto_multa_ilegal.pdf   # Late fee 5% per day
│   ├── boleto_vencido_2anos.pdf  # Due date 2 years ago
│   ├── boleto_todos_indicadores.pdf # All fraud indicators
│   ├── contracheque_inss_falso.pdf  # INSS calculation mismatch
│   └── ...
└── README.md
```

## Expected Outcomes

| Document | Expected Score | Expected Level | Min Indicators |
|----------|---------------|----------------|----------------|
| Legitimate boleto | < 40 | LOW | 0 |
| Banco inválido | ≥ 70 | HIGH | ≥ 1 (CRITICAL) |
| CNPJ falso | ≥ 70 | HIGH | ≥ 1 (CRITICAL) |
| Multa ilegal | ≥ 70 | HIGH | ≥ 1 (CRITICAL) |
| Vencido 2 anos | ≥ 70 | HIGH | ≥ 1 (CRITICAL) |
| Todos indicadores | ≥ 85 | HIGH | ≥ 5 |

## Usage with pytest

```python
import pytest
from pathlib import Path

FRAUD_CASES = Path(__file__).parent

@pytest.mark.parametrize("pdf_path,expected_min_score", [
    (FRAUD_CASES / "fraudulent" / "boleto_banco_invalido.pdf", 70),
    (FRAUD_CASES / "fraudulent" / "boleto_cnpj_falso.pdf", 70),
])
def test_fraudulent_boleto(pdf_path, expected_min_score):
    pdf_bytes = pdf_path.read_bytes()
    context = PipelineContext(file_bytes=pdf_bytes, document_type="boleto")
    result = CanonicalPipeline().execute(context)
    assert result.risk_score >= expected_min_score
```
