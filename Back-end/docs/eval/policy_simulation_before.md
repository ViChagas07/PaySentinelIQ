# Simulação de política — antes da Fase 5B

Recalcula o score fusionado a partir do `evidence_dump` com a fórmula do FusionEngine: peso da severidade × multiplicador da fonte × confiança, pisos de 1 e 3 críticos, fator 1,2 para 2+ críticos e limite 100.

## Simulação de política (somente leitura)

| Variante | Caminho | Legítimos >= 70 | Legítimos >= 40 | Recall naive >= 40 | Recall naive >= 70 | Recall multi >= 40 | Recall multi >= 70 |
|---|---|---:|---:|---:|---:|---:|---:|
| V0 | A_native | 450/694 (64.8%) | 461/694 (66.4%) | 236/268 (88.1%) | 230/268 (85.8%) | 58/60 (96.7%) | 55/60 (91.7%) |
| V0 | B_ocr_clean | 64/90 (71.1%) | 66/90 (73.3%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V0 | C_ocr_degraded | 73/90 (81.1%) | 74/90 (82.2%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V1 | A_native | 450/694 (64.8%) | 461/694 (66.4%) | 236/268 (88.1%) | 230/268 (85.8%) | 58/60 (96.7%) | 55/60 (91.7%) |
| V1 | B_ocr_clean | 64/90 (71.1%) | 66/90 (73.3%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V1 | C_ocr_degraded | 73/90 (81.1%) | 74/90 (82.2%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V2 | A_native | 452/694 (65.1%) | 484/694 (69.7%) | 257/268 (95.9%) | 233/268 (86.9%) | 60/60 (100.0%) | 57/60 (95.0%) |
| V2 | B_ocr_clean | 64/90 (71.1%) | 66/90 (73.3%) | 22/22 (100.0%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V2 | C_ocr_degraded | 73/90 (81.1%) | 75/90 (83.3%) | 21/22 (95.5%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V3 | A_native | 450/694 (64.8%) | 461/694 (66.4%) | 236/268 (88.1%) | 230/268 (85.8%) | 58/60 (96.7%) | 55/60 (91.7%) |
| V3 | B_ocr_clean | 64/90 (71.1%) | 66/90 (73.3%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |
| V3 | C_ocr_degraded | 73/90 (81.1%) | 74/90 (82.2%) | 20/22 (90.9%) | 20/22 (90.9%) | 4/4 (100.0%) | 4/4 (100.0%) |

## Matriz de confusão por variante

| Variante | Caminho | Intenção | LOW | MEDIUM | HIGH |
|---|---|---|---:|---:|---:|
| V0 | A_native | LOW | 16 | 0 | 22 |
| V0 | A_native | MEDIUM | 6 | 2 | 13 |
| V0 | A_native | HIGH | 26 | 4 | 217 |
| V0 | B_ocr_clean | LOW | 2 | 0 | 6 |
| V0 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V0 | B_ocr_clean | HIGH | 2 | 0 | 20 |
| V0 | C_ocr_degraded | LOW | 2 | 0 | 6 |
| V0 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V0 | C_ocr_degraded | HIGH | 2 | 0 | 20 |
| V1 | A_native | LOW | 16 | 0 | 22 |
| V1 | A_native | MEDIUM | 6 | 2 | 13 |
| V1 | A_native | HIGH | 5 | 25 | 217 |
| V1 | B_ocr_clean | LOW | 2 | 0 | 6 |
| V1 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V1 | B_ocr_clean | HIGH | 0 | 2 | 20 |
| V1 | C_ocr_degraded | LOW | 2 | 0 | 6 |
| V1 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V1 | C_ocr_degraded | HIGH | 1 | 1 | 20 |
| V2 | A_native | LOW | 16 | 0 | 22 |
| V2 | A_native | MEDIUM | 6 | 1 | 14 |
| V2 | A_native | HIGH | 5 | 23 | 219 |
| V2 | B_ocr_clean | LOW | 2 | 0 | 6 |
| V2 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V2 | B_ocr_clean | HIGH | 0 | 2 | 20 |
| V2 | C_ocr_degraded | LOW | 2 | 0 | 6 |
| V2 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V2 | C_ocr_degraded | HIGH | 1 | 1 | 20 |
| V3 | A_native | LOW | 16 | 0 | 22 |
| V3 | A_native | MEDIUM | 6 | 2 | 13 |
| V3 | A_native | HIGH | 26 | 4 | 217 |
| V3 | B_ocr_clean | LOW | 2 | 0 | 6 |
| V3 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V3 | B_ocr_clean | HIGH | 2 | 0 | 20 |
| V3 | C_ocr_degraded | LOW | 2 | 0 | 6 |
| V3 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V3 | C_ocr_degraded | HIGH | 2 | 0 | 20 |
