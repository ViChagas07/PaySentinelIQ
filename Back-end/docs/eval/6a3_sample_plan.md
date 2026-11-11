# 6A.3 — Plano de amostra (definido antes da execução)

- Dataset: v2.1
- Splits de avaliação: test_iid, test_shift
- Documentos: **112** (72 adulterados, 40 legítimos)
- Legítimos por split: até 20 (ordenados por ID)
- Por split: {'test_iid': 61, 'test_shift': 51}
- Variantes OCR limpas: `scanned_clean`, `image_png`
- Variantes OCR degradadas: `scanned_rot`, `scanned_blur`
- Suficiente para tabela: N >= 5 documentos por tipo/path; abaixo disso é indicativo.

| Tipo | N documentos |
|---|---:|
| B1 | 4 |
| B2 | 5 |
| B3 | 4 |
| B4 | 2 |
| B5 | 6 |
| B6 | 1 |
| B7 | 2 |
| B8 | 5 |
| P1 | 4 |
| P2 | 8 |
| P3 | 7 |
| P4 | 3 |
| P5 | 9 |
| P6 | 7 |
| P7 | 9 |
| P8 | 7 |
| P9 | 7 |

Observação: as variantes de um mesmo documento permanecem no mesmo split. A agregação por path é feita por documento (detecção em qualquer variante do grupo), não por chamada OCR.
