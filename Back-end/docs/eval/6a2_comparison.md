# 6A.2 — comparação antes/depois no dataset v2

Antes = dataset v2 com extração anterior à 6A.2. Depois = mesmo dataset v2 com as correções cirúrgicas. Números de v1 não entram neste comparativo.

## Acurácia de extração

| Dimensão | Caminho | Antes | Depois |
|---|---|---:|---:|
| geral | A_native | 90.1% | 94.8% |
| test_shift | A_native | 56.9% | 93.5% |
| test_iid | A_native | 93.9% | 95.0% |
| geral | B_ocr_clean | 91.3% | 94.5% |
| test_shift | B_ocr_clean | 50.0% | 92.3% |
| test_iid | B_ocr_clean | 91.0% | 92.4% |
| geral | C_ocr_degraded | 84.3% | 87.4% |
| test_shift | C_ocr_degraded | 44.2% | 86.5% |
| test_iid | C_ocr_degraded | 83.3% | 84.7% |

### Por campo (test_shift)

| Caminho | Campo | Antes | Depois |
|---|---|---:|---:|
| A_native | beneficiario | 0.0% | 0.0% |
| A_native | cnpj | 100.0% | 100.0% |
| A_native | codigo_banco | 95.2% | 95.2% |
| A_native | cpf | 100.0% | 100.0% |
| A_native | data_vencimento | 0.0% | 100.0% |
| A_native | fgts | 0.0% | 100.0% |
| A_native | inss | 29.3% | 100.0% |
| A_native | irrf | 70.7% | 100.0% |
| A_native | linha_digitavel | 100.0% | 100.0% |
| A_native | nome_funcionario | 82.8% | 82.8% |
| A_native | periodo | 82.8% | 100.0% |
| A_native | salario_bruto | 82.8% | 100.0% |
| A_native | salario_liquido | 53.4% | 100.0% |
| A_native | total_descontos | 0.0% | 100.0% |
| A_native | valor_nominal | 0.0% | 100.0% |
| B_ocr_clean | beneficiario | 0.0% | 0.0% |
| B_ocr_clean | cnpj | 100.0% | 100.0% |
| B_ocr_clean | codigo_banco | 100.0% | 100.0% |
| B_ocr_clean | cpf | 100.0% | 100.0% |
| B_ocr_clean | data_vencimento | 0.0% | 100.0% |
| B_ocr_clean | fgts | 0.0% | 100.0% |
| B_ocr_clean | inss | 0.0% | 100.0% |
| B_ocr_clean | irrf | 100.0% | 100.0% |
| B_ocr_clean | linha_digitavel | 100.0% | 100.0% |
| B_ocr_clean | nome_funcionario | 50.0% | 50.0% |
| B_ocr_clean | periodo | 50.0% | 100.0% |
| B_ocr_clean | salario_bruto | 50.0% | 100.0% |
| B_ocr_clean | salario_liquido | 50.0% | 100.0% |
| B_ocr_clean | total_descontos | 0.0% | 100.0% |
| B_ocr_clean | valor_nominal | 0.0% | 100.0% |
| C_ocr_degraded | beneficiario | 0.0% | 0.0% |
| C_ocr_degraded | cnpj | 100.0% | 100.0% |
| C_ocr_degraded | codigo_banco | 50.0% | 50.0% |
| C_ocr_degraded | cpf | 100.0% | 100.0% |
| C_ocr_degraded | data_vencimento | 0.0% | 100.0% |
| C_ocr_degraded | fgts | 0.0% | 100.0% |
| C_ocr_degraded | inss | 0.0% | 100.0% |
| C_ocr_degraded | irrf | 100.0% | 100.0% |
| C_ocr_degraded | linha_digitavel | 50.0% | 50.0% |
| C_ocr_degraded | nome_funcionario | 50.0% | 50.0% |
| C_ocr_degraded | periodo | 50.0% | 100.0% |
| C_ocr_degraded | salario_bruto | 25.0% | 75.0% |
| C_ocr_degraded | salario_liquido | 50.0% | 100.0% |
| C_ocr_degraded | total_descontos | 0.0% | 100.0% |
| C_ocr_degraded | valor_nominal | 0.0% | 100.0% |

## Erros de extração AUSENTE / ERRADO / AMBÍGUO (after, native)

| Causa | Tipo | Campo | Layout | Idioma | Ocorrências |
|---|---|---|---|---|---:|
| AUSENTE | contracheque | nome_funcionario | D | en | 10 |
| ERRADO | boleto | beneficiario | A | es | 34 |
| ERRADO | boleto | beneficiario | A | pt | 75 |
| ERRADO | boleto | beneficiario | B | es | 40 |
| ERRADO | boleto | beneficiario | B | pt | 86 |
| ERRADO | boleto | beneficiario | C | es | 46 |
| ERRADO | boleto | beneficiario | C | pt | 58 |
| ERRADO | boleto | beneficiario | D | en | 10 |
| ERRADO | boleto | beneficiario | D | es | 12 |
| ERRADO | boleto | beneficiario | D | pt | 20 |
| ERRADO | boleto | codigo_banco | A | en | 1 |
| ERRADO | boleto | codigo_banco | A | es | 1 |
| ERRADO | boleto | codigo_banco | A | pt | 6 |
| ERRADO | boleto | codigo_banco | B | en | 1 |
| ERRADO | boleto | codigo_banco | B | es | 1 |
| ERRADO | boleto | codigo_banco | B | pt | 6 |
| ERRADO | boleto | codigo_banco | C | en | 2 |
| ERRADO | boleto | codigo_banco | C | es | 3 |
| ERRADO | boleto | codigo_banco | C | pt | 4 |
| ERRADO | boleto | codigo_banco | D | en | 1 |
| ERRADO | boleto | codigo_banco | D | es | 1 |

## Falsos positivos

| Caminho | Split | Legítimos | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |
|---|---|---:|---:|---:|---:|---:|
| A_native | train | 416 | 0 | 0 | 0 | 0 |
| A_native | val | 100 | 0 | 0 | 0 | 0 |
| A_native | test_iid | 109 | 0 | 0 | 0 | 0 |
| A_native | test_shift | 69 | 0 | 0 | 2 | 0 |
| B_ocr_clean | train | 56 | 0 | 0 | 0 | 0 |
| B_ocr_clean | val | 12 | 0 | 0 | 0 | 0 |
| B_ocr_clean | test_iid | 16 | 0 | 0 | 0 | 0 |
| B_ocr_clean | test_shift | 6 | 0 | 0 | 0 | 0 |
| C_ocr_degraded | train | 56 | 0 | 0 | 3 | 3 |
| C_ocr_degraded | val | 12 | 0 | 0 | 0 | 0 |
| C_ocr_degraded | test_iid | 16 | 0 | 0 | 0 | 0 |
| C_ocr_degraded | test_shift | 6 | 0 | 0 | 0 | 1 |

## Detecção por código em naive/multi

| Caminho | Split | Tipo | Antes | Depois |
|---|---|---|---:|---:|
| A_native | train | B1 | 15/16 | 16/16 |
| A_native | train | B2 | 13/15 | 15/15 |
| A_native | train | B3 | 20/20 | 20/20 |
| A_native | train | B4 | 14/14 | 14/14 |
| A_native | train | B5 | 14/14 | 14/14 |
| A_native | train | B8 | 14/14 | 14/14 |
| A_native | train | P1 | 17/17 | 17/17 |
| A_native | train | P2 | 17/17 | 17/17 |
| A_native | train | P3 | 6/6 | 6/6 |
| A_native | train | P5 | 13/13 | 13/13 |
| A_native | train | P6 | 12/12 | 12/12 |
| A_native | train | P7 | 14/14 | 14/14 |
| A_native | train | P8 | 8/8 | 8/8 |
| A_native | train | P9 | 13/13 | 13/13 |
| A_native | val | B1 | 7/7 | 7/7 |
| A_native | val | B2 | 2/3 | 3/3 |
| A_native | val | B3 | 3/3 | 3/3 |
| A_native | val | B4 | 5/5 | 5/5 |
| A_native | val | B5 | 3/3 | 3/3 |
| A_native | val | B8 | 4/4 | 4/4 |
| A_native | val | P1 | 3/3 | 3/3 |
| A_native | val | P2 | 3/3 | 3/3 |
| A_native | val | P5 | 7/7 | 7/7 |
| A_native | val | P6 | 3/3 | 3/3 |
| A_native | val | P7 | 4/4 | 4/4 |
| A_native | val | P8 | 2/2 | 2/2 |
| A_native | val | P9 | 4/4 | 4/4 |
| A_native | test_iid | B1 | 3/3 | 3/3 |
| A_native | test_iid | B2 | 5/5 | 5/5 |
| A_native | test_iid | B3 | 2/2 | 2/2 |
| A_native | test_iid | B4 | 1/1 | 1/1 |
| A_native | test_iid | B5 | 4/4 | 4/4 |
| A_native | test_iid | B8 | 5/5 | 5/5 |
| A_native | test_iid | P1 | 2/2 | 2/2 |
| A_native | test_iid | P2 | 4/4 | 4/4 |
| A_native | test_iid | P3 | 4/4 | 4/4 |
| A_native | test_iid | P5 | 4/4 | 4/4 |
| A_native | test_iid | P6 | 3/3 | 3/3 |
| A_native | test_iid | P7 | 4/4 | 4/4 |
| A_native | test_iid | P8 | 6/6 | 6/6 |
| A_native | test_iid | P9 | 5/5 | 5/5 |
| A_native | test_shift | B1 | 0/1 | 1/1 |
| A_native | test_shift | B3 | 2/2 | 2/2 |
| A_native | test_shift | B4 | 1/1 | 1/1 |
| A_native | test_shift | B5 | 2/2 | 2/2 |
| A_native | test_shift | P1 | 0/2 | 2/2 |
| A_native | test_shift | P2 | 3/4 | 4/4 |
| A_native | test_shift | P3 | 2/3 | 3/3 |
| A_native | test_shift | P5 | 5/5 | 5/5 |
| A_native | test_shift | P6 | 3/4 | 4/4 |
| A_native | test_shift | P7 | 0/5 | 5/5 |
| A_native | test_shift | P8 | 0/1 | 1/1 |
| A_native | test_shift | P9 | 0/2 | 2/2 |
| B_ocr_clean | train | B4 | 4/4 | 4/4 |
| B_ocr_clean | train | P2 | 2/2 | 2/2 |
| B_ocr_clean | train | P5 | 6/6 | 6/6 |
| B_ocr_clean | train | P6 | 2/2 | 2/2 |
| B_ocr_clean | train | P9 | 2/2 | 2/2 |
| B_ocr_clean | val | P5 | 2/2 | 2/2 |
| B_ocr_clean | test_iid | B1 | 2/2 | 2/2 |
| B_ocr_clean | test_iid | B2 | 2/2 | 2/2 |
| B_ocr_clean | test_iid | P5 | 2/2 | 2/2 |
| B_ocr_clean | test_iid | P9 | 2/2 | 2/2 |
| C_ocr_degraded | train | B4 | 2/4 | 2/4 |
| C_ocr_degraded | train | P2 | 2/2 | 2/2 |
| C_ocr_degraded | train | P5 | 5/6 | 5/6 |
| C_ocr_degraded | train | P6 | 2/2 | 2/2 |
| C_ocr_degraded | train | P9 | 2/2 | 2/2 |
| C_ocr_degraded | val | P5 | 2/2 | 2/2 |
| C_ocr_degraded | test_iid | B1 | 1/2 | 1/2 |
| C_ocr_degraded | test_iid | B2 | 1/2 | 1/2 |
| C_ocr_degraded | test_iid | P5 | 2/2 | 2/2 |
| C_ocr_degraded | test_iid | P9 | 2/2 | 2/2 |

## Detecção por faixa em naive/multi

| Caminho | Split | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |
|---|---|---:|---:|---:|---:|
| A_native | train | 90/162 | 91/162 | 105/162 | 106/162 |
| A_native | val | 24/40 | 25/40 | 30/40 | 31/40 |
| A_native | test_iid | 20/39 | 20/39 | 26/39 | 26/39 |
| A_native | test_shift | 4/27 | 11/27 | 7/27 | 13/27 |
| B_ocr_clean | train | 2/16 | 2/16 | 2/16 | 2/16 |
| B_ocr_clean | val | 0/2 | 0/2 | 0/2 | 0/2 |
| B_ocr_clean | test_iid | 2/4 | 2/4 | 2/4 | 4/4 |
| C_ocr_degraded | train | 2/16 | 2/16 | 2/16 | 3/16 |
| C_ocr_degraded | val | 0/2 | 0/2 | 0/2 | 0/2 |
| C_ocr_degraded | test_iid | 2/4 | 2/4 | 2/4 | 4/4 |

## Especialistas B6 / B7 / P4 (fora da cobertura)

| Caminho | Tipo | Documentos | Evidência esperada presente | Faixa HIGH |
|---|---|---:|---:|---:|
| A_native | B6 | 7 | 0 | 0 |
| A_native | B7 | 12 | 0 | 0 |
| A_native | P4 | 19 | 0 | 0 |
| B_ocr_clean | B6 | 2 | 0 | 0 |
| B_ocr_clean | P4 | 6 | 0 | 0 |
| C_ocr_degraded | B6 | 2 | 0 | 0 |
| C_ocr_degraded | P4 | 6 | 0 | 0 |

## Limitações

- `test_shift` tem 100 documentos e 60 renderizações; os caminhos OCR têm poucas observações por tipo.
- A avaliação OCR ainda não cobre todos os B1-B8/P1-P9; isso é escopo da 6A.3.
- B6/B7/P4 continuam sem sinal interno suficiente e são reportados separadamente.
