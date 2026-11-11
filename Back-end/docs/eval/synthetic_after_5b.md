# Medição depois da Fase 5B — comparação antes/depois

Antes = harness corrigido da 5B.0, sem correções de regra. Depois = mesmas 1000 documentos, seed 42, 60 renderizados, com as mudanças da 5B.2 a 5B.7.

## Falsos positivos por caminho

| Caminho | Legítimos | Antes >= 70 | Antes >= 40 | Depois >= 70 | Depois >= 40 |
|---|---:|---:|---:|---:|---:|
| A_native | 694 | 450 | 461 | 0 | 2 |
| B_ocr_clean | 90 | 64 | 66 | 0 | 0 |
| C_ocr_degraded | 90 | 73 | 74 | 0 | 3 |

## Códigos em documentos legítimos (top 15)

| Caminho | Código | Antes | Depois |
|---|---|---:|---:|
| A_native | DOCUMENT_EXPIRED | 186 | 186 |
| A_native | BOLETO_OVERDUE | 188 | 170 |
| A_native | BOLETO_VENCIDO | 176 | 170 |
| A_native | BOLETO_SEVERELY_OVERDUE | 238 | 0 |
| A_native | BOLETO_DUE_DATE_MISMATCH | 29 | 29 |
| A_native | BANCO_INVALIDO | 53 | 0 |
| A_native | BOLETO_ROUND_AMOUNT | 25 | 25 |
| A_native | ROUND_AMOUNT_SUSPICIOUS | 25 | 25 |
| A_native | VALOR_REDONDO_SUSPEITO | 24 | 24 |
| A_native | PAYSLIP_IRRF_MISMATCH | 11 | 11 |
| B_ocr_clean | BOLETO_OVERDUE | 30 | 30 |
| B_ocr_clean | BOLETO_VENCIDO | 30 | 30 |
| B_ocr_clean | DOCUMENT_EXPIRED | 30 | 30 |
| B_ocr_clean | BOLETO_SEVERELY_OVERDUE | 26 | 0 |
| B_ocr_clean | BANCO_INVALIDO | 10 | 0 |
| B_ocr_clean | BOLETO_ROUND_AMOUNT | 4 | 4 |
| B_ocr_clean | ROUND_AMOUNT_SUSPICIOUS | 4 | 4 |
| B_ocr_clean | VALOR_REDONDO_SUSPEITO | 4 | 4 |
| B_ocr_clean | LINHA_DIGITAVEL_FORMATO_INCORRETO | 1 | 1 |
| C_ocr_degraded | BOLETO_OVERDUE | 30 | 30 |
| C_ocr_degraded | BOLETO_VENCIDO | 30 | 30 |
| C_ocr_degraded | DOCUMENT_EXPIRED | 30 | 30 |
| C_ocr_degraded | LINHA_DIGITAVEL_FORMATO_INCORRETO | 29 | 29 |
| C_ocr_degraded | BOLETO_SEVERELY_OVERDUE | 26 | 0 |
| C_ocr_degraded | BANCO_INVALIDO | 10 | 5 |
| C_ocr_degraded | BOLETO_ROUND_AMOUNT | 4 | 4 |
| C_ocr_degraded | ROUND_AMOUNT_SUSPICIOUS | 4 | 4 |
| C_ocr_degraded | VALOR_REDONDO_SUSPEITO | 4 | 4 |
| C_ocr_degraded | PAYSLIP_INSS_MISMATCH | 1 | 1 |
| C_ocr_degraded | PAYSLIP_IRRF_MISMATCH | 1 | 1 |

## Detecção por tipo de adulteração (B1-B8, P1-P9)

| Caminho | Tipo | Antes | Depois |
|---|---|---:|---:|
| A_native | B1 | 25/27 | 25/27 |
| A_native | B2 | 20/23 | 20/23 |
| A_native | B3 | 27/27 | 27/27 |
| A_native | B4 | 21/21 | 21/21 |
| A_native | B5 | 23/23 | 23/23 |
| A_native | B6 | 0/7 | 0/7 |
| A_native | B7 | 0/12 | 0/12 |
| A_native | B8 | 23/23 | 23/23 |
| A_native | P1 | 22/24 | 22/24 |
| A_native | P2 | 27/28 | 27/28 |
| A_native | P3 | 10/13 | 10/13 |
| A_native | P4 | 0/19 | 0/19 |
| A_native | P5 | 29/29 | 29/29 |
| A_native | P6 | 21/22 | 21/22 |
| A_native | P7 | 22/27 | 22/27 |
| A_native | P8 | 16/17 | 16/17 |
| A_native | P9 | 22/24 | 22/24 |
| B_ocr_clean | B1 | 2/2 | 2/2 |
| B_ocr_clean | B2 | 2/2 | 2/2 |
| B_ocr_clean | B4 | 4/4 | 4/4 |
| B_ocr_clean | B6 | 0/2 | 0/2 |
| B_ocr_clean | P2 | 2/2 | 2/2 |
| B_ocr_clean | P4 | 0/6 | 0/6 |
| B_ocr_clean | P5 | 10/10 | 10/10 |
| B_ocr_clean | P6 | 2/2 | 2/2 |
| B_ocr_clean | P9 | 4/4 | 4/4 |
| C_ocr_degraded | B1 | 1/2 | 1/2 |
| C_ocr_degraded | B2 | 1/2 | 1/2 |
| C_ocr_degraded | B4 | 2/4 | 2/4 |
| C_ocr_degraded | B6 | 0/2 | 0/2 |
| C_ocr_degraded | P2 | 2/2 | 2/2 |
| C_ocr_degraded | P4 | 0/6 | 0/6 |
| C_ocr_degraded | P5 | 9/10 | 9/10 |
| C_ocr_degraded | P6 | 2/2 | 2/2 |
| C_ocr_degraded | P9 | 4/4 | 4/4 |

## Matriz de confusão da faixa

| Caminho | Intenção | Antes L/M/H | Depois L/M/H |
|---|---|---|---|
| A_native | LOW | 16/0/22 | 38/0/0 |
| A_native | MEDIUM | 6/2/13 | 17/3/1 |
| A_native | HIGH | 26/4/217 | 84/26/137 |
| B_ocr_clean | LOW | 2/0/6 | 8/0/0 |
| B_ocr_clean | HIGH | 2/0/20 | 18/0/4 |
| C_ocr_degraded | LOW | 2/0/6 | 8/0/0 |
| C_ocr_degraded | HIGH | 2/0/20 | 18/0/4 |

## Acurácia de extração por caminho

| Caminho | Antes | Depois |
|---|---:|---:|
| A_native | 90.1% | 90.1% |
| B_ocr_clean | 91.3% | 91.3% |
| C_ocr_degraded | 84.4% | 84.4% |

### Acurácia por campo

| Caminho | Campo | Antes | Depois |
|---|---|---:|---:|
| A_native | beneficiario | 23.2% | 23.2% |
| A_native | cnpj | 100.0% | 100.0% |
| A_native | codigo_banco | 94.6% | 94.6% |
| A_native | cpf | 100.0% | 100.0% |
| A_native | data_vencimento | 83.9% | 83.9% |
| A_native | fgts | 88.5% | 88.5% |
| A_native | inss | 91.9% | 91.9% |
| A_native | irrf | 96.6% | 96.6% |
| A_native | linha_digitavel | 100.0% | 100.0% |
| A_native | nome_funcionario | 98.0% | 98.0% |
| A_native | periodo | 98.0% | 98.0% |
| A_native | salario_bruto | 98.0% | 98.0% |
| A_native | salario_liquido | 94.6% | 94.6% |
| A_native | total_descontos | 88.5% | 88.5% |
| A_native | valor_nominal | 84.7% | 84.7% |
| B_ocr_clean | beneficiario | 25.0% | 25.0% |
| B_ocr_clean | cnpj | 100.0% | 100.0% |
| B_ocr_clean | codigo_banco | 100.0% | 100.0% |
| B_ocr_clean | cpf | 100.0% | 100.0% |
| B_ocr_clean | data_vencimento | 87.5% | 87.5% |
| B_ocr_clean | fgts | 92.9% | 92.9% |
| B_ocr_clean | inss | 92.9% | 92.9% |
| B_ocr_clean | irrf | 100.0% | 100.0% |
| B_ocr_clean | linha_digitavel | 96.9% | 96.9% |
| B_ocr_clean | nome_funcionario | 96.4% | 96.4% |
| B_ocr_clean | periodo | 96.4% | 96.4% |
| B_ocr_clean | salario_bruto | 96.4% | 96.4% |
| B_ocr_clean | salario_liquido | 96.4% | 96.4% |
| B_ocr_clean | total_descontos | 92.9% | 92.9% |
| B_ocr_clean | valor_nominal | 93.8% | 93.8% |
| C_ocr_degraded | beneficiario | 25.0% | 25.0% |
| C_ocr_degraded | cnpj | 86.7% | 86.7% |
| C_ocr_degraded | codigo_banco | 85.9% | 85.9% |
| C_ocr_degraded | cpf | 98.2% | 98.2% |
| C_ocr_degraded | data_vencimento | 84.4% | 84.4% |
| C_ocr_degraded | fgts | 92.9% | 92.9% |
| C_ocr_degraded | inss | 92.9% | 92.9% |
| C_ocr_degraded | irrf | 98.2% | 98.2% |
| C_ocr_degraded | linha_digitavel | 46.9% | 46.9% |
| C_ocr_degraded | nome_funcionario | 96.4% | 96.4% |
| C_ocr_degraded | periodo | 96.4% | 96.4% |
| C_ocr_degraded | salario_bruto | 94.6% | 94.6% |
| C_ocr_degraded | salario_liquido | 96.4% | 96.4% |
| C_ocr_degraded | total_descontos | 92.9% | 92.9% |
| C_ocr_degraded | valor_nominal | 89.1% | 89.1% |

## Trade-off do rebaixamento por OCR

Detecção por score (não por presença de código) nos caminhos B e C para os tipos afetados pela mitigação provisória de OCR.

| Caminho | Tipo | Antes >= 70 | Depois >= 70 | Antes >= 40 | Depois >= 40 |
|---|---|---:|---:|---:|---:|
| B_ocr_clean | B1 | 2/2 | 0/2 | 2/2 | 0/2 |
| B_ocr_clean | B2 | 2/2 | 0/2 | 2/2 | 0/2 |
| B_ocr_clean | B4 | 4/4 | 0/4 | 4/4 | 0/4 |
| B_ocr_clean | P1 | 0/0 | 0/0 | 0/0 | 0/0 |
| B_ocr_clean | P2 | 2/2 | 0/2 | 2/2 | 0/2 |
| B_ocr_clean | P5 | 8/10 | 2/10 | 8/10 | 2/10 |
| C_ocr_degraded | B1 | 2/2 | 0/2 | 2/2 | 0/2 |
| C_ocr_degraded | B2 | 2/2 | 0/2 | 2/2 | 0/2 |
| C_ocr_degraded | B4 | 4/4 | 0/4 | 4/4 | 0/4 |
| C_ocr_degraded | P1 | 0/0 | 0/0 | 0/0 | 0/0 |
| C_ocr_degraded | P2 | 2/2 | 0/2 | 2/2 | 0/2 |
| C_ocr_degraded | P5 | 8/10 | 2/10 | 8/10 | 2/10 |

## Taxonomia de erros de extração (depois)

| Causa | Caminho | Campo | Layout | Idioma | Ocorrências |
|---|---|---|---|---|---:|
| AUSENTE | A_native | beneficiario | D | en | 10 |
| AUSENTE | A_native | beneficiario | D | es | 12 |
| AUSENTE | A_native | beneficiario | D | pt | 20 |
| AUSENTE | A_native | data_vencimento | B | en | 8 |
| AUSENTE | A_native | data_vencimento | C | en | 4 |
| AUSENTE | A_native | fgts | D | en | 10 |
| AUSENTE | A_native | fgts | D | es | 17 |
| AUSENTE | A_native | fgts | D | pt | 31 |
| AUSENTE | A_native | inss | D | en | 10 |
| AUSENTE | A_native | inss | D | pt | 31 |
| AUSENTE | A_native | irrf | D | es | 17 |
| AUSENTE | A_native | nome_funcionario | D | en | 10 |
| AUSENTE | A_native | salario_bruto | D | en | 8 |
| AUSENTE | A_native | salario_liquido | D | en | 10 |
| AUSENTE | A_native | salario_liquido | D | es | 17 |
| AUSENTE | A_native | total_descontos | D | en | 10 |
| AUSENTE | A_native | total_descontos | D | es | 17 |
| AUSENTE | A_native | total_descontos | D | pt | 31 |
| AUSENTE | A_native | valor_nominal | A | es | 34 |
| AUSENTE | A_native | valor_nominal | D | en | 10 |
| AUSENTE | A_native | valor_nominal | D | es | 12 |
| AUSENTE | A_native | valor_nominal | D | pt | 20 |
| AUSENTE | B_ocr_clean | beneficiario | D | en | 2 |
| AUSENTE | B_ocr_clean | fgts | D | en | 2 |
| AUSENTE | B_ocr_clean | fgts | D | pt | 2 |
| AUSENTE | B_ocr_clean | inss | D | en | 2 |
| AUSENTE | B_ocr_clean | inss | D | pt | 2 |
| AUSENTE | B_ocr_clean | linha_digitavel | A | pt | 1 |
| AUSENTE | B_ocr_clean | linha_digitavel | B | pt | 1 |
| AUSENTE | B_ocr_clean | nome_funcionario | D | en | 2 |
| AUSENTE | B_ocr_clean | salario_bruto | D | en | 2 |
| AUSENTE | B_ocr_clean | salario_liquido | D | en | 2 |
| AUSENTE | B_ocr_clean | total_descontos | D | en | 2 |
| AUSENTE | B_ocr_clean | total_descontos | D | pt | 2 |
| AUSENTE | B_ocr_clean | valor_nominal | A | es | 2 |
| AUSENTE | B_ocr_clean | valor_nominal | D | en | 2 |
| AUSENTE | C_ocr_degraded | beneficiario | D | en | 2 |
| AUSENTE | C_ocr_degraded | cnpj | A | es | 1 |
| AUSENTE | C_ocr_degraded | cnpj | B | en | 2 |
| AUSENTE | C_ocr_degraded | cnpj | B | es | 3 |
| AUSENTE | C_ocr_degraded | cnpj | B | pt | 3 |
| AUSENTE | C_ocr_degraded | cnpj | C | en | 1 |
| AUSENTE | C_ocr_degraded | cnpj | C | es | 2 |
| AUSENTE | C_ocr_degraded | cnpj | C | pt | 2 |
| AUSENTE | C_ocr_degraded | codigo_banco | A | en | 1 |
| AUSENTE | C_ocr_degraded | codigo_banco | B | en | 6 |
| AUSENTE | C_ocr_degraded | codigo_banco | C | en | 1 |
| AUSENTE | C_ocr_degraded | codigo_banco | D | en | 1 |
| AUSENTE | C_ocr_degraded | cpf | C | en | 1 |
| AUSENTE | C_ocr_degraded | data_vencimento | B | pt | 1 |
| AUSENTE | C_ocr_degraded | fgts | D | en | 2 |
| AUSENTE | C_ocr_degraded | fgts | D | pt | 2 |
| AUSENTE | C_ocr_degraded | inss | D | en | 2 |
| AUSENTE | C_ocr_degraded | inss | D | pt | 2 |
| AUSENTE | C_ocr_degraded | linha_digitavel | A | en | 1 |
| AUSENTE | C_ocr_degraded | linha_digitavel | A | es | 1 |
| AUSENTE | C_ocr_degraded | linha_digitavel | A | pt | 5 |
| AUSENTE | C_ocr_degraded | linha_digitavel | B | en | 6 |
| AUSENTE | C_ocr_degraded | linha_digitavel | B | es | 4 |
| AUSENTE | C_ocr_degraded | linha_digitavel | B | pt | 8 |
| AUSENTE | C_ocr_degraded | linha_digitavel | C | en | 1 |
| AUSENTE | C_ocr_degraded | linha_digitavel | C | es | 5 |
| AUSENTE | C_ocr_degraded | linha_digitavel | C | pt | 2 |
| AUSENTE | C_ocr_degraded | linha_digitavel | D | en | 1 |
| AUSENTE | C_ocr_degraded | nome_funcionario | D | en | 2 |
| AUSENTE | C_ocr_degraded | salario_bruto | D | en | 2 |
| AUSENTE | C_ocr_degraded | salario_liquido | D | en | 2 |
| AUSENTE | C_ocr_degraded | total_descontos | D | en | 2 |
| AUSENTE | C_ocr_degraded | total_descontos | D | pt | 2 |
| AUSENTE | C_ocr_degraded | valor_nominal | A | es | 2 |
| AUSENTE | C_ocr_degraded | valor_nominal | D | en | 2 |
| ERRADO | A_native | beneficiario | A | es | 34 |
| ERRADO | A_native | beneficiario | A | pt | 75 |
| ERRADO | A_native | beneficiario | B | es | 40 |
| ERRADO | A_native | beneficiario | B | pt | 86 |
| ERRADO | A_native | beneficiario | C | es | 46 |
| ERRADO | A_native | beneficiario | C | pt | 58 |
| ERRADO | A_native | codigo_banco | A | en | 1 |
| ERRADO | A_native | codigo_banco | A | es | 1 |
| ERRADO | A_native | codigo_banco | A | pt | 6 |
| ERRADO | A_native | codigo_banco | B | en | 1 |
| ERRADO | A_native | codigo_banco | B | es | 1 |
| ERRADO | A_native | codigo_banco | B | pt | 6 |
| ERRADO | A_native | codigo_banco | C | en | 2 |
| ERRADO | A_native | codigo_banco | C | es | 3 |
| ERRADO | A_native | codigo_banco | C | pt | 4 |
| ERRADO | A_native | codigo_banco | D | en | 1 |
| ERRADO | A_native | codigo_banco | D | es | 1 |
| ERRADO | A_native | data_vencimento | B | en | 11 |
| ERRADO | A_native | data_vencimento | C | en | 15 |
| ERRADO | A_native | data_vencimento | D | en | 10 |
| ERRADO | A_native | data_vencimento | D | es | 12 |
| ERRADO | A_native | data_vencimento | D | pt | 20 |
| ERRADO | A_native | periodo | D | en | 10 |
| ERRADO | A_native | salario_bruto | D | en | 2 |
| ERRADO | B_ocr_clean | beneficiario | A | es | 2 |
| ERRADO | B_ocr_clean | beneficiario | A | pt | 8 |
| ERRADO | B_ocr_clean | beneficiario | B | es | 8 |
| ERRADO | B_ocr_clean | beneficiario | B | pt | 14 |
| ERRADO | B_ocr_clean | beneficiario | C | es | 10 |
| ERRADO | B_ocr_clean | beneficiario | C | pt | 4 |
| ERRADO | B_ocr_clean | data_vencimento | B | en | 4 |
| ERRADO | B_ocr_clean | data_vencimento | C | en | 2 |
| ERRADO | B_ocr_clean | data_vencimento | D | en | 2 |
| ERRADO | B_ocr_clean | periodo | D | en | 2 |
| ERRADO | C_ocr_degraded | beneficiario | A | es | 2 |
| ERRADO | C_ocr_degraded | beneficiario | A | pt | 8 |
| ERRADO | C_ocr_degraded | beneficiario | B | es | 8 |
| ERRADO | C_ocr_degraded | beneficiario | B | pt | 14 |
| ERRADO | C_ocr_degraded | beneficiario | C | es | 10 |
| ERRADO | C_ocr_degraded | beneficiario | C | pt | 4 |
| ERRADO | C_ocr_degraded | cnpj | A | en | 1 |
| ERRADO | C_ocr_degraded | cnpj | B | pt | 1 |
| ERRADO | C_ocr_degraded | data_vencimento | B | en | 4 |
| ERRADO | C_ocr_degraded | data_vencimento | B | es | 1 |
| ERRADO | C_ocr_degraded | data_vencimento | C | en | 2 |
| ERRADO | C_ocr_degraded | data_vencimento | D | en | 2 |
| ERRADO | C_ocr_degraded | irrf | A | en | 1 |
| ERRADO | C_ocr_degraded | periodo | D | en | 2 |
| ERRADO | C_ocr_degraded | salario_bruto | D | pt | 1 |
| ERRADO | C_ocr_degraded | valor_nominal | B | es | 1 |
| ERRADO | C_ocr_degraded | valor_nominal | C | es | 2 |

## Atribuição de falsos positivos (depois)

Relatório completo: `fp_attribution_after.md`. Legítimos com score >= 70 depois: 0.

## Limitações

- Os números valem para o golden set sintético desta máquina, seed 42; não são uma estimativa de produção.
- O caminho A usa a camada nativa via `run_ocr_prelude` com provider nativo-primeiro; B e C usam o serviço de OCR local.
- A mitigação de OCR é provisória e troca recall por menos falsos positivos até existir corroboração por segunda leitura.
- B6/B7/P4 continuam sem detector dedicado nesta fase.
- O gerador ainda carrega artefatos históricos de codificação em alguns rótulos; a taxonomia abaixo mostra onde isso vira campo AUSENTE ou ERRADO.
