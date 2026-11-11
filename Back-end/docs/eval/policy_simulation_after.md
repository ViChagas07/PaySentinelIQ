# Simulação de política — depois da Fase 5B

Recalcula o score fusionado a partir do `evidence_dump` com a fórmula do FusionEngine: peso da severidade × multiplicador da fonte × confiança, pisos de 1 e 3 críticos, fator 1,2 para 2+ críticos e limite 100.

## Simulação de política (somente leitura)

| Variante | Caminho | Legítimos >= 70 | Legítimos >= 40 | Recall naive >= 40 | Recall naive >= 70 | Recall multi >= 40 | Recall multi >= 70 |
|---|---|---:|---:|---:|---:|---:|---:|
| V0 | A_native | 0/694 (0.0%) | 2/694 (0.3%) | 167/268 (62.3%) | 138/268 (51.5%) | 54/60 (90.0%) | 37/60 (61.7%) |
| V0 | B_ocr_clean | 0/90 (0.0%) | 0/90 (0.0%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |
| V0 | C_ocr_degraded | 0/90 (0.0%) | 3/90 (3.3%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |
| V1 | A_native | 0/694 (0.0%) | 2/694 (0.3%) | 167/268 (62.3%) | 138/268 (51.5%) | 54/60 (90.0%) | 37/60 (61.7%) |
| V1 | B_ocr_clean | 0/90 (0.0%) | 0/90 (0.0%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |
| V1 | C_ocr_degraded | 0/90 (0.0%) | 3/90 (3.3%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |
| V2 | A_native | 0/694 (0.0%) | 32/694 (4.6%) | 236/268 (88.1%) | 147/268 (54.9%) | 59/60 (98.3%) | 45/60 (75.0%) |
| V2 | B_ocr_clean | 0/90 (0.0%) | 1/90 (1.1%) | 12/22 (54.5%) | 4/22 (18.2%) | 4/4 (100.0%) | 2/4 (50.0%) |
| V2 | C_ocr_degraded | 1/90 (1.1%) | 29/90 (32.2%) | 12/22 (54.5%) | 4/22 (18.2%) | 4/4 (100.0%) | 2/4 (50.0%) |
| V3 | A_native | 0/694 (0.0%) | 0/694 (0.0%) | 167/268 (62.3%) | 138/268 (51.5%) | 54/60 (90.0%) | 37/60 (61.7%) |
| V3 | B_ocr_clean | 0/90 (0.0%) | 0/90 (0.0%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |
| V3 | C_ocr_degraded | 0/90 (0.0%) | 0/90 (0.0%) | 4/22 (18.2%) | 4/22 (18.2%) | 2/4 (50.0%) | 2/4 (50.0%) |

## Matriz de confusão por variante

| Variante | Caminho | Intenção | LOW | MEDIUM | HIGH |
|---|---|---|---:|---:|---:|
| V0 | A_native | LOW | 38 | 0 | 0 |
| V0 | A_native | MEDIUM | 17 | 3 | 1 |
| V0 | A_native | HIGH | 84 | 26 | 137 |
| V0 | B_ocr_clean | LOW | 8 | 0 | 0 |
| V0 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V0 | B_ocr_clean | HIGH | 18 | 0 | 4 |
| V0 | C_ocr_degraded | LOW | 8 | 0 | 0 |
| V0 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V0 | C_ocr_degraded | HIGH | 18 | 0 | 4 |
| V1 | A_native | LOW | 38 | 0 | 0 |
| V1 | A_native | MEDIUM | 17 | 3 | 1 |
| V1 | A_native | HIGH | 15 | 95 | 137 |
| V1 | B_ocr_clean | LOW | 7 | 1 | 0 |
| V1 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V1 | B_ocr_clean | HIGH | 10 | 8 | 4 |
| V1 | C_ocr_degraded | LOW | 6 | 2 | 0 |
| V1 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V1 | C_ocr_degraded | HIGH | 10 | 8 | 4 |
| V2 | A_native | LOW | 38 | 0 | 0 |
| V2 | A_native | MEDIUM | 17 | 2 | 2 |
| V2 | A_native | HIGH | 15 | 87 | 145 |
| V2 | B_ocr_clean | LOW | 7 | 1 | 0 |
| V2 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V2 | B_ocr_clean | HIGH | 10 | 8 | 4 |
| V2 | C_ocr_degraded | LOW | 6 | 2 | 0 |
| V2 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V2 | C_ocr_degraded | HIGH | 10 | 8 | 4 |
| V3 | A_native | LOW | 38 | 0 | 0 |
| V3 | A_native | MEDIUM | 17 | 3 | 1 |
| V3 | A_native | HIGH | 84 | 26 | 137 |
| V3 | B_ocr_clean | LOW | 8 | 0 | 0 |
| V3 | B_ocr_clean | MEDIUM | 0 | 0 | 0 |
| V3 | B_ocr_clean | HIGH | 18 | 0 | 4 |
| V3 | C_ocr_degraded | LOW | 8 | 0 | 0 |
| V3 | C_ocr_degraded | MEDIUM | 0 | 0 | 0 |
| V3 | C_ocr_degraded | HIGH | 18 | 0 | 4 |
