# Resultado oficial do holdout v5

**Status:** execução oficial única concluída; resultado disponível. O candidato **não foi promovido** porque os critérios de aceite não foram integralmente atendidos.

## Preflight oficial

- Data/hora: `2026-11-12T00:24:16.539128+00:00`
- HEAD: `c5d161efd4d660b73554d19cee9f01fcdb345d8b`
- Preflight passou: `True`
- SHA-256 do selo: `aebfb54085bd8145c0effe98c20c2c05f3f59a8df7184bfceddc1d2d222e9715`
- SHA-256 do preflight: `0eb4592e91df2f0f8e7d6afec2df1c810d448b021c24553f51dd5ef2e3425fb2`
- Nenhum modelo foi carregado no preflight.

## Execução

- Medição: 1 execução, exit code 0, 1368 observações (1000 native + 368 OCR).
- Avaliação: 1 execução, exit code 0.
- evidence dump SHA-256: `3188c43c0b000dc7c02874cc37ac501807d9eea39c01414132fca13b943e1c7d`
- Nenhuma evidência de v3/v4 foi reutilizada.
- Nenhuma rodada exploratória foi executada no v5.

## Métricas por cohort e modelo

| Cohort | Modelo | N | Pos | Neg | TP | FN | FP | TN | PR-AUC | ROC-AUC | Precision | Recall | F1 | Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | logistic | 940 | 280 | 660 | 278 | 2 | 0 | 660 | 1.0000 | 1.0000 | 1.0000 | 0.9929 | 0.9964 | 0.0097 |
| native | deterministic | 940 | 280 | 660 | 259 | 21 | 0 | 660 | 0.9473 | 0.9625 | 1.0000 | 0.9250 | 0.9610 | 0.0223 |
| native | fusion | 940 | 280 | 660 | 156 | 124 | 0 | 660 | 0.9934 | 0.9969 | 1.0000 | 0.5571 | 0.7156 | 0.0868 |
| B_ocr_clean | logistic | 160 | 112 | 48 | 23 | 89 | 0 | 48 | 0.9999 | 0.9998 | 1.0000 | 0.2054 | 0.3407 | 0.1261 |
| B_ocr_clean | deterministic | 160 | 112 | 48 | 15 | 97 | 0 | 48 | 0.7402 | 0.5670 | 1.0000 | 0.1339 | 0.2362 | 0.6062 |
| B_ocr_clean | fusion | 160 | 112 | 48 | 15 | 97 | 0 | 48 | 0.9700 | 0.9501 | 1.0000 | 0.1339 | 0.2362 | 0.3630 |
| C_ocr_degraded | logistic | 160 | 112 | 48 | 15 | 97 | 0 | 48 | 0.9617 | 0.9125 | 1.0000 | 0.1339 | 0.2362 | 0.1897 |
| C_ocr_degraded | deterministic | 160 | 112 | 48 | 14 | 98 | 0 | 48 | 0.7375 | 0.5625 | 1.0000 | 0.1250 | 0.2222 | 0.6125 |
| C_ocr_degraded | fusion | 160 | 112 | 48 | 20 | 92 | 5 | 43 | 0.8027 | 0.6688 | 0.8000 | 0.1786 | 0.2920 | 0.3676 |

Reconciliação: em todos os cohorts e modelos, TP + FN = Pos e FP + TN = Neg. Não houve descarte de documentos.

## Naive e multi

| Cohort | Categoria | N | TP | FN | Recall Logistic | Recall Deterministic | Recall Fusion | Não inferior? |
|---|---|---:|---:|---:|---:|---:|---:|---|
| native | naive | 280 | 278 | 2 | 0.9929 | 0.9250 | 0.5571 | sim |
| native | multi | 0 | 0 | 0 | N/A | N/A | N/A | inconclusivo (N=0) |
| B_ocr_clean | naive | 112 | 23 | 89 | 0.2054 | 0.1339 | 0.1339 | sim |
| B_ocr_clean | multi | 0 | 0 | 0 | N/A | N/A | N/A | inconclusivo (N=0) |
| C_ocr_degraded | naive | 112 | 15 | 97 | 0.1339 | 0.1250 | 0.1786 | sim |
| C_ocr_degraded | multi | 0 | 0 | 0 | N/A | N/A | N/A | inconclusivo (N=0) |

**Cobertura:** não há documentos `multi` no holdout v5; todos os 280 supervisionados são `naive`. Isso torna o critério de multi inconclusivo, não aprovado. Não foi feita segunda rodada.

## Falsos positivos — Logistic

| Cohort | FP | FP+TN | Taxa observada | Wilson 95% | Cap | Status |
|---|---:|---:|---:|---:|---:|---|
| native | 0 | 660 | 0.0000 | 0.0058 | 0.05 | passa |
| B_ocr_clean | 0 | 48 | 0.0000 | 0.0741 | 0.10 | passa |
| C_ocr_degraded | 0 | 48 | 0.0000 | 0.0741 | 0.15 | passa |

## Intervalos de confiança por linhagem

| Cohort | Métrica | IC 95% |
|---|---|---|
| native | precision | [1.0000; 1.0000] |
| native | recall | [0.9815; 1.0000] |
| native | f1 | [0.9907; 1.0000] |
| native | pr_auc | [1.0000; 1.0000] |
| native | roc_auc | [1.0000; 1.0000] |
| B_ocr_clean | precision | [1.0000; 1.0000] |
| B_ocr_clean | recall | [0.1316; 0.2834] |
| B_ocr_clean | f1 | [0.2325; 0.4416] |
| B_ocr_clean | pr_auc | [0.9996; 1.0000] |
| B_ocr_clean | roc_auc | [0.9989; 1.0000] |
| C_ocr_degraded | precision | [1.0000; 1.0000] |
| C_ocr_degraded | recall | [0.0747; 0.2019] |
| C_ocr_degraded | f1 | [0.1391; 0.3360] |
| C_ocr_degraded | pr_auc | [0.9363; 0.9802] |
| C_ocr_degraded | roc_auc | [0.8651; 0.9509] |

## Tabelas por idioma/layout/tipo — Logistic

| Cohort | Dimensão | Grupo | TP | FN | FP | TN | Recall | Indicativo |
|---|---|---|---:|---:|---:|---:|---:|---|
| native | language | pt | 93 | 1 | 0 | 220 | 0.9894 | False |
| native | language | es | 93 | 0 | 0 | 220 | 1.0000 | False |
| native | language | en | 92 | 1 | 0 | 220 | 0.9892 | False |
| native | layout | A | 70 | 0 | 0 | 165 | 1.0000 | False |
| native | layout | B | 70 | 0 | 0 | 165 | 1.0000 | False |
| native | layout | C | 69 | 1 | 0 | 165 | 0.9857 | False |
| native | layout | D | 69 | 1 | 0 | 165 | 0.9857 | False |
| native | document_type | boleto | 120 | 0 | 0 | 330 | 1.0000 | False |
| native | document_type | contracheque | 158 | 2 | 0 | 330 | 0.9875 | False |
| B_ocr_clean | language | es | 5 | 32 | 0 | 16 | 0.1351 | False |
| B_ocr_clean | language | en | 13 | 28 | 0 | 16 | 0.3171 | False |
| B_ocr_clean | language | pt | 5 | 29 | 0 | 16 | 0.1471 | False |
| B_ocr_clean | layout | B | 4 | 26 | 0 | 13 | 0.1333 | False |
| B_ocr_clean | layout | C | 3 | 17 | 0 | 11 | 0.1500 | False |
| B_ocr_clean | layout | A | 5 | 21 | 0 | 12 | 0.1923 | False |
| B_ocr_clean | layout | D | 11 | 25 | 0 | 12 | 0.3056 | False |
| B_ocr_clean | document_type | contracheque | 16 | 48 | 0 | 25 | 0.2500 | False |
| B_ocr_clean | document_type | boleto | 7 | 41 | 0 | 23 | 0.1458 | False |
| C_ocr_degraded | language | es | 3 | 34 | 0 | 16 | 0.0811 | False |
| C_ocr_degraded | language | en | 9 | 32 | 0 | 16 | 0.2195 | False |
| C_ocr_degraded | language | pt | 3 | 31 | 0 | 16 | 0.0882 | False |
| C_ocr_degraded | layout | B | 2 | 28 | 0 | 13 | 0.0667 | False |
| C_ocr_degraded | layout | C | 2 | 18 | 0 | 11 | 0.1000 | False |
| C_ocr_degraded | layout | A | 3 | 23 | 0 | 12 | 0.1154 | False |
| C_ocr_degraded | layout | D | 8 | 28 | 0 | 12 | 0.2222 | False |
| C_ocr_degraded | document_type | contracheque | 15 | 49 | 0 | 25 | 0.2344 | False |
| C_ocr_degraded | document_type | boleto | 0 | 48 | 0 | 23 | 0.0000 | False |

## Critérios

| Cohort | Sample | a det | a Fusion | b det | b Fusion | c naive | c multi | d FP | Passou | Motivos |
|---|---|---|---|---|---|---|---|---|---|---|
| native | True | True | True | True | True | True | False | True | False | multi: sem amostra |
| B_ocr_clean | True | True | True | True | True | True | False | True | False | multi: sem amostra |
| C_ocr_degraded | True | True | True | True | False | True | False | True | False | F1 não supera fusion; multi: sem amostra |

## Decisão

- `native`: a, b e d passam; `naive` passa; `multi` é inconclusivo (N=0). Cohort **não aprovado**.
- `B_ocr_clean`: a, b e d passam; `naive` passa; `multi` é inconclusivo. Cohort **não aprovado**.
- `C_ocr_degraded`: a e d passam; **b falha** contra Fusion; `multi` inconclusivo. Cohort **reprovado** e incompleto.
- **Decisão global: NÃO PROMOVIDO.** A promoção exige todos os cohorts conclusivos e aprovados.
- A ausência de `multi` é uma falha de cobertura do holdout, não uma aprovação por desempenho. Não houve reexecução.

## Especialistas

Os 60 especialistas (24 na amostra OCR) não foram diagnosticados pelo avaliador congelado, que os exclui dos cohorts. Não foi feita uma segunda rodada de inferência para produzi-los após observar o resultado. Portanto, o diagnóstico B6/B7/P4 está **ausente** nesta rodada.

## Limitações

- Holdout sintético; não substitui validação representativa em dados reais/OOD.
- Não há documentos multi; o critério correspondente não pode ser avaliado.
- Especialistas não têm diagnóstico próprio nesta execução.
- As probabilidades logísticas não são taxa real de fraude.
- Brier de Deterministic/Fusion é descritivo, não calibração.

## Artefatos

- `docs/eval/holdout_result_v5.md` (este relatório)
- `docs/eval/holdout_result_v5.json` (estruturado)
- `docs/eval/holdout_result_v5_raw.md` / `.raw.json` (saída bruta)
- `docs/eval/holdout_preflight_v5_official.json`
- `docs/eval/holdout_seal_v5.json`
- `docs/eval/holdout_v5_measurement.log` / `holdout_v5_official_eval.log`
