# BANCO_INVALIDO em documentos legítimos — antes da 5B

Fonte: `docs/eval/evidence_dump_before.jsonl` (medicao antes, seed 42).

Dos 73 `BANCO_INVALIDO` disparados em legitimas, **todos** vieram da leitura de
um numero que nao e o codigo de banco: fragmentos de CNPJ, valor do documento,
datas, CPF do pagador e agencia. Nenhum veio de um codigo de banco realmente
impresso no cabecalho. A lista `BANCOS_VALIDOS` incompleta nao explica nenhum
caso observado; ela e endurecida na 5B.4c de forma preventiva.

Exemplos verificados:
- `syn-42-00005`: `BANCO_INVALIDO: codigo 206` veio de `Document Amount: 2068.79`.
- `syn-42-00416`: codigo 801 veio de um fragmento numerico do texto.
- `syn-42-00780`: codigo 323 veio de `Document Amount: 3235.98` (o banco real era 341).

| Codigo lido | Ocorrencias | Causa |
|---|---:|---|
| 166 | 5 | Leitura errada de fragmento numerico |
| 213 | 5 | Leitura errada de fragmento numerico |
| 497 | 5 | Leitura errada de fragmento numerico |
| 566 | 5 | Leitura errada de fragmento numerico |
| 801 | 5 | Leitura errada de fragmento numerico |
| 720 | 2 | Leitura errada de fragmento numerico |
| 113 | 1 | Leitura errada de fragmento numerico |
| 124 | 1 | Leitura errada de fragmento numerico |
| 130 | 1 | Leitura errada de fragmento numerico |
| 132 | 1 | Leitura errada de fragmento numerico |
| 134 | 1 | Leitura errada de fragmento numerico |
| 143 | 1 | Leitura errada de fragmento numerico |
| 165 | 1 | Leitura errada de fragmento numerico |
| 172 | 1 | Leitura errada de fragmento numerico |
| 175 | 1 | Leitura errada de fragmento numerico |
| 184 | 1 | Leitura errada de fragmento numerico |
| 196 | 1 | Leitura errada de fragmento numerico |
| 206 | 1 | Leitura errada de fragmento numerico |
| 227 | 1 | Leitura errada de fragmento numerico |
| 230 | 1 | Leitura errada de fragmento numerico |
| 234 | 1 | Leitura errada de fragmento numerico |
| 240 | 1 | Leitura errada de fragmento numerico |
| 301 | 1 | Leitura errada de fragmento numerico |
| 315 | 1 | Leitura errada de fragmento numerico |
| 323 | 1 | Leitura errada de fragmento numerico |
| 358 | 1 | Leitura errada de fragmento numerico |
| 372 | 1 | Leitura errada de fragmento numerico |
| 397 | 1 | Leitura errada de fragmento numerico |
| 410 | 1 | Leitura errada de fragmento numerico |
| 442 | 1 | Leitura errada de fragmento numerico |
| 462 | 1 | Leitura errada de fragmento numerico |
| 472 | 1 | Leitura errada de fragmento numerico |
| 475 | 1 | Leitura errada de fragmento numerico |
| 478 | 1 | Leitura errada de fragmento numerico |
| 526 | 1 | Leitura errada de fragmento numerico |
| 528 | 1 | Leitura errada de fragmento numerico |
| 547 | 1 | Leitura errada de fragmento numerico |
| 560 | 1 | Leitura errada de fragmento numerico |
| 593 | 1 | Leitura errada de fragmento numerico |
| 649 | 1 | Leitura errada de fragmento numerico |
| 658 | 1 | Leitura errada de fragmento numerico |
| 660 | 1 | Leitura errada de fragmento numerico |
| 670 | 1 | Leitura errada de fragmento numerico |
| 677 | 1 | Leitura errada de fragmento numerico |
| 704 | 1 | Leitura errada de fragmento numerico |
| 728 | 1 | Leitura errada de fragmento numerico |
| 729 | 1 | Leitura errada de fragmento numerico |
| 779 | 1 | Leitura errada de fragmento numerico |
| 782 | 1 | Leitura errada de fragmento numerico |
| 804 | 1 | Leitura errada de fragmento numerico |
| 810 | 1 | Leitura errada de fragmento numerico |
| 899 | 1 | Leitura errada de fragmento numerico |

Observacao: a linha digitavel ja contem o banco codificado nos tres primeiros
digitos. A correcao da 5B.4b passa a usar esse valor como autoridade e deixa a
leitura do texto apenas para quando a linha nao existir.
