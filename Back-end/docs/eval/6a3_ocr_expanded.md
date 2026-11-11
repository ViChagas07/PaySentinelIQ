# 6A.3 — Avaliação OCR ampliada

Dataset v2.1; N = **112** documentos (72 adulterados, 40 legítimos).
Suficiente: N >= 5 por tipo/path; caso contrário, indicativo.

## Amostra por tipo

| Tipo | N | Suficiente? |
|---|---:|---|
| B1 | 4 | indicativo |
| B2 | 5 | sim |
| B3 | 4 | indicativo |
| B4 | 2 | indicativo |
| B5 | 6 | sim |
| B6 | 1 | indicativo |
| B7 | 2 | indicativo |
| B8 | 5 | sim |
| P1 | 4 | indicativo |
| P2 | 8 | sim |
| P3 | 7 | sim |
| P4 | 3 | indicativo |
| P5 | 9 | sim |
| P6 | 7 | sim |
| P7 | 9 | sim |
| P8 | 7 | sim |
| P9 | 7 | sim |

## Cobertura por path

| Path | Documentos |
|---|---:|
| A_native | 112 |
| B_ocr_clean | 112 |
| C_ocr_degraded | 112 |

## Detecção por código (naive/multi; especialistas à parte)

| Tipo | Path | N | Detectados | Cobertura | Amostra |
|---|---|---:|---:|---:|---|
| B1 | A_native | 4 | 4 | 100.0% | indicativo |
| B1 | B_ocr_clean | 4 | 3 | 75.0% | indicativo |
| B1 | C_ocr_degraded | 4 | 2 | 50.0% | indicativo |
| B2 | A_native | 5 | 5 | 100.0% | suficiente |
| B2 | B_ocr_clean | 5 | 5 | 100.0% | suficiente |
| B2 | C_ocr_degraded | 5 | 3 | 60.0% | suficiente |
| B3 | A_native | 4 | 4 | 100.0% | indicativo |
| B3 | B_ocr_clean | 4 | 4 | 100.0% | indicativo |
| B3 | C_ocr_degraded | 4 | 4 | 100.0% | indicativo |
| B4 | A_native | 2 | 2 | 100.0% | indicativo |
| B4 | B_ocr_clean | 2 | 2 | 100.0% | indicativo |
| B4 | C_ocr_degraded | 2 | 1 | 50.0% | indicativo |
| B5 | A_native | 6 | 6 | 100.0% | suficiente |
| B5 | B_ocr_clean | 6 | 6 | 100.0% | suficiente |
| B5 | C_ocr_degraded | 6 | 6 | 100.0% | suficiente |
| B8 | A_native | 5 | 5 | 100.0% | suficiente |
| B8 | B_ocr_clean | 5 | 5 | 100.0% | suficiente |
| B8 | C_ocr_degraded | 5 | 1 | 20.0% | suficiente |
| P1 | A_native | 4 | 4 | 100.0% | indicativo |
| P1 | B_ocr_clean | 4 | 4 | 100.0% | indicativo |
| P1 | C_ocr_degraded | 4 | 4 | 100.0% | indicativo |
| P2 | A_native | 8 | 8 | 100.0% | suficiente |
| P2 | B_ocr_clean | 8 | 8 | 100.0% | suficiente |
| P2 | C_ocr_degraded | 8 | 8 | 100.0% | suficiente |
| P3 | A_native | 7 | 7 | 100.0% | suficiente |
| P3 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P3 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P5 | A_native | 9 | 9 | 100.0% | suficiente |
| P5 | B_ocr_clean | 9 | 9 | 100.0% | suficiente |
| P5 | C_ocr_degraded | 9 | 9 | 100.0% | suficiente |
| P6 | A_native | 7 | 7 | 100.0% | suficiente |
| P6 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P6 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P7 | A_native | 9 | 9 | 100.0% | suficiente |
| P7 | B_ocr_clean | 9 | 9 | 100.0% | suficiente |
| P7 | C_ocr_degraded | 9 | 9 | 100.0% | suficiente |
| P8 | A_native | 7 | 7 | 100.0% | suficiente |
| P8 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P8 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |
| P9 | A_native | 7 | 7 | 100.0% | suficiente |
| P9 | B_ocr_clean | 7 | 7 | 100.0% | suficiente |
| P9 | C_ocr_degraded | 7 | 7 | 100.0% | suficiente |

## Especialistas (seção separada)

| Tipo | Path | N | Detectados | Cobertura |
|---|---|---:|---:|---:|
| B6 | A_native | 1 | 0 | 0.0% |
| B6 | B_ocr_clean | 1 | 0 | 0.0% |
| B6 | C_ocr_degraded | 1 | 0 | 0.0% |
| B7 | A_native | 2 | 0 | 0.0% |
| B7 | B_ocr_clean | 2 | 0 | 0.0% |
| B7 | C_ocr_degraded | 2 | 0 | 0.0% |
| P4 | A_native | 3 | 0 | 0.0% |
| P4 | B_ocr_clean | 3 | 0 | 0.0% |
| P4 | C_ocr_degraded | 3 | 0 | 0.0% |

## Falsos positivos em legítimos

| Path | Legítimos | >= 70 | >= 40 |
|---|---:|---:|---:|
| A_native | 40 | 0 | 0 |
| B_ocr_clean | 40 | 0 | 1 |
| C_ocr_degraded | 40 | 0 | 2 |

## B8 / P9 — aritmética vs. sinal forense

| Tipo | Path | N | Código aritmético | Sinal forense |
|---|---|---:|---:|---:|
| B8 | A_native | 5 | 5 | 5 |
| B8 | B_ocr_clean | 5 | 5 | 0 |
| B8 | C_ocr_degraded | 5 | 1 | 0 |
| P9 | A_native | 7 | 7 | 6 |
| P9 | B_ocr_clean | 7 | 7 | 0 |
| P9 | C_ocr_degraded | 7 | 7 | 0 |

Sinal forense = metadados `creator`/`producer` diferentes do gerador padrão no PDF nativo. OCR rasteriza o PDF e remove esse sinal; a ausência não prova autenticidade.

## Limitações

- N por tipo é pequeno em vários casos; a coluna `Amostra` separa suficiente de indicativo.
- A agregação por path usa a melhor variante do documento, não multiplica variantes como observações independentes.
- Nenhuma regra, extração, peso ou threshold foi alterado por esta avaliação.
