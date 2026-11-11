# Regras determinísticas de boleto e contracheque

Todas as regras abaixo são determinísticas, não usam LLM nem rede e são avaliadas pelo
`DeterministicRulesStage`, entre `ValidateStage` e `RiskStage`. Ausência de um campo
necessário faz a regra ser pulada e registrada em `metadata.validation.skipped_rules`.

## Extração de texto de PDF

O extrator central guarda `doc.page_count` antes de fechar o documento do
PyMuPDF. Um PDF válido não gera mais o warning `document closed` nem cai para os
métodos de fallback por causa desse erro; a cascata só avança quando o método
realmente falha.

## Status de OCR

| Status | Origem | Efeito no score |
|---|---|---|
| `completed` | OCR executado (Tesseract, Paddle ou serviço remoto) | usa `ocr_confidence` |
| `not_needed` | texto veio da camada nativa do PDF | nenhuma evidência `OCR_VERY_LOW`; confiança tratada como ausente |
| `empty` | OCR não encontrou texto útil | confiança tratada como ausente |
| `failed` | OCR indisponível | confiança tratada como ausente |

Quando `ExtractStage` lê texto nativo (`pymupdf`, `pdfplumber`, `pypdf` ou
`native_text`) e ainda não existe bloco `ocr`, grava
`metadata.ocr = {"status": "not_needed", "provider": "native_text"}`. O `RiskStage`
trata `failed`, `empty` e `not_needed` passando `ocr_confidence=None`, portanto
não emite `OCR_VERY_LOW` nem `OCR_MODERATE` para PDFs nativos ou sem OCR.

## Tabelas

| Tabela | Vigência | Fonte |
|---|---|---|
| `INSS_2026` | 2026-01-01 | Portaria Interministerial MPS/MF 13/2026 |
| `IRRF_2025_05` | 2025-05-01 | Tabela mensal do IRRF vigente desde maio/2025 |
| `IRRF_REDUCAO_2026` | 2026-01-01 | Lei 15.270/2025 |

Os valores monetários usam `Decimal`. O INSS é calculado de forma progressiva e
arredondado com `ROUND_HALF_UP` a duas casas no fim. Nos componentes do IRRF
(tabela e redução), o arredondamento a duas casas usa `ROUND_HALF_EVEN` para reproduzir
os valores oficiais dos exemplos; o resultado final é subtraído já em duas casas.

## Mitigação provisória de proveniência do OCR

Quando `metadata.ocr.status == "completed"` e o provider não é `native_text`,
o `DeterministicRulesStage` reduz em um nível a severidade das evidências
dependentes de leitura de dígitos/nomes listadas em
`OCR_SENSITIVE_CODES` (`app/services/validation/ocr_provenance.py`):
`critical→high`, `high→medium`, `medium→low`, `low→info`. A confiança não muda;
`metadata.ocr_uncertain = true` e `metadata.original_severity` registram a
decisão. A lista cobre códigos de boleto, linha digitável, banco, contracheque e
`CNPJ_INVALID_PATTERN`. É uma mitigação provisória até a corroboração por segunda
leitura.

## Banco

- Quando existe linha digitável (47 dígitos) ou código de barras (44), a
  validade do banco usa os três primeiros dígitos codificados. O código lido do
  texto só é usado na ausência da linha.
- `BANCO_INVALIDO`: `critical` apenas para `000` e `999`; `medium` para código
  numérico de três dígitos fora da lista; `high` para código não numérico.
- `BOLETO_BANK_MISMATCH` compara o banco codificado com candidatos impressos
  obtidos apenas pelo cabeçalho `\b(\d{3})\s*-\s*\d\b` (primeiras 15 linhas) e
  pelo rótulo de banco do texto. O código canônico derivado da linha nunca entra
  como candidato impresso. Sem candidato impresso, a regra é pulada e registrada
  como `missing_banco_impresso`.
- A lista `BANCOS_VALIDOS` foi completada com `003`, `004`, `041`, `070`, `085`,
  `136`, `218` e `323`.

## Política temporal e valor redondo

| Código | Severidade | Regra |
|---|---|---|
| `BOLETO_OVERDUE` | info | Vencimento entre 31 e 365 dias atrás |
| `BOLETO_VENCIDO` | info | Mesma janela, emitido pela varredura de texto do `boleto_analyzer` |
| `BOLETO_SEVERELY_OVERDUE` | low | Vencimento há mais de 365 dias |
| `DOCUMENT_EXPIRED` | info | Data de vencimento no passado (`RiskAnalyzer`) |
| `VALOR_REDONDO_SUSPEITO` | low | Valor múltiplo de R$ 100 na varredura de texto |
| `BOLETO_ROUND_AMOUNT` | low | Valor múltiplo de R$ 100 (`RiskAnalyzer`) |
| `ROUND_AMOUNT_SUSPICIOUS` | low | Valor múltiplo de R$ 100 (`ValidateStage`) |

Os limiares de detecção (30 e 365 dias; valor >= R$ 100 e múltiplo de 100) não
mudam. Para boleto, a data usada nas regras de atraso é o campo extraído
`data_vencimento` (ou `due_date`) quando existe; a varredura de datas do texto é
fallback apenas quando o campo está ausente. Contracheques, holerites e payslips
não geram `BOLETO_*` nem `DOCUMENT_EXPIRED` por vencimento.

## Boleto

| Código | Documento | Severidade | Descrição | Base / tolerância |
|---|---|---|---|---|
| `BOLETO_GENERAL_DV_INVALID` | boleto | critical | Dígito verificador geral do código de barras não confere. | FEBRABAN módulo 11, sem tolerância |
| `BOLETO_CURRENCY_CODE_INVALID` | boleto | medium | Código de moeda diferente de 9. | FEBRABAN código de barras |
| `BOLETO_AMOUNT_MISMATCH` | boleto | critical | Valor nominal impresso difere do valor codificado. | FEBRABAN, igualdade exata em `Decimal` |
| `BOLETO_DUE_DATE_MISMATCH` | boleto | high | Vencimento impresso difere do fator decodificado. | FEBRABAN fator de vencimento, igualdade de data |
| `BOLETO_DUE_DATE_UNRESOLVABLE` | boleto | low | Fator de vencimento fora da janela de datas plausíveis. | Janela de 3.000 dias no passado e 5.500 no futuro |
| `BOLETO_BANK_MISMATCH` | boleto | critical | Banco impresso difere do banco codificado. | FEBRABAN, sem tolerância |
| `BOLETO_BARCODE_MISMATCH` | boleto | high | Código de barras extraído difere do convertido da linha. | FEBRABAN, 44 dígitos |
| `BOLETO_ARRECADACAO_UNSUPPORTED` | boleto | info | Linha de arrecadação de 48 dígitos não é validada. | FEBRABAN/ABBC arrecadação |

Limitações do boleto:
- Linhas com tamanho diferente de 47 ou 48 não geram evidência nova; o formato já é
  coberto por `LINHA_DIGITAVEL_FORMATO_INCORRETO` no fluxo existente.
- DVs dos campos 1, 2 e 3 são calculados e expostos em `boleto_decoded`, mas não geram
  evidência, pois o `boleto_analyzer` existente já os avalia.
- Valor codificado zero é tratado como valor livre e não é comparado.
- Fator 0000 é tratado como sem vencimento.
- Quando o fator é ambíguo, nenhuma comparação de vencimento é feita.
- A janela de datas é configurável pelas constantes `WINDOW_PAST_DAYS` e
  `WINDOW_FUTURE_DAYS`.
- A base do fator é 1997-10-07. O fator 9586 resulta em 2024-01-05 pela fórmula
  FEBRABAN; o valor 2025-01-06 mencionado em um exemplo de teste não é reproduzível
  pela fórmula e foi mantido como divergência documentada.

## Contracheque

| Código | Documento | Severidade | Descrição | Base / tolerância |
|---|---|---|---|---|
| `PAYSLIP_NET_MISMATCH` | contracheque | critical ou medium | Líquido difere de proventos menos descontos. | Tolerância de R$ 0,02; acima de R$ 1,00 vira critical |
| `PAYSLIP_DEDUCTIONS_INCONSISTENT` | contracheque | high | Total de descontos menor que INSS + IRRF. | Tolerância de R$ 0,10 |
| `PAYSLIP_INSS_ABOVE_CEILING` | contracheque | critical | INSS impresso acima do teto. | Teto de R$ 7.786,02 e máximo de R$ 988,09 |
| `PAYSLIP_INSS_MISMATCH` | contracheque | medium, high ou low | INSS impresso difere do cálculo progressivo. | Tolerância de R$ 0,10; até R$ 5,00 medium, acima high; base presumida rebaixa uma severidade |
| `PAYSLIP_IRRF_MISMATCH` | contracheque | medium, high ou low | IRRF impresso não bate com nenhum candidato. | Tolerância de R$ 1,00; high se delta > R$ 50,00 e > 20% do esperado; dependentes presumidos rebaixam uma severidade |
| `PAYSLIP_FGTS_MISMATCH` | contracheque | medium | FGTS impresso não bate com 8%, 2% ou 11,2%. | Tolerância de R$ 0,10 |
| `PAYSLIP_BASE_EXCEEDS_GROSS` | contracheque | medium | Base de INSS ou FGTS maior que o bruto. | Tolerância de R$ 0,10 |
| `PAYSLIP_CPF_INVALID` | contracheque | high | Dígitos verificadores do CPF inválidos. | Módulo 11 CPF |
| `PAYSLIP_CNPJ_INVALID` | contracheque | high | Dígitos verificadores do CNPJ inválidos. | Módulo 11 CNPJ (validador existente) |
| `PAYSLIP_PERIOD_FUTURE` | contracheque | high | Competência posterior ao mês atual. | Sem tolerância |
| `PAYSLIP_PERIOD_BEFORE_ADMISSION` | contracheque | high | Competência anterior ao mês de admissão. | Sem tolerância |
| `PAYSLIP_TAX_TABLE_UNSUPPORTED` | contracheque | info | Competência sem tabela de INSS/IRRF suportada. | Regras de INSS e IRRF são puladas; aritmética continua |

Candidatos de IRRF:
- Base impressa, quando existir.
- Deduções legais: rendimento bruto − INSS impresso − dependentes × R$ 189,59.
- Desconto simplificado: rendimento bruto − R$ 607,20.
- A redução da Lei 15.270/2025 só é aplicada a partir de 01/2026 e usa o rendimento bruto,
  sem descontar INSS.

Limitações do contracheque:
- Se dependentes não existir, o cálculo usa 0 e a severidade do IRRF é rebaixada.
- Se a base de INSS não existir, usa o bruto e a severidade do INSS é rebaixada.
- O FGTS não é descontado do líquido.
- Competências fora das tabelas registradas não geram erro; geram `info` e pulam INSS/IRRF.
- Todos os valores de saída de `metadata.validation` são strings/JSON-safe.

## Como atualizar as tabelas a cada ano

1. Acrescente uma nova `InssTable` em `app/services/validation/tables.py` com
   `valid_from`, `source`, `verified_on`, faixas e teto.
2. Registre-a em `INSS_TABLES` pelo ano de competência.
3. Atualize `IRRF_TABLES` e `IRRF_REDUCTIONS` quando houver nova tabela ou nova lei.
4. Adicione os valores oficiais de conferência em `tests/unit/test_validation_tables_tax.py`.
5. Rode a suíte e confira `payslip_expected.tables` para garantir a versão usada.
