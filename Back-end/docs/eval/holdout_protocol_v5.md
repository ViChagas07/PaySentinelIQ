# Protocolo do holdout v5 — preparado, não avaliado

**Status:** protocolo aprovado para preparação. Nenhum scoring, inferência ou
métrica foi executado no holdout v5. v3 e v4 permanecem encerrados e
preservados.

## 1. Identidade e componentes congelados

| Item | Valor |
|---|---|
| Dataset | `holdout-v5` |
| Gerador | `v5` |
| Seed | **2029** |
| Documentos | 1000 |
| Novos pools | empresas, pessoas e cargos exclusivos do v5 |
| Linhagem | `lineage_id = document_id`; sem reuso de v1/v2/v2.1/v3/v4 |
| Schema | `holdout-seal/2.0` |
| SHA-256 do schema | `8bd2b7b738849deb578529277c1fa5ec460e8a482c5e59976399d89a4d04f6fb` |
| Commit do gerador | `4cf4dee` |
| SHA-256 de `holdout_v5.py` | `123d2975c7600e9482b5f20a9906e873cb2f04a71e15d756c9094a0056e8342e` |
| Commit do avaliador/contrato | `4cf4dee` |
| SHA-256 de `evaluate_holdout.py` | `4bc9989ecaa2763957063cf528fdc56e5e6e8d5ac1bd6804ee4f4a504da0e8b7` |
| SHA-256 de `holdout_contract.py` | `547fb13ac6ff15764ec290f5bb515f15a465c98b1c03fff847927ff9a6d6852a` |
| Artefato | `data/ml/frozen/logistic_v2_1_d4100dc5.joblib` |
| SHA-256 do artefato | `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e` |
| Threshold Logistic | `0.809` |
| Deterministic | `0.5` |
| Fusion | `0.4` |
| Commit do extrator | `ba79eaaca24271c5dc1e7d8a844e44a048ccd1e4` |
| Commit do modelo | `7d0fb416d26e51569ef415c12fb35d7829a180fb` |

## 2. Smoke test obrigatório antes do selo

O caminho oficial da CLI deve ser comprovado em fixture de desenvolvimento,
nunca em v3, v4 ou v5:

```powershell
poetry run pytest -q `
  tests/unit/test_ml_holdout_cli.py::test_real_cli_end_to_end_on_fixture -s
```

Evidência exigida no selo:

- resultado `1 passed`;
- log `docs/eval/holdout_v5_smoke_test.log`
  (SHA-256 `93526c8d1d342569abfe54477bd730408bf1c1f01442adce349765f034eb3836`);
- execução real de `main()`/CLI, preflight, loader, `evaluate`, baselines,
  agregação OCR, reconciliação TP+FN/FP+TN, critérios e escrita MD/JSON;
- nenhuma fixture apontando para v3/v4/v5.

Se o smoke test falhar, o selo v5 não pode ser criado.

## 3. Composição pré-registrada

| Grupo | N |
|---|---:|
| Legítimos | 660 |
| Supervisionados | 280 (20 por tipo: B1–B5, B8, P1–P3, P5–P9) |
| Especialistas | 60 (20 por tipo: B6, B7, P4) |
| **Total** | **1000** |

Layouts A/B/C/D e idiomas pt/es/en em rotação determinística. Todos com
`split="holdout"`. Interseção de IDs e entidades com v1/v2/v2.1/v3/v4 deve ser
**0**, verificada antes do selo.

Amostra OCR: 8 por tipo supervisionado (112) + 8 por tipo especialista (24) +
48 legítimos (16 por idioma) = **184**; **160 primários**. Variantes
`scanned_clean` e `scanned_rot`; unidade documental/linhagem.

## 4. Critérios — idênticos ao v4

Cohorts separados: `native` (940 primários), `B_ocr_clean` (160) e
`C_ocr_degraded` (160).

Em cada cohort:

1. PR-AUC Logistic estritamente maior que Deterministic **e** Fusion.
2. F1 positivo no threshold congelado estritamente maior que Deterministic
   **e** Fusion.
3. Recall `naive` e `multi` separadamente: `recall_Logistic >=
   recall_baseline - 0.05` contra cada baseline.
4. FP com limite superior de Wilson 95%: native <= 5%; clean <= 10%;
   degraded <= 15%.

Cohort com < 30 positivos ou < 30 negativos é inconclusivo. Estratos por
idioma/layout/tipo com < 10 por classe são indicativos e não participam do
aceite. Todos os cohorts conclusivos e aprovados são necessários; qualquer
falha/inconclusão encerra a promoção. Aprovação integral significa apenas
elegibilidade para nova revisão humana.

## 5. CLI e contrato

O avaliador deve:

- ler o selo bruto somente pela camada `holdout_contract`;
- validar schema, hashes, thresholds e commits antes de carregar o modelo;
- produzir `HoldoutConfig` imutável;
- passar essa configuração a `preflight_and_load`, `evaluate` e ao relatório;
- não acessar `seal["..."]` fora do contrato;
- gravar Markdown e JSON estruturado;
- rejeitar schema antigo, campos ausentes, tipos incorretos, hashes,
  thresholds e commits divergentes sem carregar o modelo.

## 6. Preparação, selo e abertura

Comandos previstos:

```powershell
poetry run python -m app.synthetic.holdout_v5 `
  --out ../data/holdout/v5_seed2029 `
  --generator-commit 4cf4dee

# Somente após o selo commitado e nova autorização:
poetry run python -m app.synthetic.evaluate --out ../data/holdout/v5_seed2029 ...
poetry run python -m app.ml.evaluate_holdout `
  --dump ../data/holdout/v5_seed2029/eval/evidence_dump.jsonl `
  --seal ../docs/eval/holdout_seal_v5.json `
  --model ../data/ml/frozen/logistic_v2_1_d4100dc5.joblib `
  --out ../docs/eval/holdout_result_v5.md
```

O selo v5 deve incluir schema/hash, hashes de dataset, manifest, records,
arquivos, linhagens, amostras, artefato, features, contrato, avaliador,
gerador, protocolo, baselines, ambiente, commits, interseção zero, resultado
do smoke test e declaração de ausência de scoring.

## 7. Limitações

Holdout sintético; não substitui validação real/OOD. B6/B7/P4 continuam fora da
cobertura. Nada aqui autoriza ativação, integração, 6C, Qwen, RAG ou banco
vetorial.
