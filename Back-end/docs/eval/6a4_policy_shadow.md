# 6A.4 — Políticas em shadow (V0, V2, V4, V5)

Native: dump completo v2.1 (1000 documentos). N=694 legítimos; adulterados naive/multi conforme dump.
OCR: 6A.3, 112 documentos (40 legítimos), agregados por documento e path usando a melhor variante; não são 4 observações independentes.

Nenhuma variante foi ativada. `risk_level`, FusionEngine e API permanecem inalterados.

## N por caminho

| Caminho | N | Legítimos | Adulterados naive/multi |
|---|---:|---:|---:|
| A_native | 1000 | 694 | 268 |
| B_ocr_clean | 112 | 40 | 66 |
| C_ocr_degraded | 112 | 40 | 66 |

## Score e decisão por variante

| Variante | Caminho | Legítimos >=70 | Legítimos >=40 | Recall naive >=40 | Recall naive >=70 | Recall multi >=40 | Recall multi >=70 | needs_review | Dados insuficientes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 | A_native | 0/694 (0.0%) | 0/694 (0.0%) | 176/268 (65.7%) | 147/268 (54.9%) | 58/60 (96.7%) | 40/60 (66.7%) | 0/1000 | 0/1000 |
| V0 | B_ocr_clean | 0/40 (0.0%) | 1/40 (2.5%) | 14/66 (21.2%) | 3/66 (4.5%) | 8/18 (44.4%) | 2/18 (11.1%) | 104/112 | 6/112 |
| V0 | C_ocr_degraded | 0/40 (0.0%) | 2/40 (5.0%) | 21/66 (31.8%) | 4/66 (6.1%) | 9/18 (50.0%) | 3/18 (16.7%) | 104/112 | 34/112 |
| V2 | A_native | 0/694 (0.0%) | 0/694 (0.0%) | 249/268 (92.9%) | 157/268 (58.6%) | 60/60 (100.0%) | 50/60 (83.3%) | 0/1000 | 0/1000 |
| V2 | B_ocr_clean | 1/40 (2.5%) | 5/40 (12.5%) | 36/66 (54.5%) | 9/66 (13.6%) | 9/18 (50.0%) | 5/18 (27.8%) | 104/112 | 6/112 |
| V2 | C_ocr_degraded | 1/40 (2.5%) | 18/40 (45.0%) | 39/66 (59.1%) | 12/66 (18.2%) | 10/18 (55.6%) | 6/18 (33.3%) | 104/112 | 34/112 |
| V4 | A_native | 0/694 (0.0%) | 0/694 (0.0%) | 249/268 (92.9%) | 157/268 (58.6%) | 60/60 (100.0%) | 50/60 (83.3%) | 0/1000 | 0/1000 |
| V4 | B_ocr_clean | 0/40 (0.0%) | 2/40 (5.0%) | 24/66 (36.4%) | 7/66 (10.6%) | 9/18 (50.0%) | 4/18 (22.2%) | 104/112 | 6/112 |
| V4 | C_ocr_degraded | 0/40 (0.0%) | 8/40 (20.0%) | 26/66 (39.4%) | 10/66 (15.2%) | 10/18 (55.6%) | 5/18 (27.8%) | 104/112 | 34/112 |

## V5 — decisão explícita (shadow)

| Caminho | N | HIGH | MEDIUM | LOW | needs_review | Dados insuficientes |
|---|---:|---:|---:|---:|---:|---:|
| A_native | 1000 | 154 | 95 | 751 | 0 | 0 |
| B_ocr_clean | 112 | 1 | 40 | 71 | 104 | 6 |
| C_ocr_degraded | 112 | 1 | 60 | 51 | 104 | 34 |

### V5 — recall e falsos positivos

| Caminho | FP MEDIUM+ | FP HIGH | Recall naive MEDIUM+ | Recall naive HIGH | Recall multi MEDIUM+ | Recall multi HIGH |
|---|---:|---:|---:|---:|---:|---:|
| A_native | 0/694 (0.0%) | 0/694 (0.0%) | 249/268 (92.9%) | 154/268 (57.5%) | 60/60 (100.0%) | 47/60 (78.3%) |
| B_ocr_clean | 5/40 (12.5%) | 0/40 (0.0%) | 36/66 (54.5%) | 1/66 (1.5%) | 9/18 (50.0%) | 1/18 (5.6%) |
| C_ocr_degraded | 18/40 (45.0%) | 0/40 (0.0%) | 39/66 (59.1%) | 1/66 (1.5%) | 10/18 (55.6%) | 1/18 (5.6%) |

## Motivos de needs_review

| Motivo | Ocorrências |
|---|---:|
| ocr_sem_confirmacao | 122 |
| dados_insuficientes | 40 |
| ocr_incerto | 86 |

## Limitações

- V4 é uma variante de contribuição (+50% para determinística confirmada), não uma recomendação.
- V5 é uma decisão por grupos de fato; info/low não confirmam adulteração e evidência OCR incerta favorece revisão.
- Nenhuma variante foi ligada ao pipeline ou à API.
- O conjunto atual é de desenvolvimento/avaliação; não é holdout.
