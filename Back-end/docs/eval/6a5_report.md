# 6A.5 — Relatório final do checkpoint 6A

Dataset v2.1. Native = dump completo (1000 documentos). OCR = 6A.3 (112 documentos; 40 legítimos), agregado por documento/path pela melhor variante. N é informado em todas as tabelas.

Os conjuntos são de desenvolvimento/avaliação, não holdout intocado.

## N por caminho

| Caminho | N | Legítimos | Adulterados naive/multi |
|---|---:|---:|---:|
| A_native | 1000 | 694 | 268 |
| B_ocr_clean | 112 | 40 | 66 |
| C_ocr_degraded | 112 | 40 | 66 |

## Acurácia de extração

N = campos comparados; OCR inclui todas as variantes observadas.

| Caminho | Campo | Acertos | N |
|---|---|---:|---:|
| A_native | beneficiario | 23.2% | 496 |
| A_native | cnpj | 100.0% | 1000 |
| A_native | codigo_banco | 94.6% | 496 |
| A_native | cpf | 100.0% | 504 |
| A_native | data_vencimento | 100.0% | 496 |
| A_native | fgts | 100.0% | 504 |
| A_native | inss | 100.0% | 504 |
| A_native | irrf | 100.0% | 504 |
| A_native | linha_digitavel | 100.0% | 496 |
| A_native | nome_funcionario | 98.0% | 504 |
| A_native | periodo | 100.0% | 504 |
| A_native | salario_bruto | 100.0% | 504 |
| A_native | salario_liquido | 100.0% | 504 |
| A_native | total_descontos | 100.0% | 504 |
| A_native | valor_nominal | 100.0% | 496 |
| B_ocr_clean | beneficiario | 16.7% | 84 |
| B_ocr_clean | cnpj | 100.0% | 224 |
| B_ocr_clean | codigo_banco | 85.7% | 84 |
| B_ocr_clean | cpf | 100.0% | 140 |
| B_ocr_clean | data_vencimento | 100.0% | 84 |
| B_ocr_clean | fgts | 100.0% | 140 |
| B_ocr_clean | inss | 100.0% | 140 |
| B_ocr_clean | irrf | 100.0% | 140 |
| B_ocr_clean | linha_digitavel | 91.7% | 84 |
| B_ocr_clean | nome_funcionario | 91.4% | 140 |
| B_ocr_clean | periodo | 100.0% | 140 |
| B_ocr_clean | salario_bruto | 100.0% | 140 |
| B_ocr_clean | salario_liquido | 100.0% | 140 |
| B_ocr_clean | total_descontos | 100.0% | 140 |
| B_ocr_clean | valor_nominal | 100.0% | 84 |
| C_ocr_degraded | beneficiario | 16.7% | 84 |
| C_ocr_degraded | cnpj | 88.8% | 224 |
| C_ocr_degraded | codigo_banco | 67.9% | 84 |
| C_ocr_degraded | cpf | 99.3% | 140 |
| C_ocr_degraded | data_vencimento | 97.6% | 84 |
| C_ocr_degraded | fgts | 100.0% | 140 |
| C_ocr_degraded | inss | 98.6% | 140 |
| C_ocr_degraded | irrf | 100.0% | 140 |
| C_ocr_degraded | linha_digitavel | 44.0% | 84 |
| C_ocr_degraded | nome_funcionario | 91.4% | 140 |
| C_ocr_degraded | periodo | 100.0% | 140 |
| C_ocr_degraded | salario_bruto | 99.3% | 140 |
| C_ocr_degraded | salario_liquido | 97.1% | 140 |
| C_ocr_degraded | total_descontos | 100.0% | 140 |
| C_ocr_degraded | valor_nominal | 98.8% | 84 |

### Por idioma

| Caminho | Dimensão | Acertos | N |
|---|---|---:|---:|
| A_native | en | 98.8% | 2100 |
| A_native | es | 93.6% | 2172 |
| A_native | pt | 93.2% | 3744 |
| B_ocr_clean | en | 94.2% | 412 |
| B_ocr_clean | es | 93.6% | 580 |
| B_ocr_clean | pt | 95.6% | 912 |
| C_ocr_degraded | en | 88.1% | 412 |
| C_ocr_degraded | es | 88.3% | 580 |
| C_ocr_degraded | pt | 91.8% | 912 |

### Por layout

| Caminho | Dimensão | Acertos | N |
|---|---|---:|---:|
| A_native | A | 95.1% | 2394 |
| A_native | B | 94.5% | 2432 |
| A_native | C | 95.2% | 2358 |
| A_native | D | 93.5% | 832 |
| B_ocr_clean | A | 96.1% | 284 |
| B_ocr_clean | B | 94.8% | 288 |
| B_ocr_clean | C | 95.7% | 440 |
| B_ocr_clean | D | 93.7% | 892 |
| C_ocr_degraded | A | 91.9% | 284 |
| C_ocr_degraded | B | 88.9% | 288 |
| C_ocr_degraded | C | 92.0% | 440 |
| C_ocr_degraded | D | 88.6% | 892 |

### Por tipo

| Caminho | Dimensão | Acertos | N |
|---|---|---:|---:|
| A_native | boleto | 86.3% | 2976 |
| A_native | contracheque | 99.8% | 5040 |
| B_ocr_clean | boleto | 82.3% | 504 |
| B_ocr_clean | contracheque | 99.1% | 1400 |
| C_ocr_degraded | boleto | 68.8% | 504 |
| C_ocr_degraded | contracheque | 97.5% | 1400 |

## Detecção por código

| Tipo | Caminho | N | Detectados | Cobertura | Amostra |
|---|---|---:|---:|---:|---|
| B1 | A_native | 27 | 27 | 100.0% | suficiente |
| B1 | B_ocr_clean | 4 | 3 | 75.0% | indicativo |
| B1 | C_ocr_degraded | 4 | 2 | 50.0% | indicativo |
| B2 | A_native | 23 | 23 | 100.0% | suficiente |
| B2 | B_ocr_clean | 5 | 5 | 100.0% | suficiente |
| B2 | C_ocr_degraded | 5 | 3 | 60.0% | suficiente |
| B3 | A_native | 27 | 27 | 100.0% | suficiente |
| B3 | B_ocr_clean | 4 | 4 | 100.0% | indicativo |
| B3 | C_ocr_degraded | 4 | 4 | 100.0% | indicativo |
| B4 | A_native | 21 | 21 | 100.0% | suficiente |
| B4 | B_ocr_clean | 2 | 2 | 100.0% | indicativo |
| B4 | C_ocr_degraded | 2 | 1 | 50.0% | indicativo |
| B5 | A_native | 23 | 23 | 100.0% | suficiente |
| B5 | B_ocr_clean | 6 | 6 | 100.0% | suficiente |
| B5 | C_ocr_degraded | 6 | 6 | 100.0% | suficiente |
| B8 | A_native | 23 | 23 | 100.0% | suficiente |
| B8 | B_ocr_clean | 5 | 5 | 100.0% | suficiente |
| B8 | C_ocr_degraded | 5 | 1 | 20.0% | suficiente |
| P1 | A_native | 24 | 24 | 100.0% | suficiente |
| P1 | B_ocr_clean | 4 | 4 | 100.0% | indicativo |
| P1 | C_ocr_degraded | 4 | 4 | 100.0% | indicativo |
| P2 | A_native | 28 | 28 | 100.0% | suficiente |
| P2 | B_ocr_clean | 8 | 8 | 100.0% | suficiente |
| P2 | C_ocr_degraded | 8 | 8 | 100.0% | suficiente |
| P3 | A_native | 13 | 13 | 100.0% | suficiente |
| P3 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P3 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P5 | A_native | 29 | 29 | 100.0% | suficiente |
| P5 | B_ocr_clean | 9 | 9 | 100.0% | suficiente |
| P5 | C_ocr_degraded | 9 | 9 | 100.0% | suficiente |
| P6 | A_native | 22 | 22 | 100.0% | suficiente |
| P6 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P6 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P7 | A_native | 27 | 27 | 100.0% | suficiente |
| P7 | B_ocr_clean | 9 | 9 | 100.0% | suficiente |
| P7 | C_ocr_degraded | 9 | 9 | 100.0% | suficiente |
| P8 | A_native | 17 | 17 | 100.0% | suficiente |
| P8 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P8 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P9 | A_native | 24 | 24 | 100.0% | suficiente |
| P9 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P9 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |

## Recall por faixa (naive e multi)

| Caminho | Classe | N | >=70 | >=40 |
|---|---|---:|---:|---:|
| A_native | naive+multi | 268 | 147 | 176 |
| A_native | multi | 60 | 40 | 58 |
| B_ocr_clean | naive+multi | 66 | 3 | 14 |
| B_ocr_clean | multi | 18 | 2 | 8 |
| C_ocr_degraded | naive+multi | 66 | 4 | 21 |
| C_ocr_degraded | multi | 18 | 3 | 9 |

## Falsos positivos

| Caminho | Legítimos | >=70 | >=40 |
|---|---:|---:|---:|
| A_native | 694 | 0 | 0 |
| B_ocr_clean | 40 | 0 | 1 |
| C_ocr_degraded | 40 | 0 | 2 |

## Especialistas B6 / B7 / P4

| Tipo | Caminho | N | Código esperado |
|---|---|---:|---:|
| B6 | A_native | 7 | 0 |
| B6 | B_ocr_clean | 1 | 0 |
| B6 | C_ocr_degraded | 1 | 0 |
| B7 | A_native | 12 | 0 |
| B7 | B_ocr_clean | 2 | 0 |
| B7 | C_ocr_degraded | 2 | 0 |
| P4 | A_native | 19 | 0 |
| P4 | B_ocr_clean | 3 | 0 |
| P4 | C_ocr_degraded | 3 | 0 |

## B8 / P9 — aritmética vs. sinal forense

| Tipo | Caminho | N | Código aritmético | Sinal forense |
|---|---|---:|---:|---:|
| B8 | A_native | 23 | 23 | 5 |
| B8 | B_ocr_clean | 5 | 5 | 0 |
| B8 | C_ocr_degraded | 5 | 1 | 0 |
| P9 | A_native | 24 | 24 | 6 |
| P9 | B_ocr_clean | 7 | 7 | 0 |
| P9 | C_ocr_degraded | 7 | 7 | 0 |

Sinal forense = `creator`/`producer` diferentes do gerador padrão no PDF nativo. OCR rasteriza o PDF e remove o metadado; ausência não prova autenticidade.

## Políticas shadow V0 / V2 / V4 / V5

| Variante | Caminho | N | FP >=70 | FP >=40 | Recall naive >=40 | Recall naive >=70 | Recall multi >=40 | Recall multi >=70 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| V0 | A_native | 1000 | 0 | 0 | 176 | 147 | 58 | 40 |
| V0 | B_ocr_clean | 112 | 0 | 1 | 14 | 3 | 8 | 2 |
| V0 | C_ocr_degraded | 112 | 0 | 2 | 21 | 4 | 9 | 3 |
| V2 | A_native | 1000 | 0 | 0 | 249 | 157 | 60 | 50 |
| V2 | B_ocr_clean | 112 | 1 | 5 | 36 | 9 | 9 | 5 |
| V2 | C_ocr_degraded | 112 | 1 | 18 | 39 | 12 | 10 | 6 |
| V4 | A_native | 1000 | 0 | 0 | 249 | 157 | 60 | 50 |
| V4 | B_ocr_clean | 112 | 0 | 2 | 24 | 7 | 9 | 4 |
| V4 | C_ocr_degraded | 112 | 0 | 8 | 26 | 10 | 10 | 5 |

### V5 — decisão e revisão

| Caminho | N | HIGH | MEDIUM | LOW | needs_review | Dados insuficientes | FP MEDIUM+ | Recall naive MEDIUM+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A_native | 1000 | 154 | 95 | 751 | 0 | 0 | 0 | 249 |
| B_ocr_clean | 112 | 1 | 40 | 71 | 104 | 6 | 5 | 36 |
| C_ocr_degraded | 112 | 1 | 60 | 51 | 104 | 34 | 18 | 39 |

## Artefatos e reprodutibilidade

- Manifestos pequenos versionados: `docs/eval/manifests/v1.json`, `v2.json`, `v2.1.json` e `6a3_sample.json`.
- Datasets grandes permanecem fora do Git (`data/synthetic/v1`, `v2`, `v2.1`).
- Dumps: `data/synthetic/v2.1/eval/evidence_dump.jsonl` e `data/synthetic/v2.1/eval_ocr/evidence_dump_6a3.jsonl`.
- Commits de geração/avaliação estão nos manifestos.

## Trade-offs e limitações

- O aumento de extração veio de aliases de layout D e datas; o beneficiário continua sem correção dedicada.
- OCR degradado perde B8 e parte de B1/B2/B4; a aritmética ainda detecta P9, mas o sinal forense de metadados desaparece na rasterização.
- V4 e V5 são apenas simulações; nenhuma política foi ativada.
- need_review é alto em OCR porque a amostra é pequena e a qualidade/ausência de campos impede conclusão segura.
- B6/B7/P4 continuam fora da cobertura e são apresentados separados.
- N por tipo é pequeno em várias células; a coluna Amostra marca indicativo quando N < 5.
