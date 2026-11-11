# Protocolo de holdout intocado — preparado, não avaliado

**Status:** holdout gerado e empacotado para verificação estrutural; **nenhuma
inferência, score, métrica ou matriz de confusão foi calculada**. O selo só pode
ser aberto em uma rodada posterior, após revisão humana.

## 1. Artefato e componentes congelados

| Componente | Valor |
|---|---|
| Modelo | LogisticRegression |
| C | 0.01 |
| Threshold | 0.809 |
| `class_weight` | `balanced` |
| Pré-processamento | `SimpleImputer(median)` + `StandardScaler` |
| SHA-256 do artefato | `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e` |
| SHA-256 das features ordenadas | `a240323638b438875ca94492b4d89e3bb7ebd410edde5f19dc059811d64070a4` |
| SHA-256 de `features.py` | `b14920d258e55014c1fafd07f66041218f6ddf61910c30545664a9a71753a708` |
| Dataset de treino | v2.1 |
| `records_sha256` de treino | `2a8f71d078d4a91efd2a86918991f82a41470601001f9b68d991d7f70e742663` |
| Commit do extrator | `ba79eaaca24271c5dc1e7d8a844e44a048ccd1e4` |
| Commit do código do modelo | `7d0fb416d26e51569ef415c12fb35d7829a180fb` |
| Commit do gerador/evaluator | `9ada588` (v3 + avaliador) |

O artefato congelado está em
`data/ml/frozen/logistic_v2_1_d4100dc5.joblib`. Qualquer alteração de features,
C, threshold ou modelo invalida este protocolo e exige um novo holdout.

## 2. Composição pré-registrada do v3

| Grupo | N |
|---|---:|
| Legítimos | 660 |
| Adulterados supervisionados | 280 |
| Especialistas (B6/B7/P4) | 60 |
| **Total** | **1000** |

Supervisionados: **20 por tipo** para B1–B5, B8, P1–P3, P5–P9 (14 tipos).
Especialistas: **20 por tipo** para B6, B7 e P4. Cada documento tem um único
tipo de adulteração.

- Idiomas: pt/es/en em rotação determinística.
- Layouts: A/B/C/D em rotação determinística; D usa `set2`.
- `lineage_id = document_id`.
- Nenhuma linhagem, documento-base ou variante de v1/v2/v2.1 é reutilizada.
- Interseção de IDs e entidades com v1/v2/v2.1 verificada em **0**.
- Todos os 1000 documentos têm `split="holdout"`; não há treino, validação ou
  seleção neste conjunto.

### Amostra OCR pré-registrada

- 8 documentos por tipo supervisionado: **112**.
- 8 documentos por tipo especialista: **24**.
- 48 legítimos: 16 por idioma, escolhidos por hash da linhagem.
- **Amostra total: 184**; **primária sem especialistas: 160** (112 fraudados +
  48 legítimos).
- Variantes: `scanned_clean` e `scanned_rot`.
- Seleção por `sha256(id:tipo:ocr)` e `sha256(id:idioma:legit:ocr)`, antes de
  qualquer inferência.
- Nenhuma chamada OCR é observação independente; a unidade é o documento.

## 3. Preparação versus abertura

Permitido antes do selo:

- gerar e empacotar documentos;
- verificar contagens, hashes, interseção de linhagem e estrutura de arquivos;
- registrar commits, versões de ambiente e configuração de OCR;
- escrever e commitar o selo.

Proibido antes do selo commitado:

- calcular scores, métricas, matrizes de confusão ou distribuições de score;
- inspecionar resultados para orientar ajustes;
- alterar features, C, threshold, modelo, gerador ou avaliador.

Qualquer alteração posterior ao selo invalida a rodada e exige outro holdout.

## 4. Avaliação futura — critérios sem ambiguidade

Cortes fixos:

- Deterministic: **0.5**.
- Fusion: **0.4**.
- Logistic: **0.809** (congelado; sem reotimização).

Cohorts primários, avaliados separadamente, sem pooling:

1. `native`: todos os 940 documentos não-especialistas (660 legítimos + 280
   supervisionados).
2. `B_ocr_clean`: 160 documentos primários (112 fraudados + 48 legítimos).
3. `C_ocr_degraded`: os mesmos 160 documentos, agregados por documento/path.

Especialistas B6/B7/P4 são seção separada e não entram no aceite principal.

### Critério de desempenho

Em **cada** cohort primário:

- PR-AUC do Logistic deve ser **estritamente maior** que a PR-AUC do
  Deterministic **e** que a PR-AUC do Fusion;
- F1 positivo no threshold congelado deve ser **estritamente maior** que o F1
  do Deterministic **e** que o F1 do Fusion.

“Superar as baselines” significa, portanto, superar **ambas**, separadamente,
em cada cohort. Não há pooling entre native, OCR limpo e OCR degradado.

### Critério de recall naive/multi

Em cada cohort:

- avaliar **agregado por categoria** (`naive` e `multi` separadamente), não por
  idioma/layout/tipo;
- usar estimativa pontual com margem de não inferioridade de **5 pontos
  percentuais**;
- exigir `recall_logistic >= recall_baseline - 0.05` para Deterministic e para
  Fusion, em cada categoria;
- relatar intervalo bootstrap 95% descritivo, sem trocar o critério por uma
  métrica mais favorável.

### Critério de falso positivo

Separadamente por cohort:

| Cohort | N legítimos mínimo | Cap do limite superior Wilson 95% |
|---|---:|---:|
| native | 30 | 5% |
| B_ocr_clean | 30 | 10% |
| C_ocr_degraded | 30 | 15% |

O critério usa o limite superior de Wilson, não apenas a estimativa pontual.
Se o N de legítimos for menor que 30, o cohort é **inconclusivo** e não pode ser
aprovado automaticamente.

### Estratos pequenos

- Cohort primário exige >= 30 positivos e >= 30 negativos para ser conclusivo.
- Idioma/layout/tipo com N < 10 por classe é **indicativo**, não entra no
  aceite e não pode ser apresentado como evidência robusta.
- Estrato inconclusivo nunca conta como aprovação.

### Decisão

A promoção exige que **todos** os cohorts primários sejam conclusivos e passem
em todos os critérios. Qualquer falha ou inconclusão encerra a promoção daquele
candidato nesta rodada. Mesmo o passe completo significa apenas
**elegibilidade para nova revisão humana**, nunca ativação automática. Uma nova
tentativa exige outro protocolo e outro holdout.

## 5. Métricas a reportar

Primárias:

- PR-AUC, ROC-AUC;
- F1, precision e recall positivos no threshold 0.809;
- TP/FN/FP/TN e matriz de confusão;
- recall agregado de `naive` e `multi`;
- FP por cohort com IC de Wilson;
- N, TP/FN e FP/TN por idioma, layout e tipo;
- ICs bootstrap por documento/linhagem, nunca por variante OCR.

Secundárias:

- Brier apenas para o Logistic; Brier de Deterministic/Fusion é apenas
  descritivo e não é comparação de calibração;
- distribuição de scores por classe;
- especialistas B6/B7/P4 separados;
- B8/P9 separando sinal aritmético de sinal forense.

## 6. Comandos e selo

Comandos pre-registrados:

```powershell
poetry run python -m app.synthetic.holdout `
  --out ../data/holdout/v3_seed2027 `
  --generator-commit 9ada588

# Somente após o selo commitado e nova autorização:
poetry run python -m app.synthetic.evaluate --out ../data/holdout/v3_seed2027 ...
poetry run python -m app.ml.evaluate_holdout `
  --dump ../data/holdout/v3_seed2027/eval/evidence_dump.jsonl `
  --seal ../docs/eval/holdout_seal.json `
  --model ../data/ml/frozen/logistic_v2_1_d4100dc5.joblib
```

O selo `docs/eval/holdout_seal.json` registra:

- hashes do dataset, manifest, records, arquivos e linhagens;
- SHA-256 do artefato, das features e de `features.py`;
- commits do gerador, avaliador, extrator e modelo;
- definições e cortes das baselines;
- configuração OCR (variantes, seleção, N, engine);
- versões de Python, scikit-learn, numpy, PyMuPDF, Pillow e joblib;
- critérios de aceite e a declaração de que nenhuma inferência foi executada.

O selo deve ser commitado antes de qualquer predição. O avaliador deve ser
testado somente em fixtures/smoke de desenvolvimento, nunca no holdout.

## 7. Limitações

- O holdout é sintético, gerado pelo mesmo projeto de gerador; mede
  generalização dentro dessa família, não validade ecológica.
- Validação em documentos reais/OOD exige autorização, governança e conjunto de
  referência próprios.
- B6/B7/P4 exigem corroboração externa, assinatura/proveniência, forense ou
  revisão humana.
- Nenhum resultado deste protocolo é taxa real de fraude ou de falso positivo
  em produção.
