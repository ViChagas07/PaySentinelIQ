# Medição antes da Fase 5B (harness corrigido)

Dataset seed **42**, 1000 documentos, 60 renderizados; native avaliado em 1000.

Todos os documentos são fictícios. Nenhum limiar de aprovação foi usado.

## Precisão de extração por caminho (campos comparados)

| Caminho | Acertos |
|---|---:|
| A_native | 7221/8016 (90.1%) |
| B_ocr_clean | 862/944 (91.3%) |
| C_ocr_degraded | 797/944 (84.4%) |

### Por campo

| Caminho | Campo | Acertos |
|---|---|---:|
| A_native | beneficiario | 115/496 (23.2%) |
| A_native | cnpj | 1000/1000 (100.0%) |
| A_native | codigo_banco | 469/496 (94.6%) |
| A_native | cpf | 504/504 (100.0%) |
| A_native | data_vencimento | 416/496 (83.9%) |
| A_native | fgts | 446/504 (88.5%) |
| A_native | inss | 463/504 (91.9%) |
| A_native | irrf | 487/504 (96.6%) |
| A_native | linha_digitavel | 496/496 (100.0%) |
| A_native | nome_funcionario | 494/504 (98.0%) |
| A_native | periodo | 494/504 (98.0%) |
| A_native | salario_bruto | 494/504 (98.0%) |
| A_native | salario_liquido | 477/504 (94.6%) |
| A_native | total_descontos | 446/504 (88.5%) |
| A_native | valor_nominal | 420/496 (84.7%) |
| B_ocr_clean | beneficiario | 16/64 (25.0%) |
| B_ocr_clean | cnpj | 120/120 (100.0%) |
| B_ocr_clean | codigo_banco | 64/64 (100.0%) |
| B_ocr_clean | cpf | 56/56 (100.0%) |
| B_ocr_clean | data_vencimento | 56/64 (87.5%) |
| B_ocr_clean | fgts | 52/56 (92.9%) |
| B_ocr_clean | inss | 52/56 (92.9%) |
| B_ocr_clean | irrf | 56/56 (100.0%) |
| B_ocr_clean | linha_digitavel | 62/64 (96.9%) |
| B_ocr_clean | nome_funcionario | 54/56 (96.4%) |
| B_ocr_clean | periodo | 54/56 (96.4%) |
| B_ocr_clean | salario_bruto | 54/56 (96.4%) |
| B_ocr_clean | salario_liquido | 54/56 (96.4%) |
| B_ocr_clean | total_descontos | 52/56 (92.9%) |
| B_ocr_clean | valor_nominal | 60/64 (93.8%) |
| C_ocr_degraded | beneficiario | 16/64 (25.0%) |
| C_ocr_degraded | cnpj | 104/120 (86.7%) |
| C_ocr_degraded | codigo_banco | 55/64 (85.9%) |
| C_ocr_degraded | cpf | 55/56 (98.2%) |
| C_ocr_degraded | data_vencimento | 54/64 (84.4%) |
| C_ocr_degraded | fgts | 52/56 (92.9%) |
| C_ocr_degraded | inss | 52/56 (92.9%) |
| C_ocr_degraded | irrf | 55/56 (98.2%) |
| C_ocr_degraded | linha_digitavel | 30/64 (46.9%) |
| C_ocr_degraded | nome_funcionario | 54/56 (96.4%) |
| C_ocr_degraded | periodo | 54/56 (96.4%) |
| C_ocr_degraded | salario_bruto | 53/56 (94.6%) |
| C_ocr_degraded | salario_liquido | 54/56 (96.4%) |
| C_ocr_degraded | total_descontos | 52/56 (92.9%) |
| C_ocr_degraded | valor_nominal | 57/64 (89.1%) |

### Por idioma

| Caminho | Idioma | Acertos |
|---|---|---:|
| A_native | en | 1957/2100 (93.2%) |
| A_native | es | 1908/2172 (87.8%) |
| A_native | pt | 3356/3744 (89.6%) |
| B_ocr_clean | en | 222/248 (89.5%) |
| B_ocr_clean | es | 258/280 (92.1%) |
| B_ocr_clean | pt | 382/416 (91.8%) |
| C_ocr_degraded | en | 198/248 (79.8%) |
| C_ocr_degraded | es | 238/280 (85.0%) |
| C_ocr_degraded | pt | 361/416 (86.8%) |

### Por layout

| Caminho | Layout | Acertos |
|---|---|---:|
| A_native | A | 2243/2394 (93.7%) |
| A_native | B | 2279/2432 (93.7%) |
| A_native | C | 2226/2358 (94.4%) |
| A_native | D | 473/832 (56.9%) |
| B_ocr_clean | A | 159/172 (92.4%) |
| B_ocr_clean | B | 337/364 (92.6%) |
| B_ocr_clean | C | 340/356 (95.5%) |
| B_ocr_clean | D | 26/52 (50.0%) |
| C_ocr_degraded | A | 149/172 (86.6%) |
| C_ocr_degraded | B | 302/364 (83.0%) |
| C_ocr_degraded | C | 323/356 (90.7%) |
| C_ocr_degraded | D | 23/52 (44.2%) |

### Por tipo de documento

| Caminho | Tipo | Acertos |
|---|---|---:|
| A_native | boleto | 2412/2976 (81.0%) |
| A_native | contracheque | 4809/5040 (95.4%) |
| B_ocr_clean | boleto | 322/384 (83.9%) |
| B_ocr_clean | contracheque | 540/560 (96.4%) |
| C_ocr_degraded | boleto | 269/384 (70.1%) |
| C_ocr_degraded | contracheque | 528/560 (94.3%) |

### Dígitos vs texto em OCR

| Caminho | Classe | Acertos |
|---|---|---:|
| A_native | digits | 6612/7016 (94.2%) |
| A_native | text | 609/1000 (60.9%) |
| B_ocr_clean | digits | 792/824 (96.1%) |
| B_ocr_clean | text | 70/120 (58.3%) |
| C_ocr_degraded | digits | 727/824 (88.2%) |
| C_ocr_degraded | text | 70/120 (58.3%) |

## Falsos positivos em legítimos

| Caminho | Legítimos | Score >= 70 | Score >= 40 | Top códigos | Críticos |
|---|---:|---:|---:|---|---|
| A_native | 694 | 450 | 461 | BOLETO_SEVERELY_OVERDUE:238, BOLETO_OVERDUE:188, DOCUMENT_EXPIRED:186, BOLETO_VENCIDO:176, BANCO_INVALIDO:53 | BOLETO_SEVERELY_OVERDUE:238, BANCO_INVALIDO:53 |
| B_ocr_clean | 90 | 64 | 66 | BOLETO_VENCIDO:30, BOLETO_OVERDUE:30, DOCUMENT_EXPIRED:30, BOLETO_SEVERELY_OVERDUE:26, BANCO_INVALIDO:10 | BOLETO_SEVERELY_OVERDUE:26, BANCO_INVALIDO:10, LINHA_DIGITAVEL_FORMATO_INCORRETO:1 |
| C_ocr_degraded | 90 | 73 | 74 | BOLETO_VENCIDO:30, BOLETO_OVERDUE:30, DOCUMENT_EXPIRED:30, LINHA_DIGITAVEL_FORMATO_INCORRETO:29, BOLETO_SEVERELY_OVERDUE:26 | LINHA_DIGITAVEL_FORMATO_INCORRETO:29, BOLETO_SEVERELY_OVERDUE:26, BANCO_INVALIDO:10 |

## Detecção por adulteração

| Caminho | Tipo | Detectado |
|---|---|---:|
| A_native | B1 | 25/27 (92.6%) |
| A_native | B2 | 20/23 (87.0%) |
| A_native | B3 | 27/27 (100.0%) |
| A_native | B4 | 21/21 (100.0%) |
| A_native | B5 | 23/23 (100.0%) |
| A_native | B6 | 0/7 (0.0%) |
| A_native | B7 | 0/12 (0.0%) |
| A_native | B8 | 23/23 (100.0%) |
| A_native | P1 | 22/24 (91.7%) |
| A_native | P2 | 27/28 (96.4%) |
| A_native | P3 | 10/13 (76.9%) |
| A_native | P4 | 0/19 (0.0%) |
| A_native | P5 | 29/29 (100.0%) |
| A_native | P6 | 21/22 (95.5%) |
| A_native | P7 | 22/27 (81.5%) |
| A_native | P8 | 16/17 (94.1%) |
| A_native | P9 | 22/24 (91.7%) |
| B_ocr_clean | B1 | 2/2 (100.0%) |
| B_ocr_clean | B2 | 2/2 (100.0%) |
| B_ocr_clean | B4 | 4/4 (100.0%) |
| B_ocr_clean | B6 | 0/2 (0.0%) |
| B_ocr_clean | P2 | 2/2 (100.0%) |
| B_ocr_clean | P4 | 0/6 (0.0%) |
| B_ocr_clean | P5 | 10/10 (100.0%) |
| B_ocr_clean | P6 | 2/2 (100.0%) |
| B_ocr_clean | P9 | 4/4 (100.0%) |
| C_ocr_degraded | B1 | 1/2 (50.0%) |
| C_ocr_degraded | B2 | 1/2 (50.0%) |
| C_ocr_degraded | B4 | 2/4 (50.0%) |
| C_ocr_degraded | B6 | 0/2 (0.0%) |
| C_ocr_degraded | P2 | 2/2 (100.0%) |
| C_ocr_degraded | P4 | 0/6 (0.0%) |
| C_ocr_degraded | P5 | 9/10 (90.0%) |
| C_ocr_degraded | P6 | 2/2 (100.0%) |
| C_ocr_degraded | P9 | 4/4 (100.0%) |

## Matriz de confusão da banda final

| Caminho | Intenção | LOW | MEDIUM | HIGH |
|---|---|---:|---:|---:|
| A_native | LOW | 16 | 0 | 22 |
| A_native | MEDIUM | 6 | 2 | 13 |
| A_native | HIGH | 26 | 4 | 217 |
| B_ocr_clean | LOW | 2 | 0 | 6 |
| B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| B_ocr_clean | HIGH | 2 | 0 | 20 |
| C_ocr_degraded | LOW | 2 | 0 | 6 |
| C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| C_ocr_degraded | HIGH | 2 | 0 | 20 |

## Expert — cobertura atual (esperado próximo de zero)

| Caminho | Tipo | Detectado |
|---|---|---:|
| A_native | B6 | 0/7 (0.0%) |
| A_native | B7 | 0/12 (0.0%) |
| A_native | P4 | 0/19 (0.0%) |
| B_ocr_clean | B6 | 0/2 (0.0%) |
| B_ocr_clean | P4 | 0/6 (0.0%) |
| C_ocr_degraded | B6 | 0/2 (0.0%) |
| C_ocr_degraded | P4 | 0/6 (0.0%) |

## PDF editado (B8/P9) — sinais forenses

| Caminho | PDFs editados | Sinal forense |
|---|---:|---:|
| A_native | 47 | 0 |
| B_ocr_clean | 4 | 0 |
| C_ocr_degraded | 4 | 0 |

## Tempo médio por documento

| Caminho | Segundos/documento |
|---|---:|
| A_native | 0.023 |
| B_ocr_clean | 1.145 |
| C_ocr_degraded | 1.379 |

## Limitações

- Os documentos legítimos são consistentes por construção: o gerador usa as mesmas fórmulas econômicas do domínio, portanto a taxa de falso positivo mede principalmente o ruído das regras sobre dados sintéticos.
- Os resultados valem para este golden set sintético; não são uma estimativa de produção.
- O caminho A executa a mesma sequência do router: `run_ocr_prelude` com provider nativo-primeiro e `pipeline.execute` em thread; agentes de IA são desligados localmente no script.
- B6/B7/P4 são ataques especializados; a ausência de detecção é esperada.
- B8/P9 não têm detector forense dedicado nesta fase.
