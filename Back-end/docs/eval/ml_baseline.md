# 6B — Baseline de scikit-learn (offline e shadow)

Nenhum modelo foi integrado ao CanonicalPipeline, à API ou ao FusionEngine. O experimento é offline e shadow.

Dataset: v2.1 native; features=119; scikit-learn=1.9.0.

## Dataset e rótulo

- Positivos: naive/multi (B1-B5, B8, P1-P3, P5-P9).
- Negativos: legítimos.
- B6/B7/P4 excluídos do treino e da avaliação principal; avaliados separadamente em 6A.5.
- N por split (legítimos/adulterados): train=416/162, val=100/40, test_iid=109/39, test_shift=69/27
- Variantes de um mesmo documento permanecem no mesmo split; o treino inicial usa somente native.

## Seleção de modelo

| C | Val PR-AUC |
|---|---:|
| 0.01 | 1.000 |
| 0.1 | 1.000 |
| 1.0 | 1.000 |
| 10.0 | 1.000 |

C escolhido: **0.01**; threshold escolhido na validação: **0.809**.

## Métricas por split

| Split | Modelo | N | PR-AUC | ROC-AUC | Pos P/R/F1 | Neg P/R/F1 | Brier | Threshold |
|---|---|---:|---:|---:|---|---|---:|---:|
| val | Dummy | 140 | 0.286 | 0.500 | 0.000/0.000/0.000 | 0.714/1.000/0.833 | 0.204 | 0.500 |
| val | Deterministic | 140 | 0.964 | 0.975 | 1.000/0.950/0.974 | 0.980/1.000/0.990 | 0.014 | 0.500 |
| val | Fusion | 140 | 0.998 | 0.999 | 1.000/0.775/0.873 | 0.917/1.000/0.957 | 0.059 | 0.400 |
| val | Logistic | 140 | 1.000 | 1.000 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | 0.008 | 0.809 |
| test_iid | Dummy | 148 | 0.264 | 0.500 | 0.000/0.000/0.000 | 0.736/1.000/0.848 | 0.194 | 0.500 |
| test_iid | Deterministic | 148 | 0.962 | 0.974 | 1.000/0.949/0.974 | 0.982/1.000/0.991 | 0.014 | 0.500 |
| test_iid | Fusion | 148 | 0.993 | 0.997 | 1.000/0.667/0.800 | 0.893/1.000/0.944 | 0.066 | 0.400 |
| test_iid | Logistic | 148 | 1.000 | 1.000 | 1.000/0.974/0.987 | 0.991/1.000/0.995 | 0.009 | 0.809 |
| test_shift | Dummy | 96 | 0.281 | 0.500 | 0.000/0.000/0.000 | 0.719/1.000/0.836 | 0.202 | 0.500 |
| test_shift | Deterministic | 96 | 0.867 | 0.907 | 1.000/0.815/0.898 | 0.932/1.000/0.965 | 0.052 | 0.500 |
| test_shift | Fusion | 96 | 0.981 | 0.992 | 1.000/0.481/0.650 | 0.831/1.000/0.908 | 0.097 | 0.400 |
| test_shift | Logistic | 96 | 1.000 | 1.000 | 1.000/0.926/0.962 | 0.972/1.000/0.986 | 0.010 | 0.809 |

## Detalhamento
### Matrizes de confusão

| Split | Modelo | TN | FP | FN | TP |
|---|---|---:|---:|---:|---:|
| val | Dummy | 100 | 0 | 40 | 0 |
| val | Deterministic | 100 | 0 | 2 | 38 |
| val | Fusion | 100 | 0 | 9 | 31 |
| val | Logistic | 100 | 0 | 0 | 40 |
| test_iid | Dummy | 109 | 0 | 39 | 0 |
| test_iid | Deterministic | 109 | 0 | 2 | 37 |
| test_iid | Fusion | 109 | 0 | 13 | 26 |
| test_iid | Logistic | 109 | 0 | 1 | 38 |
| test_shift | Dummy | 69 | 0 | 27 | 0 |
| test_shift | Deterministic | 69 | 0 | 5 | 22 |
| test_shift | Fusion | 69 | 0 | 14 | 13 |
| test_shift | Logistic | 69 | 0 | 2 | 25 |

### Falsos positivos por caminho

| Split | Modelo | Path | Legítimos | FP | Fraudes | Detectadas |
|---|---|---|---:|---:|---:|---:|
| val | Dummy | A_native | 100 | 0 | 40 | 0 |
| val | Deterministic | A_native | 100 | 0 | 40 | 38 |
| val | Fusion | A_native | 100 | 0 | 40 | 31 |
| val | Logistic | A_native | 100 | 0 | 40 | 40 |
| test_iid | Dummy | A_native | 109 | 0 | 39 | 0 |
| test_iid | Deterministic | A_native | 109 | 0 | 39 | 37 |
| test_iid | Fusion | A_native | 109 | 0 | 39 | 26 |
| test_iid | Logistic | A_native | 109 | 0 | 39 | 38 |
| test_shift | Dummy | A_native | 69 | 0 | 27 | 0 |
| test_shift | Deterministic | A_native | 69 | 0 | 27 | 22 |
| test_shift | Fusion | A_native | 69 | 0 | 27 | 13 |
| test_shift | Logistic | A_native | 69 | 0 | 27 | 25 |

### Recall por classe

| Split | Modelo | Classe | Detectadas | N | Recall |
|---|---|---|---:|---:|---:|
| test_iid | Deterministic | multi | 13 | 13 | 1.000 |
| test_iid | Deterministic | naive | 24 | 26 | 0.923 |
| test_iid | Fusion | multi | 12 | 13 | 0.923 |
| test_iid | Fusion | naive | 14 | 26 | 0.538 |
| test_iid | Logistic | multi | 13 | 13 | 1.000 |
| test_iid | Logistic | naive | 25 | 26 | 0.962 |
| test_shift | Deterministic | multi | 5 | 5 | 1.000 |
| test_shift | Deterministic | naive | 17 | 22 | 0.773 |
| test_shift | Fusion | multi | 5 | 5 | 1.000 |
| test_shift | Fusion | naive | 8 | 22 | 0.364 |
| test_shift | Logistic | multi | 5 | 5 | 1.000 |
| test_shift | Logistic | naive | 20 | 22 | 0.909 |

### Logistic — recall por idioma, layout e tipo

| Split | Dimensão | Grupo | Detectadas | N | Recall |
|---|---|---|---:|---:|---:|
| test_iid | language | en | 10 | 10 | 1.000 |
| test_iid | language | es | 15 | 15 | 1.000 |
| test_iid | language | pt | 13 | 14 | 0.929 |
| test_iid | layout | A | 7 | 8 | 0.875 |
| test_iid | layout | B | 12 | 12 | 1.000 |
| test_iid | layout | C | 19 | 19 | 1.000 |
| test_iid | document_type | boleto | 16 | 16 | 1.000 |
| test_iid | document_type | contracheque | 22 | 23 | 0.957 |
| test_shift | language | en | 5 | 6 | 0.833 |
| test_shift | language | es | 7 | 7 | 1.000 |
| test_shift | language | pt | 13 | 14 | 0.929 |
| test_shift | layout | D | 25 | 27 | 0.926 |
| test_shift | document_type | boleto | 5 | 5 | 1.000 |
| test_shift | document_type | contracheque | 20 | 22 | 0.909 |

## Avaliação externa OCR (modelo treinado só em native)

| Path | Modelo | N | Positivos | PR-AUC | ROC-AUC | Recall naive+multi | FP legítimos |
|---|---|---:|---:|---:|---:|---:|---:|
| B_ocr_clean | Logistic | 106 | 66 | 1.000 | 1.000 | 0.394 | 0 |
| B_ocr_clean | Deterministic | 106 | 66 | 0.668 | 0.561 | 0.121 | 0 |
| B_ocr_clean | Fusion | 106 | 66 | 0.912 | 0.900 | 0.212 | 1 |
| C_ocr_degraded | Logistic | 106 | 66 | 0.982 | 0.970 | 0.409 | 0 |
| C_ocr_degraded | Deterministic | 106 | 66 | 0.668 | 0.561 | 0.121 | 0 |
| C_ocr_degraded | Fusion | 106 | 66 | 0.810 | 0.734 | 0.318 | 2 |

## Calibração do Logistic (test_iid)

| Bin | N | Probabilidade média | Taxa observada |
|---|---:|---:|---:|
| 1 | 15 | 0.041 | 0.000 |
| 2 | 15 | 0.047 | 0.000 |
| 3 | 15 | 0.070 | 0.000 |
| 4 | 15 | 0.079 | 0.000 |
| 5 | 15 | 0.085 | 0.000 |
| 6 | 15 | 0.111 | 0.000 |
| 7 | 15 | 0.116 | 0.000 |
| 8 | 15 | 0.641 | 0.733 |
| 9 | 14 | 0.911 | 1.000 |
| 10 | 14 | 0.997 | 1.000 |

## IsolationForest (experimento separado)

- Treinado somente com legítimos de train; `contamination='auto'`; não é probabilidade de fraude.
- ROC-AUC test_iid: 0.787; test_shift: 0.700.
- PR-AUC test_iid: 0.435; test_shift: 0.394.
- Threshold p95 em legítimos de val: 0.640.
- Recall no threshold p95: test_iid 0.077; test_shift 0.037.
- Fraudes perdidas pelo Logistic e flagradas pela anomalia em test_iid: 0/1.

Conclusão: a anomalia não é usada para decisão; o resultado indica se acrescenta sinal além das regras/classificação.

## Features e vazamento

- 119 features numéricas, listadas no manifesto.
- Nenhum campo de `tamper_types`, `sophistication`, `intended_band`, `gabarito`, `seed`, `document_id`, texto bruto, nome ou empresa.
- Imputação e escala dentro do Pipeline, ajustadas somente em train.
- Testes de reprodutibilidade, ausência de vazamento, inferência com feature ausente/desconhecida e ausência de chamadas a LLM/rede.

## Trade-offs e limitações

- O conjunto é de desenvolvimento/avaliação; `test_iid`/`test_shift` não são holdout intocado.
- O modelo é treinado somente em native; a avaliação OCR é domínio externo e tem N pequeno.
- Probabilidades não são convertidas automaticamente em LOW/MEDIUM/HIGH.
- B6/B7/P4 estão fora da cobertura e não entram no treino.
- Se o ganho sobre as baselines não for consistente, o modelo não deve ser integrado.
