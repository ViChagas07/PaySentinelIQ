# Atribuição de falsos positivos — depois da Fase 5B

Análise somente leitura sobre o dump de evidências da medição correspondente.

Categorias de causa raiz: OCR_QUALITY, DATE_OVERDUE, BANK, LINHA_FORMAT, RULE_BOLETO, RULE_PAYSLIP, ROUND_AMOUNT, OTHER.

## a) Códigos de evidência disparados em documentos legítimos

| Caminho | Código | Documentos | Taxa sobre legítimos | Severidade máxima | Estágio |
|---|---|---:|---:|---|---|
| A_native | DOCUMENT_EXPIRED | 186 | 26.8% | info | RiskStage |
| A_native | BOLETO_OVERDUE | 170 | 24.5% | info | ValidateStage |
| A_native | BOLETO_VENCIDO | 170 | 24.5% | info | ValidateStage |
| A_native | BOLETO_DUE_DATE_MISMATCH | 29 | 4.2% | high | DeterministicRulesStage |
| A_native | BOLETO_ROUND_AMOUNT | 25 | 3.6% | low | RiskStage |
| A_native | ROUND_AMOUNT_SUSPICIOUS | 25 | 3.6% | low | ValidateStage |
| A_native | VALOR_REDONDO_SUSPEITO | 24 | 3.5% | low | ValidateStage |
| A_native | PAYSLIP_IRRF_MISMATCH | 11 | 1.6% | high | DeterministicRulesStage |
| B_ocr_clean | BOLETO_OVERDUE | 30 | 33.3% | info | ValidateStage |
| B_ocr_clean | BOLETO_VENCIDO | 30 | 33.3% | info | ValidateStage |
| B_ocr_clean | DOCUMENT_EXPIRED | 30 | 33.3% | info | RiskStage |
| B_ocr_clean | BOLETO_ROUND_AMOUNT | 4 | 4.4% | low | RiskStage |
| B_ocr_clean | ROUND_AMOUNT_SUSPICIOUS | 4 | 4.4% | low | ValidateStage |
| B_ocr_clean | VALOR_REDONDO_SUSPEITO | 4 | 4.4% | low | ValidateStage |
| B_ocr_clean | LINHA_DIGITAVEL_FORMATO_INCORRETO | 1 | 1.1% | high | ValidateStage |
| C_ocr_degraded | BOLETO_OVERDUE | 30 | 33.3% | info | ValidateStage |
| C_ocr_degraded | BOLETO_VENCIDO | 30 | 33.3% | info | ValidateStage |
| C_ocr_degraded | DOCUMENT_EXPIRED | 30 | 33.3% | info | RiskStage |
| C_ocr_degraded | LINHA_DIGITAVEL_FORMATO_INCORRETO | 29 | 32.2% | high | ValidateStage |
| C_ocr_degraded | BANCO_INVALIDO | 5 | 5.6% | low | ValidateStage |
| C_ocr_degraded | BOLETO_ROUND_AMOUNT | 4 | 4.4% | low | RiskStage |
| C_ocr_degraded | ROUND_AMOUNT_SUSPICIOUS | 4 | 4.4% | low | ValidateStage |
| C_ocr_degraded | VALOR_REDONDO_SUSPEITO | 4 | 4.4% | low | ValidateStage |
| C_ocr_degraded | PAYSLIP_INSS_MISMATCH | 1 | 1.1% | low | DeterministicRulesStage |
| C_ocr_degraded | PAYSLIP_IRRF_MISMATCH | 1 | 1.1% | medium | DeterministicRulesStage |

## b) Conjunto decisivo dos legítimos com score >= 70

| Caminho | Documento | Score | Conjunto mínimo decisivo | Categoria |
|---|---|---:|---|---|

### Contagem por categoria

| Caminho | Categoria | Legítimos |
|---|---|---:|

### Contagem por idioma

| Caminho | Dimensão | Categoria | Legítimos |
|---|---|---|---:|

### Contagem por layout

| Caminho | Dimensão | Categoria | Legítimos |
|---|---|---|---:|

### Contagem por tipo de documento

| Caminho | Dimensão | Categoria | Legítimos |
|---|---|---|---:|

## c) Causa das evidências BOLETO_* e PAYSLIP_* em legítimos

| Caminho | Código | Causa | Evidências | Exemplos (ids) | Detalhe |
|---|---|---|---:|---|---|
| A_native | BOLETO_DUE_DATE_MISMATCH | ERRADO:29 | 29 | syn-42-00905, syn-42-00908, syn-42-00913 | '27/11/2026' vs '2026-12-17' |
| A_native | BOLETO_OVERDUE | DIVERGENCIA_REAL:156, ERRADO:14 | 170 | syn-42-00002, syn-42-00016, syn-42-00034 | '09/05/2026' vs '2026-05-09' |
| A_native | BOLETO_ROUND_AMOUNT | DIVERGENCIA_REAL:25 | 25 | syn-42-00034, syn-42-00045, syn-42-00079 | 8800.0 vs '8800' |
| A_native | BOLETO_VENCIDO | DIVERGENCIA_REAL:156, ERRADO:14 | 170 | syn-42-00002, syn-42-00016, syn-42-00034 | '09/05/2026' vs '2026-05-09' |
| A_native | PAYSLIP_IRRF_MISMATCH | DIVERGENCIA_REAL:11 | 11 | syn-42-00909, syn-42-00910, syn-42-00918 | 643.4 vs '643.40' |
| B_ocr_clean | BOLETO_OVERDUE | DIVERGENCIA_REAL:30 | 30 | syn-42-00016, syn-42-00112, syn-42-00192 | '21/09/2026' vs '2026-09-21' |
| B_ocr_clean | BOLETO_ROUND_AMOUNT | DIVERGENCIA_REAL:4 | 4 | syn-42-00528, syn-42-00560 | 6300.0 vs '6300' |
| B_ocr_clean | BOLETO_VENCIDO | DIVERGENCIA_REAL:30 | 30 | syn-42-00016, syn-42-00112, syn-42-00192 | '21/09/2026' vs '2026-09-21' |
| C_ocr_degraded | BOLETO_OVERDUE | DIVERGENCIA_REAL:30 | 30 | syn-42-00016, syn-42-00112, syn-42-00192 | '21/09/2026' vs '2026-09-21' |
| C_ocr_degraded | BOLETO_ROUND_AMOUNT | DIVERGENCIA_REAL:4 | 4 | syn-42-00528, syn-42-00560 | 6300.0 vs '6300' |
| C_ocr_degraded | BOLETO_VENCIDO | DIVERGENCIA_REAL:30 | 30 | syn-42-00016, syn-42-00112, syn-42-00192 | '21/09/2026' vs '2026-09-21' |
| C_ocr_degraded | PAYSLIP_INSS_MISMATCH | DIVERGENCIA_REAL:1 | 1 | syn-42-00048 | 745.36 vs '745.36' |
| C_ocr_degraded | PAYSLIP_IRRF_MISMATCH | ERRADO:1 | 1 | syn-42-00608 | 344.45 vs '844.45' |

## d) Cobertura do código de banco impresso em boletos legítimos

| Caminho | Boletos legítimos | Com candidato impresso | Com candidato distinto da linha | % dos boletos |
|---|---:|---:|---:|---:|
| A_native | 360 | 360 | 0 | 0.0% |
| B_ocr_clean | 56 | 56 | 0 | 0.0% |
| C_ocr_degraded | 56 | 56 | 0 | 0.0% |
