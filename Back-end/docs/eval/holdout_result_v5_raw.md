# Resultado do holdout — avaliação oficial

Artefato: `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e`; threshold: 0.809.

| Path | N | Pos | Neg | PR-AUC | ROC-AUC | F1 | Recall | TP | FN | FP | TN | FP Wilson 95% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_native | 940 | 280 | 660 | 1.000 | 1.000 | 0.996 | 0.993 | 278 | 2 | 0 | 660 | 0.006 |
| B_ocr_clean | 160 | 112 | 48 | 1.000 | 1.000 | 0.341 | 0.205 | 23 | 89 | 0 | 48 | 0.074 |
| C_ocr_degraded | 160 | 112 | 48 | 0.962 | 0.912 | 0.236 | 0.134 | 15 | 97 | 0 | 48 | 0.074 |

## Critérios

| Path | Passou | Checks | Motivos |
|---|---|---|---|
| A_native | False | sample_size=True, pr_auc_gt_deterministic=True, f1_gt_deterministic=True, pr_auc_gt_fusion=True, f1_gt_fusion=True, naive_non_inferior=True, multi_non_inferior=False, fp_cap=True | multi: sem amostra |
| B_ocr_clean | False | sample_size=True, pr_auc_gt_deterministic=True, f1_gt_deterministic=True, pr_auc_gt_fusion=True, f1_gt_fusion=True, naive_non_inferior=True, multi_non_inferior=False, fp_cap=True | multi: sem amostra |
| C_ocr_degraded | False | sample_size=True, pr_auc_gt_deterministic=True, f1_gt_deterministic=True, pr_auc_gt_fusion=True, f1_gt_fusion=False, naive_non_inferior=True, multi_non_inferior=False, fp_cap=True | F1 não supera fusion; multi: sem amostra |

## ICs bootstrap por linhagem/documento

| Path | Métrica | IC 95% |
|---|---|---|
| A_native | precision | [1.000; 1.000] |
| A_native | recall | [0.982; 1.000] |
| A_native | f1 | [0.991; 1.000] |
| A_native | pr_auc | [1.000; 1.000] |
| A_native | roc_auc | [1.000; 1.000] |
| B_ocr_clean | precision | [1.000; 1.000] |
| B_ocr_clean | recall | [0.132; 0.283] |
| B_ocr_clean | f1 | [0.233; 0.442] |
| B_ocr_clean | pr_auc | [1.000; 1.000] |
| B_ocr_clean | roc_auc | [0.999; 1.000] |
| C_ocr_degraded | precision | [1.000; 1.000] |
| C_ocr_degraded | recall | [0.075; 0.202] |
| C_ocr_degraded | f1 | [0.139; 0.336] |
| C_ocr_degraded | pr_auc | [0.936; 0.980] |
| C_ocr_degraded | roc_auc | [0.865; 0.951] |

## Grupos (N, TP/FN, FP/TN)

| Path | Dimensão | Grupo | TP | FN | FP | TN | Recall | Indicativo |
|---|---|---|---:|---:|---:|---:|---:|---|
| A_native | language | pt | 93 | 1 | 0 | 220 | 0.989 | False |
| A_native | language | es | 93 | 0 | 0 | 220 | 1.000 | False |
| A_native | language | en | 92 | 1 | 0 | 220 | 0.989 | False |
| A_native | layout | A | 70 | 0 | 0 | 165 | 1.000 | False |
| A_native | layout | B | 70 | 0 | 0 | 165 | 1.000 | False |
| A_native | layout | C | 69 | 1 | 0 | 165 | 0.986 | False |
| A_native | layout | D | 69 | 1 | 0 | 165 | 0.986 | False |
| A_native | document_type | boleto | 120 | 0 | 0 | 330 | 1.000 | False |
| A_native | document_type | contracheque | 158 | 2 | 0 | 330 | 0.988 | False |
| B_ocr_clean | language | es | 5 | 32 | 0 | 16 | 0.135 | False |
| B_ocr_clean | language | en | 13 | 28 | 0 | 16 | 0.317 | False |
| B_ocr_clean | language | pt | 5 | 29 | 0 | 16 | 0.147 | False |
| B_ocr_clean | layout | B | 4 | 26 | 0 | 13 | 0.133 | False |
| B_ocr_clean | layout | C | 3 | 17 | 0 | 11 | 0.150 | False |
| B_ocr_clean | layout | A | 5 | 21 | 0 | 12 | 0.192 | False |
| B_ocr_clean | layout | D | 11 | 25 | 0 | 12 | 0.306 | False |
| B_ocr_clean | document_type | contracheque | 16 | 48 | 0 | 25 | 0.250 | False |
| B_ocr_clean | document_type | boleto | 7 | 41 | 0 | 23 | 0.146 | False |
| C_ocr_degraded | language | es | 3 | 34 | 0 | 16 | 0.081 | False |
| C_ocr_degraded | language | en | 9 | 32 | 0 | 16 | 0.220 | False |
| C_ocr_degraded | language | pt | 3 | 31 | 0 | 16 | 0.088 | False |
| C_ocr_degraded | layout | B | 2 | 28 | 0 | 13 | 0.067 | False |
| C_ocr_degraded | layout | C | 2 | 18 | 0 | 11 | 0.100 | False |
| C_ocr_degraded | layout | A | 3 | 23 | 0 | 12 | 0.115 | False |
| C_ocr_degraded | layout | D | 8 | 28 | 0 | 12 | 0.222 | False |
| C_ocr_degraded | document_type | contracheque | 15 | 49 | 0 | 25 | 0.234 | False |
| C_ocr_degraded | document_type | boleto | 0 | 48 | 0 | 23 | 0.000 | False |

O resultado não deve ser produzido antes do selo commitado. Qualquer falha encerra a promoção do candidato nesta rodada.
