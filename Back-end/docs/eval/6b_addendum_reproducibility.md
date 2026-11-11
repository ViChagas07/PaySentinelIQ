# 6B — Adendo de reprodutibilidade, comparabilidade e interpretação

Este adendo não altera features, C, threshold, modelo, dados, FusionEngine, API
ou caminho de produção. O artefato candidato foi congelado e o protocolo de
holdout foi preparado, mas **não executado**.

## 1. Fechamento documental de 6A e preservação

Os ajustes documentais pendentes de 6A estão fechados:

- `docs/eval/manifests/v1.json`, `v2.json`, `v2.1.json` e `6a3_sample.json`
  registram comando, seed, splits, hashes, versões e commits.
- `6a0_audit.md`, `6a1_generator_versions.md`, `6a2r_review.md`,
  `6a3_sample_plan.md`, `6a3_ocr_expanded.md`, `6a4_policy_shadow.md` e
  `6a5_report.md` estão versionados.
- `test_iid` e `test_shift` estão documentados como desenvolvimento/avaliação,
  não holdout intocado.
- Relatórios antigos de 5B e 6A não foram reescritos.
- O golden não foi regenerado.

Preservação verificada:

| Conjunto | SHA-256 de `records.jsonl` |
|---|---|
| v1 | `ba422a618832e257d05f17ab8dd5f9998c586a1b28484fab0229cab4029c88fc` |
| v2 | `e737753e1c7cc87c212cbc26ae3698db0def0b3ec4e54bf22fa69ba7ff1024f5` |
| v2.1 | `2a8f71d078d4a91efd2a86918991f82a41470601001f9b68d991d7f70e742663` |

Golden: **42 documentos, 0,98 MB**, `manifest.json` SHA-256
`21e2c08a9af3e07868a9f35fedb8437e26d01b1237c18863f64b97b4ee6d92a9`;
hash agregado do diretório (51 arquivos):
`b4f999d735aa95b13d597477db80823b7ce505d20b035207f1cf08a9ee039718`.

## 2. Seleção de C, threshold e congelamento

### Grade e objetivo

- Grade de `C`: `0.01, 0.1, 1.0, 10.0`.
- Objetivo: maior **PR-AUC positiva em `val`**.
- Desempate: menor `C` (a implementação só substitui quando o valor é
  estritamente maior; a grade é percorrida em ordem crescente).
- Threshold: candidatos = scores únicos de `val` arredondados em 4 casas;
  objetivo = maior **F1 da classe positiva** em `val`.
- Desempate do threshold: menor threshold (mesma regra de atualização
  estritamente maior).
- `C=0.01` e `threshold=0.809` foram escolhidos apenas em `val`.
- Nenhuma escolha usou `test_iid`, `test_shift` ou os caminhos OCR. A avaliação
  desses conjuntos ocorre depois de `choose_c` e `choose_threshold`.

### Congelamento

O artefato candidato foi copiado para
`data/ml/frozen/logistic_v2_1_d4100dc5.joblib` e registrado em
`docs/eval/ml_artifact_freeze.json`:

| Item | Valor |
|---|---|
| SHA-256 do artefato | `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e` |
| Tamanho | 6.369 bytes |
| Dataset | v2.1 |
| `records_sha256` | `2a8f71d078d4a91efd2a86918991f82a41470601001f9b68d991d7f70e742663` |
| SHA-256 de `manifest.json` v2.1 | `d0f39943b36a715369b0e3a8f8616d1440cbe9d31aac8bb11cca2781c97bb2f2` |
| SHA-256 das features ordenadas | `a240323638b438875ca94492b4d89e3bb7ebd410edde5f19dc059811d64070a4` |
| SHA-256 de `app/ml/features.py` | `b14920d258e55014c1fafd07f66041218f6ddf61910c30545664a9a71753a708` |
| Commit do extrator | `ba79eaaca24271c5dc1e7d8a844e44a048ccd1e4` |
| Commit do código do modelo | `7d0fb416d26e51569ef415c12fb35d7829a180fb` |

## 3. Comparabilidade das baselines

| Score | Transformação | ROC/PR | Ponto de corte da matriz | Brier |
|---|---|---|---|---|
| Dummy | `predict_proba` da prior | score contínuo trivial | 0,5 | Probabilidade trivial; não é baseline de calibração útil |
| Deterministic | `min(1, max(confirmed_material, confirmed_critical))`, binário 0/1 | apenas dois pontos de operação | 0,5 | Brier de score binário, **não** probabilidade calibrada |
| Fusion | `dump.score / 100` | score contínuo 0–1 | 0,4 (MEDIUM atual) | Brier de score heurístico, **não** comparável como calibração |
| Logistic | `predict_proba` do Logistic | score contínuo 0–1 | 0,809 congelado | Brier de probabilidade do modelo |

Portanto, o Brier do Deterministic/Fusion não deve ser lido como comparação
direta de calibração. A comparação de calibração válida é apenas entre
probabilidades logísticas e a taxa observada.

## 4. Avaliação OCR — esclarecimentos

- “Externa” significa **externa ao domínio native de treino**, não holdout
  independente.
- O modelo foi treinado somente em `native/train`.
- Os 106 documentos OCR não-especialistas avaliados têm **0 interseção com
  train/val**; todos os 106 vêm de `test_iid`/`test_shift` do dataset v2.1.
- Os 6 documentos especialistas (B6/B7/P4) foram excluídos do conjunto
  supervisionado.
- As variantes de um mesmo documento estão no mesmo split e foram agregadas
  por documento/path; não são observações independentes.
- O threshold 0,809 foi congelado no native/val e **não foi otimizado no OCR**.

### Matrizes de confusão no threshold congelado

| Path | N | TP | FN | FP | TN | Recall | Precision | F1 | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B_ocr_clean | 106 | 26 | 40 | 0 | 40 | 0,394 | 1,000 | 0,565 | 0,0847 |
| C_ocr_degraded | 106 | 27 | 39 | 0 | 40 | 0,409 | 1,000 | 0,581 | 0,0998 |

Recall por classe OCR:

| Path | naive | multi |
|---|---:|---:|
| B_ocr_clean | 0,188 (6/32) | 0,944 (17/18) |
| C_ocr_degraded | 0,250 (8/32) | 0,833 (15/18) |

### Distribuição dos scores por classe

| Path | Classe | N | Média | Desvio | Mín. | Q25 | Mediana | Q75 | Máx. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B_ocr_clean | legítimo | 40 | 0,107 | 0,075 | 0,040 | 0,071 | 0,082 | 0,115 | 0,326 |
| B_ocr_clean | fraudado | 66 | 0,699 | 0,187 | 0,342 | 0,566 | 0,654 | 0,891 | 0,991 |
| C_ocr_degraded | legítimo | 40 | 0,199 | 0,139 | 0,068 | 0,081 | 0,182 | 0,287 | 0,655 |
| C_ocr_degraded | fraudado | 66 | 0,714 | 0,207 | 0,267 | 0,572 | 0,723 | 0,907 | 0,991 |

### Reconciliação dos denominadores OCR

| Item | N |
|---|---:|
| Amostra 6A.3 total | 112 |
| Fraudados na amostra | 72 |
| Legítimos na amostra | 40 |
| Especialistas removidos do conjunto supervisionado | 6 |
| — B6 | 1 |
| — B7 | 2 |
| — P4 | 3 |
| **Avaliação externa 6B (não-especialistas)** | **106** |
| — fraudados | 66 |
| — legítimos | 40 |

Os 106 IDs externos têm **0 interseção com train/val** e **106/106** vêm de
`test_iid`/`test_shift`. Cada documento tem 4 variantes OCR, mas a unidade é o
documento: as variantes foram agregadas e não contam como observações
independentes. Por isso a avaliação externa tem N=106, não 112 e não 424.

Uma recalibração ou mudança de threshold no OCR exigiria uma validação OCR
separada e outro teste independente; não foi feita.

## 5. Denominadores, células pequenas e incerteza

### Native `test_iid` — Logistic, threshold 0,809

| Idioma | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| en | 10 | 10 | 0 | 0 | 31 | 1,000 |
| es | 15 | 15 | 0 | 0 | 35 | 1,000 |
| pt | 14 | 13 | 1 | 0 | 43 | 0,929 |

| Layout | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| A | 8 | 7 | 1 | 0 | 36 | 0,875 (indicativo) |
| B | 12 | 12 | 0 | 0 | 39 | 1,000 |
| C | 19 | 19 | 0 | 0 | 34 | 1,000 |

| Tipo | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| boleto | 16 | 16 | 0 | 0 | 62 | 1,000 |
| contracheque | 23 | 22 | 1 | 0 | 47 | 0,957 |

### Native `test_shift` — Logistic, threshold 0,809

| Idioma | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| en | 6 | 5 | 1 | 0 | 12 | 0,833 (indicativo) |
| es | 7 | 7 | 0 | 0 | 21 | 1,000 (indicativo) |
| pt | 14 | 13 | 1 | 0 | 36 | 0,929 |

| Layout | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| D | 27 | 25 | 2 | 0 | 69 | 0,926 |

| Tipo | N fraudes | TP | FN | FP | TN | Recall |
|---|---:|---:|---:|---:|---:|---:|
| boleto | 5 | 5 | 0 | 0 | 35 | 1,000 (indicativo) |
| contracheque | 22 | 20 | 2 | 0 | 34 | 0,909 |

Células com N < 10 estão marcadas como indicativas.

### Intervalos de confiança bootstrap (2.000 reamostragens, seed 2026)

| Split | Métrica | Estimativa | IC 95% |
|---|---|---:|---|
| test_iid | Precision positiva | 1,000 | [1,000; 1,000] |
| test_iid | Recall positivo | 0,974 | [0,917; 1,000] |
| test_iid | F1 positivo | 0,987 | [0,957; 1,000] |
| test_iid | PR-AUC | 1,000 | [1,000; 1,000] |
| test_iid | ROC-AUC | 1,000 | [1,000; 1,000] |
| test_shift | Precision positiva | 1,000 | [1,000; 1,000] |
| test_shift | Recall positivo | 0,926 | [0,815; 1,000] |
| test_shift | F1 positivo | 0,962 | [0,898; 1,000] |
| test_shift | PR-AUC | 1,000 | [1,000; 1,000] |
| test_shift | ROC-AUC | 1,000 | [1,000; 1,000] |

### Zero falsos positivos

Foram **0 FP em 178 legítimos** somando `test_iid` e `test_shift`. Isso não
significa taxa real de FP igual a zero; o limite superior de Wilson 95% para
0/178 é **2,11%**.

## 6. Vazamento e interpretação

- Os testes de tokens proibidos e invariância ao gabarito são necessários, mas
  não provam ausência de vazamento semântico.
- O agrupamento atual cobre `document_id` e variantes do mesmo documento. Não
  existe linhagem documental sintética além do ID; o protocolo de holdout exige
  que documento-base, linhagem e variantes sejam agrupados explicitamente.
- O modelo consome saídas das próprias regras. O resultado demonstra
  **combinação e ponderação desses sinais no gerador sintético avaliado**, não
  descoberta de um sinal de fraude independente.
- `class_weight="balanced"` e a prevalência artificial dos splits fazem com que
  as probabilidades logísticas brutas **não** sejam probabilidade real de
  fraude.
- B6/B7/P4 continuam fora da cobertura; B8/P9 têm sinal aritmético, mas o sinal
  forense de metadados desaparece no OCR.

## 7. Decisão e próxima ação

- V0, FusionEngine, API e thresholds de produção **permanecem inalterados**.
- O Logistic fica **congelado como candidato experimental**, não escolhido para
  produção.
- Não recomendo tentar resgatar o IsolationForest nos mesmos testes; ele não
  acrescentou sinal.
- Os conjuntos atuais **não devem mais ser apresentados como evidência final
  independente**.
- Próxima ação segura: preparar e congelar um protocolo de holdout intocado,
  sem executá-lo. O protocolo está em `docs/eval/holdout_protocol.md`.
- Mesmo um holdout sintético intocado não substitui validação representativa em
  documentos reais/OOD, que exige autorização e governança próprias.
