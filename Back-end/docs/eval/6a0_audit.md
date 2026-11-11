# 6A.0 — Auditoria antes das correções

Fonte: `../data/synthetic/v1/eval/evidence_dump.jsonl` (dataset v1, pós-5B).

## 1. BOLETO_DUE_DATE_MISMATCH em legítimos

Total: **29**.

| ID | Idioma | Layout | data extraída | gabarito | data_documento | data_emissão | causa |
|---|---|---|---|---|---|---|---|
| syn-42-00905 | es | D | 27/11/2026 | 2026-12-17 | None | 17/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00908 | es | D | 04/10/2026 | 2026-10-24 | None | 24/10/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00913 | pt | D | 26/11/2026 | 2026-12-02 | None | 02/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00914 | es | D | 23/11/2026 | 2026-12-03 | None | 03/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00916 | pt | D | 16/12/2026 | 2027-01-01 | None | 01/01/2027 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00919 | pt | D | 05/12/2026 | 2026-12-23 | None | 23/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00921 | pt | D | 03/05/2026 | 2026-05-19 | None | 19/05/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00925 | es | D | 12/12/2026 | 2026-12-22 | None | 22/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00926 | pt | D | 30/06/2026 | 2026-07-07 | None | 07/07/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00934 | pt | D | 31/10/2026 | 2026-11-15 | None | 15/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00945 | es | D | 16/10/2026 | 2026-11-10 | None | 10/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00946 | pt | D | 17/09/2026 | 2026-09-22 | None | 22/09/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00947 | es | D | 12/10/2026 | 2026-11-06 | None | 06/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00948 | pt | D | 11/06/2026 | 2026-06-18 | None | 18/06/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00949 | pt | D | 10/08/2026 | 2026-08-17 | None | 17/08/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00952 | pt | D | 03/10/2026 | 2026-10-16 | None | 16/10/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00957 | es | D | 03/06/2026 | 2026-06-20 | None | 20/06/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00959 | pt | D | 25/04/2026 | 2026-04-27 | None | 27/04/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00965 | es | D | 05/01/2027 | 2027-01-11 | None | 11/01/2027 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00966 | pt | D | 28/04/2026 | 2026-05-13 | None | 13/05/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00969 | pt | D | 13/11/2026 | 2026-12-09 | None | 09/12/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00976 | pt | D | 23/10/2026 | 2026-11-16 | None | 16/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00977 | pt | D | 23/10/2026 | 2026-11-04 | None | 04/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00982 | es | D | 29/05/2026 | 2026-06-21 | None | 21/06/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00985 | pt | D | 11/09/2026 | 2026-09-22 | None | 22/09/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00987 | pt | D | 23/07/2026 | 2026-08-18 | None | 18/08/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00994 | pt | D | 03/02/2027 | 2027-02-12 | None | 12/02/2027 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00998 | es | D | 20/10/2026 | 2026-11-12 | None | 12/11/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |
| syn-42-00999 | pt | D | 04/07/2026 | 2026-07-13 | None | 13/07/2026 | DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO |

| Causa | Ocorrências |
|---|---:|
| DATA_ERRADA_TROCA_LEGACY_DOCUMENTO_VENCIMENTO | 29 |

## 2. PAYSLIP_IRRF_MISMATCH em legítimos

Total: **11**.

| ID | Idioma | Layout | bruto | inss extraído | inss gabarito | irrf extraído | base_irrf extraída | dependentes | causa |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| syn-42-00909 | pt | D | 6839.81 | None | 759.10 | 643.4 | None | 1 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00910 | pt | D | 6237.46 | None | 674.76 | 368.61 | None | 2 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00918 | pt | D | 8295.55 | None | 962.89 | 1003.48 | None | 2 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00923 | pt | D | 6548.5 | None | 718.30 | 431.44 | None | 3 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00930 | pt | D | 8443.09 | None | 983.55 | 986.23 | None | 3 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00933 | pt | D | 6761.63 | None | 748.14 | 666.64 | None | 0 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00938 | pt | D | 5061.51 | None | 510.13 | 1.2 | None | 1 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00941 | pt | D | 7174.27 | None | 805.91 | 819.17 | None | 0 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00950 | pt | D | 8974.06 | None | 988.10 | 1183.13 | None | 2 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00953 | pt | D | 8727.38 | None | 988.09 | 1115.3 | None | 2 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |
| syn-42-00963 | pt | D | 5493.7 | None | 570.64 | 145.81 | None | 1 | EXTRACAO_AUSENTE_INSS_BASE_IRRF |

| Causa | Ocorrências |
|---|---:|
| EXTRACAO_AUSENTE_INSS_BASE_IRRF | 11 |

## 3. Adulterados naive/multi em LOW

Total: **137** (todos os caminhos).

| Caminho | ID | Tipos | Classe | Score | Faixa | Códigos esperados | Evidências (código/sev/fonte/ocr_uncertain) |
|---|---|---|---|---:|---|---|---|
| A_native | syn-42-00000 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00008 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00014 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00017 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00024 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00036 | B1 | NENHUMA_EVIDENCIA_GERADA | 3.0 | LOW | BOLETO_AMOUNT_MISMATCH | DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00044 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00052 | P3 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_IRRF_MISMATCH | - |
| A_native | syn-42-00053 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00063 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00094 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00124 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00140 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00157 | B2 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | BOLETO_DUE_DATE_MISMATCH | - |
| A_native | syn-42-00160 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00161 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00163 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00177 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00178 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00183 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00198 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00216 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00222 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00230 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00235 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00253 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00267 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00273 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00275 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00278 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00280 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00288 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00310 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00313 | P9,P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH,PAYSLIP_NET_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00322 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00363 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00369 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00373 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00400 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00403 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00426 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00450 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00457 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00485 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00491 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00508 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00522 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00527 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00541 | B2 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | BOLETO_DUE_DATE_MISMATCH | - |
| A_native | syn-42-00549 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00550 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_DUE_DATE_MISMATCH/high/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| A_native | syn-42-00551 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00559 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00576 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00583 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00587 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00595 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00615 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00628 | B2,B1 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_AMOUNT_MISMATCH,BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00639 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00665 | B2 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | BOLETO_DUE_DATE_MISMATCH | - |
| A_native | syn-42-00671 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00674 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00695 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00703 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00736 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00737 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00753 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00767 | P3,P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_INSS_MISMATCH,PAYSLIP_IRRF_MISMATCH | PAYSLIP_INSS_MISMATCH/high/deterministic/False |
| A_native | syn-42-00806 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00813 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00825 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00826 | P3 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_IRRF_MISMATCH | - |
| A_native | syn-42-00827 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00841 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00853 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00855 | P9,P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT,PAYSLIP_NET_MISMATCH | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00860 | B2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_DUE_DATE_MISMATCH | BOLETO_DUE_DATE_MISMATCH/high/deterministic/False |
| A_native | syn-42-00863 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00875 | P7 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_FGTS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00885 | P8 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | PAYSLIP_DEDUCTIONS_INCONSISTENT/high/deterministic/False |
| A_native | syn-42-00902 | P6 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_PERIOD_FUTURE | - |
| A_native | syn-42-00907 | P9 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_NET_MISMATCH | - |
| A_native | syn-42-00915 | P3 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_IRRF_MISMATCH | - |
| A_native | syn-42-00920 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00924 | P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_IRRF_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00929 | P9 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_NET_MISMATCH | - |
| A_native | syn-42-00940 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00955 | P2,P7 | NENHUMA_EVIDENCIA_GERADA | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH,PAYSLIP_INSS_MISMATCH | PAYSLIP_IRRF_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00961 | P1 | NENHUMA_EVIDENCIA_GERADA | 15.0 | LOW | PAYSLIP_NET_MISMATCH | PAYSLIP_IRRF_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00964 | B1 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | BOLETO_AMOUNT_MISMATCH | - |
| A_native | syn-42-00967 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00968 | P8 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_DEDUCTIONS_INCONSISTENT | - |
| A_native | syn-42-00970 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| A_native | syn-42-00973 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00981 | P5,P3 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_CPF_INVALID,PAYSLIP_IRRF_MISMATCH | PAYSLIP_CPF_INVALID/high/deterministic/False |
| A_native | syn-42-00986 | P7 | NENHUMA_EVIDENCIA_GERADA | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_IRRF_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00989 | P7 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_FGTS_MISMATCH | - |
| A_native | syn-42-00992 | P1 | NENHUMA_EVIDENCIA_GERADA | 30.0 | LOW | PAYSLIP_NET_MISMATCH | PAYSLIP_IRRF_MISMATCH/high/deterministic/False |
| A_native | syn-42-00995 | P7 | NENHUMA_EVIDENCIA_GERADA | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_IRRF_MISMATCH/medium/deterministic/False |
| A_native | syn-42-00996 | P7 | NENHUMA_EVIDENCIA_GERADA | 15.0 | LOW | PAYSLIP_FGTS_MISMATCH | PAYSLIP_IRRF_MISMATCH/medium/deterministic/False |
| B_ocr_clean | syn-42-00000 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/medium/deterministic/True |
| B_ocr_clean | syn-42-00000 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/medium/deterministic/True |
| C_ocr_degraded | syn-42-00000 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/medium/deterministic/True |
| C_ocr_degraded | syn-42-00000 | P2 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_INSS_MISMATCH | PAYSLIP_INSS_MISMATCH/medium/deterministic/True |
| B_ocr_clean | syn-42-00160 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00160 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00160 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00160 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00288 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| B_ocr_clean | syn-42-00288 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| C_ocr_degraded | syn-42-00288 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| C_ocr_degraded | syn-42-00288 | P6 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | PAYSLIP_PERIOD_FUTURE | PAYSLIP_PERIOD_FUTURE/high/deterministic/False |
| B_ocr_clean | syn-42-00352 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_GENERAL_DV_INVALID/high/deterministic/True; DOCUMENT_EXPIRED/info/deterministic/False |
| B_ocr_clean | syn-42-00352 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_GENERAL_DV_INVALID/high/deterministic/True; DOCUMENT_EXPIRED/info/deterministic/False |
| C_ocr_degraded | syn-42-00352 | B4 | NENHUMA_EVIDENCIA_GERADA | 39.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_VENCIDO/info/deterministic/False; LINHA_DIGITAVEL_FORMATO_INCORRETO/high/deterministic/True; BOLETO_OVERDUE/info/deterministic/False; DOCUMENT_EXPIRED/info/deterministic/False |
| C_ocr_degraded | syn-42-00352 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 39.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_VENCIDO/info/deterministic/False; BOLETO_OVERDUE/info/deterministic/False; BOLETO_GENERAL_DV_INVALID/high/deterministic/True; DOCUMENT_EXPIRED/info/deterministic/False |
| B_ocr_clean | syn-42-00400 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00400 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00400 | P5 | NENHUMA_EVIDENCIA_GERADA | 0.0 | LOW | PAYSLIP_CPF_INVALID | - |
| C_ocr_degraded | syn-42-00400 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00448 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_GENERAL_DV_INVALID/high/deterministic/True |
| B_ocr_clean | syn-42-00448 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_GENERAL_DV_INVALID/high/deterministic/True |
| C_ocr_degraded | syn-42-00448 | B4 | NENHUMA_EVIDENCIA_GERADA | 37.5 | LOW | BOLETO_GENERAL_DV_INVALID | BANCO_INVALIDO/low/deterministic/True; LINHA_DIGITAVEL_FORMATO_INCORRETO/high/deterministic/True |
| C_ocr_degraded | syn-42-00448 | B4 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_GENERAL_DV_INVALID | BOLETO_GENERAL_DV_INVALID/high/deterministic/True |
| B_ocr_clean | syn-42-00576 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00576 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00576 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00576 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00736 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00736 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00736 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| C_ocr_degraded | syn-42-00736 | P5 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 15.0 | LOW | PAYSLIP_CPF_INVALID | PAYSLIP_CPF_INVALID/medium/deterministic/True |
| B_ocr_clean | syn-42-00768 | B2,B1 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_AMOUNT_MISMATCH,BOLETO_DUE_DATE_MISMATCH | BOLETO_AMOUNT_MISMATCH/high/deterministic/True |
| B_ocr_clean | syn-42-00768 | B2,B1 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_AMOUNT_MISMATCH,BOLETO_DUE_DATE_MISMATCH | BOLETO_AMOUNT_MISMATCH/high/deterministic/True |
| C_ocr_degraded | syn-42-00768 | B2,B1 | NENHUMA_EVIDENCIA_GERADA | 37.5 | LOW | BOLETO_AMOUNT_MISMATCH,BOLETO_DUE_DATE_MISMATCH | BANCO_INVALIDO/low/deterministic/True; LINHA_DIGITAVEL_FORMATO_INCORRETO/high/deterministic/True |
| C_ocr_degraded | syn-42-00768 | B2,B1 | EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 30.0 | LOW | BOLETO_AMOUNT_MISMATCH,BOLETO_DUE_DATE_MISMATCH | BOLETO_AMOUNT_MISMATCH/high/deterministic/True |

| Classe | Ocorrências |
|---|---:|
| EVIDENCIA_GERADA_SCORE_INSUFICIENTE | 114 |
| NENHUMA_EVIDENCIA_GERADA | 23 |

## 4. Falhas restantes por tipo de adulteração

Somente `A_native`, naive/multi, código esperado ausente.

| Tipo | ID | Idioma | Layout | Campos ausentes | Campos errados | Score |
|---|---|---|---|---|---|---:|
| B1 | syn-42-00036 | es | A | valor_nominal | beneficiario | 3.0 |
| B1 | syn-42-00964 | en | D | valor_nominal,beneficiario | data_vencimento | 0.0 |
| B2 | syn-42-00157 | en | C | - | data_vencimento | 0.0 |
| B2 | syn-42-00541 | en | B | data_vencimento | - | 0.0 |
| B2 | syn-42-00665 | en | B | - | data_vencimento | 0.0 |
| P1 | syn-42-00961 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P1 | syn-42-00992 | pt | D | total_descontos,inss,fgts | - | 30.0 |
| P2 | syn-42-00955 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P3 | syn-42-00052 | es | A | - | - | 0.0 |
| P3 | syn-42-00826 | pt | A | - | - | 0.0 |
| P3 | syn-42-00915 | en | D | total_descontos,salario_liquido,inss,fgts,nome_funcionario | salario_bruto,periodo | 0.0 |
| P7 | syn-42-00955 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P7 | syn-42-00986 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P7 | syn-42-00989 | es | D | total_descontos,salario_liquido,irrf,fgts | - | 0.0 |
| P7 | syn-42-00995 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P7 | syn-42-00996 | pt | D | total_descontos,inss,fgts | - | 15.0 |
| P8 | syn-42-00968 | en | D | salario_bruto,total_descontos,salario_liquido,inss,fgts,nome_funcionario | periodo | 0.0 |

## 5. Cobertura dos campos-alvo

A_native, legítimos + adulterados.

| Tipo | Layout | Idioma | Campo | AUSENTE | ERRADO | OK |
|---|---|---|---|---:|---:|---:|
| boleto | A | es | valor_nominal | 34 | 0 | 0 |
| boleto | B | en | data_vencimento | 8 | 11 | 27 |
| boleto | B | en | data_vencimento | 8 | 11 | 27 |
| boleto | C | en | data_vencimento | 4 | 15 | 10 |
| boleto | C | en | data_vencimento | 4 | 15 | 10 |
| boleto | D | en | data_vencimento | 0 | 10 | 0 |
| boleto | D | en | valor_nominal | 10 | 0 | 0 |
| boleto | D | es | data_vencimento | 0 | 12 | 0 |
| boleto | D | es | valor_nominal | 12 | 0 | 0 |
| boleto | D | pt | data_vencimento | 0 | 20 | 0 |
| boleto | D | pt | valor_nominal | 20 | 0 | 0 |
| contracheque | D | en | fgts | 10 | 0 | 0 |
| contracheque | D | en | inss | 10 | 0 | 0 |
| contracheque | D | en | salario_bruto | 8 | 2 | 0 |
| contracheque | D | en | salario_bruto | 8 | 2 | 0 |
| contracheque | D | en | salario_liquido | 10 | 0 | 0 |
| contracheque | D | en | total_descontos | 10 | 0 | 0 |
| contracheque | D | es | fgts | 17 | 0 | 0 |
| contracheque | D | es | irrf | 17 | 0 | 0 |
| contracheque | D | es | salario_liquido | 17 | 0 | 0 |
| contracheque | D | es | total_descontos | 17 | 0 | 0 |
| contracheque | D | pt | fgts | 31 | 0 | 0 |
| contracheque | D | pt | inss | 31 | 0 | 0 |
| contracheque | D | pt | total_descontos | 31 | 0 | 0 |
