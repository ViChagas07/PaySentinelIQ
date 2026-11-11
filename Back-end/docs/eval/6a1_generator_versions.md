# 6A.1 — Versionamento do gerador e do dataset

## v1 — congelado para comparações históricas

- Caminho: `data/synthetic/v1/`
- Versão do dataset: `v1`
- Versão do gerador: `v1-legacy`
- Seed: `42`; documentos: `1000`; renderizados: `60`
- Splits: train 600, val 150, test_iid 150, test_shift 100
- SHA-256 de `records.jsonl`:
  `ba422a618832e257d05f17ab8dd5f9998c586a1b28484fab0229cab4029c88fc`
- Metadados: `data/synthetic/v1/VERSION.json`
- Dump histórico da 5B preservado em
  `data/synthetic/v1/eval/evidence_dump.jsonl`.
- Relatórios antigos (`synthetic_before_5b.md`, `synthetic_after_5b.md`,
  `fp_attribution_before.md`, `fp_attribution_after.md`,
  `policy_simulation_before.md`, `policy_simulation_after.md`) não foram
  reescritos.

## v2 — artefatos de codificação corrigidos

- Caminho: `data/synthetic/v2/`
- Versão do dataset: `v2`
- Versão do gerador: `v2`
- Gerado em: `2026-11-11`
- Seed: `42`; documentos: `1000`; renderizados: `60`
- Splits: train 600, val 150, test_iid 150, test_shift 100
- SHA-256 de `records.jsonl`:
  `e737753e1c7cc87c212cbc26ae3698db0def0b3ec4e54bf22fa69ba7ff1024f5`
- Hashes por split:
  - train: `e04b54a939ac1bcee925f6504d281f6b8e6fa9c52ef32c9238cba96e41beeb08`
  - val: `e743ceb84a568d7abcda87d9cb2474f621fdea4ff3cd3f418ed1de080241099d`
  - test_iid: `d04a12635010784a4b666e100de188729c58e26f6d3102ef0d8b555348d829ff`
  - test_shift: `ec39e6fe0f86fdfda6ccb86cd6182e35f959ee83a6e04b61ea0f63702d7e21f5`
- Hashes dos arquivos renderizados: `data/synthetic/v2/manifest.json`
  (`file_hashes`).

### Correções do gerador

1. **Mojibake restante**: `app/synthetic/values.py` (55 linhas),
   `app/synthetic/records.py` (rótulo `CNPJ do Beneficiário`) e
   `app/synthetic/dataset.py` (README do golden). Não restam `Ã`, `Â`,
   `U+FFFD` nem soft hyphen (`U+00AD`) nesses arquivos.
2. **P3 sem efeito**: quando o IRRF original era `0.00`, o tamper P3
   reaplicava zero. Agora, nesse caso, aplica delta material de `123,45` e
   mantém `total_descontos`/`salario_liquido` coerentes.
3. **Texto estruturado e gabarito**: o texto desenhado usa os mesmos rótulos
   corrigidos; `page_text`, `fields` e `to_dict()` continuam derivados da
   mesma estrutura.

### Coerência verificada

- `tests/unit/test_synthetic_generator_v2.py` verifica ausência de mojibake,
  coerência de rótulos/campos e presença de `dataset_version`,
  `generator_version`, seed, splits, `records_sha256` e `split_hashes`.
- O golden **não foi regenerado** nesta fase.
- A comparação 6A.2 usa somente v2 (antes/depois); v1 permanece apenas como
  histórico da 5B.
