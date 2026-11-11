# Protocolo de holdout intocado — preparado, não executado

**Status:** preparado e congelado como protocolo; nenhum holdout foi gerado,
aberto ou avaliado. Este documento não altera features, modelo, C, threshold,
dados ou caminho de produção.

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

O artefato congelado está em
`data/ml/frozen/logistic_v2_1_d4100dc5.joblib`. Qualquer alteração de features,
C, threshold ou modelo invalida este protocolo e exige um novo holdout.

## 2. Desenho do holdout sintético

O holdout será gerado por uma versão **v3** do gerador, aprovada e commitada
antes da geração, com:

- novos pools de empresas, pessoas, beneficiários e empregadores;
- seed fixa **2027**;
- 1000 documentos;
- `lineage_id = document_id`; nenhuma linhagem, documento-base ou variante
  pode ser reutilizada de v1, v2 ou v2.1;
- todas as variantes de um documento no mesmo grupo de linhagem;
- todos os 1000 documentos são **holdout**; não há treino, validação ou
  seleção de modelo neste conjunto;
- interseção de IDs e linhagens com v1/v2/v2.1 deve ser **0**, verificada antes
  do selo.

Amostra OCR pré-registrada:

- todos os documentos fraudados naive/multi do holdout;
- 100 legítimos escolhidos pelo hash da linhagem (ordem lexicográfica), não pelo
  resultado do modelo;
- mesmos grupos de linhagem/split;
- variantes `scanned_clean`, `image_png`, `scanned_rot`, `scanned_blur`;
- N efetivo por tipo e path será reportado, sem ampliar amostra após ver
  resultados.

B6/B7/P4 serão avaliados em seção separada e não entram nos critérios
principais.

## 3. Comandos pre-registrados

Executar somente após aprovação explícita e implementação do gerador v3 e do
avaliador de holdout:

```powershell
poetry run python -m app.synthetic.build `
  --out ../data/holdout/v3_seed2027 `
  --seed 2027 --n-total 1000 --render 120 `
  --dataset-version holdout-v3 --generator-version v3

# Implementar sob aprovação separada:
poetry run python -m app.ml.evaluate_holdout `
  --model ../data/ml/frozen/logistic_v2_1_d4100dc5.joblib `
  --holdout ../data/holdout/v3_seed2027 `
  --threshold 0.809 `
  --out ../Back-end/docs/eval/holdout_result.md
```

O comando de avaliação não existe nesta fase; ele deve ser implementado antes
da execução, usando o mesmo `FEATURE_NAMES`, o threshold congelado e nenhuma
otimização.

## 4. Selo antes da avaliação

Antes de qualquer predição no holdout, gravar e commitar um arquivo pequeno:

`data/holdout/v3_seed2027/HOLDOUT_SEAL.json`

com:

- `generator_version`, `seed`, comando;
- `records_sha256`, `split_hashes`/`lineage_hashes`, `file_hashes`;
- `artifact_sha256` do modelo congelado;
- `feature_names_sha256`, `features_code_sha256`;
- `threshold`, `C`, commit do gerador, commit do avaliador, data/hora;
- confirmação de interseção zero com v1/v2/v2.1.

O holdout só pode ser aberto depois que o selo estiver commitado. Qualquer
avaliação anterior ao selo invalida o holdout.

## 5. Métricas e critérios de aceite

Primárias:

- PR-AUC positiva;
- recall positivo no threshold congelado 0,809;
- F1 positivo;
- taxa de falso positivo com IC 95% de Wilson;
- recall separado de naive e multi;
- N, TP, FN, FP e TN por path, idioma, layout e tipo.

Secundárias:

- ROC-AUC;
- Brier (somente para a probabilidade logística; não comparar Brier de
  Deterministic/Fusion como calibração);
- distribuição de scores por classe;
- matrizes de confusão.

Critério pré-registrado para avançar:

1. PR-AUC e F1 positivo devem superar **Fusion** e **Deterministic** no
   holdout;
2. o limite superior do IC 95% de FP deve ser **<= 5%**;
3. o recall naive e o recall multi não podem ser inferiores aos do Fusion;
4. nenhuma mudança de features, C, threshold ou modelo pode ocorrer após abrir
   o holdout;
5. se qualquer critério falhar, o modelo não é integrado e o resultado negativo
   é registrado.

O threshold **não** pode ser reotimizado no holdout. Uma recalibração exigiria
uma validação OCR/holdout separada e um novo teste independente.

## 6. Limitações do holdout sintético

- Mesmo com novas entidades e seed, o holdout sintético compartilha o gerador e
  suas famílias de regras; ele mede generalização dentro do gerador, não
  validade ecológica.
- Validação representativa em documentos reais/OOD depende de autorização,
  governança, privacidade e conjunto de referência próprios.
- B6/B7/P4 continuam fora da cobertura interna e exigem corroboração externa,
  assinatura/proveniência, forense ou revisão humana.
- Nenhum resultado deste protocolo deve ser apresentado como taxa real de
  fraude ou de falso positivo em produção.
