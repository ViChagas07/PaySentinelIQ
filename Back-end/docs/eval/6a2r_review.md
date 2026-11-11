# 6A.2R — Revisão curta

## Preservação

- `data/synthetic/v1/` permanece congelado e não foi regenerado.
- `data/synthetic/v2/` permanece com os dumps `evidence_dump_before_6a2.jsonl` e
  `evidence_dump_after_6a2.jsonl`.
- Relatórios antigos da 5B e da 6A.2 não foram reescritos.
- Golden não foi regenerado.

## v2.1 — apenas semântica do P3

- Caminho: `data/synthetic/v2.1/`
- `dataset_version`: `v2.1`; `generator_version`: `v2.1`
- Seed 42; 1000 documentos; 60 renderizados; splits 600/150/150/100
- `records_sha256`:
  `2a8f71d078d4a91efd2a86918991f82a41470601001f9b68d991d7f70e742663`
- Hashes por split:
  - train: `cc04c4455b1473d9f76266d3f6a8996ca0831e75cca9a9b5f3927bce3e15e1b3`
  - val: `e743ceb84a568d7abcda87d9cb2474f621fdea4ff3cd3f418ed1de080241099d`
  - test_iid: `ef4f7a2930f41e487a4d3432c774107bcbe488488ee069227c33f448800b1883`
  - test_shift: `0e07e2c48f42755c9ab7f098bc778ed0b70ed9a53e7a2f689ea5ca418185efad`
- Arquivos renderizados e hashes: `data/synthetic/v2.1/manifest.json`.

### P3

O gerador agora regenera os insumos salariais do documento-base até que o IRRF
original seja maior que zero e só então aplica “IRRF zerado”, recalculando
`total_descontos` e `salario_liquido`. Não existe mais o delta artificial de
123,45. Se o IRRF original continuar zero, o gerador falha explicitamente em vez
de produzir um no-op silencioso.

Verificação em v2.1: **13/13 documentos P3 detectados**; nenhum no-op.

### Datas

- `pt`/`es`: `dd/mm` é o formato do locale.
- `en`/locale desconhecido com dia e mês <= 12: ambíguo; o campo não alimenta
  regras de vencimento.
- Data válida apenas como `MM/DD` em documento `pt`/`es` (ex.: `02/13/2026`) é
  marcada como `data_vencimento_locale_inconsistent=true`, não é exportada como
  `data_vencimento`/`due_date` e não alimenta mismatch/atraso.
- Não foi criada nova evidência de fraude nem alterado score por esse motivo.

## Contagens finais (v2.1, caminho A_native, legítimos)

| Evidência | Antes 6A.2 | v2.1 |
|---|---:|---:|
| `BOLETO_DUE_DATE_MISMATCH` | 29 | **0** |
| `PAYSLIP_IRRF_MISMATCH` | 11 | **0** |
| Falsos positivos >= 70 | 0 | **0** |
| Falsos positivos >= 40 | 2 | **0** |

O `6a2r_v2_1.md` usa o mesmo dataset v2.1 e o mesmo pipeline; não mistura v1,
v2 ou v2.1 no mesmo comparativo.

## Reclassificação dos splits

Os conjuntos atuais são **dados de desenvolvimento/avaliação**. Eles já
orientaram correções de extração e regra, portanto `test_iid` e `test_shift`
não são holdout intocado. Nenhum novo holdout final foi criado ou avaliado
neste checkpoint.

## Reconciliação do aumento de 9 testes (718 → 727)

| Origem | Testes |
|---|---:|
| `test_extraction_6a2.py` | +5 |
| `test_synthetic_generator_v2.py` | +3 |
| novo caso parametrizado `01/02/2026/en` em `test_extraction_numeric_dates.py` | +1 |
| **Total** | **+9** |

A 6A.2R acrescenta mais 4 testes de revisão (data ambígua sem fallback legado,
inconsistência de locale, vencimento nativo válido e P3 não no-op). A 6A.4
acrescenta 5 testes de política. Total final do checkpoint: **736 passed,
2 failed, 11 skipped** (727 + 4 + 5).
