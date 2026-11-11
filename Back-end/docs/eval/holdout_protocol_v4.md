# Protocolo do holdout v4 — preparado, não avaliado

**Status:** novo protocolo aprovado para preparação. Nenhum scoring, inferência
ou métrica foi executado no holdout v4. O holdout v3 permanece encerrado,
preservado e não reutilizável.

## 1. Identidade

| Item | Valor |
|---|---|
| Dataset | `holdout-v4` |
| Gerador | `v4` |
| Seed | **2028** |
| Documentos | 1000 |
| Novos pools | empresas, pessoas e cargos exclusivos do v4 |
| Linhagem | `lineage_id = document_id`; sem reuso de v1/v2/v2.1/v3 |
| Schema do selo | `holdout-seal/2.0` |
| Schema | `docs/eval/holdout_seal.schema.json` |
| SHA-256 do schema | `8bd2b7b738849deb578529277c1fa5ec460e8a482c5e59976399d89a4d04f6fb` |
| Commit do gerador v4 | `54b2eca` |
| SHA-256 de `holdout_v4.py` | `fafcd44b9584b9c73eeb17d1c469bb8924fc4a21a9ec5db8741d7a9e1c153bb4` |
| Commit do avaliador | `54b2eca` |
| SHA-256 de `evaluate_holdout.py` | `7be693a5f5013883acb4a88aa8ea78e62fb3f0fa10ec7861a51e71adbcbaf5ca` |
| SHA-256 de `holdout_contract.py` | `6ccc6a2133c70403c2a7a61af404f38c10908b78e430452b3eb8036b27080b1b` |
| Artefato | `data/ml/frozen/logistic_v2_1_d4100dc5.joblib` |
| SHA-256 do artefato | `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e` |
| Threshold Logistic | `0.809` |
| Deterministic | `0.5` |
| Fusion | `0.4` |

O artefato, features, C e threshold permanecem congelados. O contrato
canônico está em `holdout-seal/2.0`; selos antigos são rejeitados antes de
qualquer acesso a campos individuais ou carregamento de modelo.

## 2. Composição pré-registrada

| Grupo | N |
|---|---:|
| Legítimos | 660 |
| Supervisionados | 280 (20 por tipo: B1–B5, B8, P1–P3, P5–P9) |
| Especialistas | 60 (20 por tipo: B6, B7, P4) |
| **Total** | **1000** |

Layouts A/B/C/D e idiomas pt/es/en em rotação determinística. Todos com
`split="holdout"`. Interseção de IDs e entidades com v1/v2/v2.1/v3 deve ser
**0**, verificada antes do selo.

### Amostra OCR

- 8 por tipo supervisionado: 112.
- 8 por tipo especialista: 24.
- 48 legítimos (16 por idioma), por hash da linhagem.
- Total 184; primária sem especialistas 160.
- Variantes `scanned_clean` e `scanned_rot`.
- Unidade de avaliação: documento/linhagem, não chamada OCR ou variante.

## 3. Critérios — idênticos aos aprovados

Cohorts separados, sem pooling: `native` (940 primários), `B_ocr_clean` (160) e
`C_ocr_degraded` (160).

Em cada cohort:

1. PR-AUC do Logistic estritamente maior que Deterministic **e** Fusion.
2. F1 positivo no threshold congelado estritamente maior que Deterministic
   **e** Fusion.
3. Recall `naive` e `multi` separadamente: `recall_Logistic >=
   recall_baseline - 0.05` contra cada baseline.
4. FP com limite superior de Wilson 95%: native <= 5%; clean <= 10%;
   degraded <= 15%.

Cohort com < 30 positivos ou < 30 negativos é inconclusivo. Estratos por
idioma/layout/tipo com < 10 por classe são indicativos e não participam do
aceite. A promoção exige todos os cohorts conclusivos e aprovados; qualquer
falha/inconclusão encerra a promoção. Aprovação integral significa apenas
elegibilidade para nova revisão humana.

## 4. Preparação e selo

Comandos previstos:

```powershell
poetry run python -m app.synthetic.holdout_v4 `
  --out ../data/holdout/v4_seed2028 `
  --generator-commit 54b2eca

# Somente após o selo commitado e nova autorização:
poetry run python -m app.synthetic.evaluate --out ../data/holdout/v4_seed2028 ...
poetry run python -m app.ml.evaluate_holdout `
  --dump ../data/holdout/v4_seed2028/eval/evidence_dump.jsonl `
  --seal ../docs/eval/holdout_seal_v4.json `
  --model ../data/ml/frozen/logistic_v2_1_d4100dc5.joblib `
  --out ../docs/eval/holdout_result_v4.md
```

O selo v4 deve incluir:

- `schema_version = holdout-seal/2.0` e `schema_sha256`;
- hashes do dataset, manifest, records, arquivos e linhagens;
- hashes do artefato, features e `features.py`;
- hashes do gerador, avaliador, protocolo e extrator, com commits;
- baselines e cortes;
- configuração OCR e denominadores;
- versões de ambiente;
- verificação de interseção zero;
- declaração de que nenhum scoring foi executado antes do selo.

O avaliador valida o schema, o hash do schema, hashes, thresholds e commits
antes de carregar o modelo. Falha de schema/hash/commit é controlada e não
pode chamar inferência.

## 5. Limitações

O holdout é sintético, gerado pelo mesmo projeto de gerador; mede
generalização dentro dessa família, não validade ecológica. Validação em
documentos reais/OOD exige autorização e governança próprias. B6/B7/P4
continuam fora da cobertura interna.

Nada neste protocolo autoriza ativação, integração, 6C, Qwen, RAG ou banco
vetorial.
