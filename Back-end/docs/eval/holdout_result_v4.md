# Holdout v4 — EXECUÇÃO OFICIAL INTERROMPIDA

**Status:** execução interrompida por exceção no avaliador, após o preflight
oficial e após a medição de evidências. Nenhum score Logistic, métrica,
matriz de confusão ou decisão de aceite foi produzido. O candidato **não foi
promovido** nesta rodada.

## 1. Preflight oficial

- Data/hora: `2026-11-11T23:01:37.041538+00:00`
- HEAD: `f3c3a6008ced331028e8c20b379ccb1e0c16f301`
- Selo: `docs/eval/holdout_seal_v4.json`
- SHA-256 do selo: `12977cde4cb67bb2453355b883516ecb9c3f4ca6ae55e8e2f86c55b611579cd4`
- Schema: `holdout-seal/2.0`
- SHA-256 do schema: `8bd2b7b738849deb578529277c1fa5ec460e8a482c5e59976399d89a4d04f6fb`
- Artefato: `d4100dc572d6238a9f819b078cca0ef50bb8ad04e046bd62bd8dd1325abea33e`

Todos os checks passaram:

- schema, avaliador, contrato, gerador e protocolo;
- records, manifest, arquivos e linhagens;
- amostra OCR e amostra primária;
- artefato, features e `features.py`;
- thresholds 0,809 / 0,5 / 0,4;
- commits e ambiente;
- interseção zero;
- ausência de resultado oficial anterior.

Preflight completo: `docs/eval/holdout_preflight_v4_official.json`  
SHA-256: `54c27e7964b3a7d64deadb53e314778f9620a5eec788314c39d662130ef7c166`

Nenhum modelo foi carregado durante o preflight.

## 2. Medição oficial de evidências

Comando executado uma única vez:

```powershell
poetry run python -m app.synthetic.evaluate `
  --out ../data/holdout/v4_seed2028/eval_run `
  --report ../data/holdout/v4_seed2028/eval_run/measurement.md `
  --dump ../data/holdout/v4_seed2028/eval_run/evidence_dump.jsonl `
  --native-limit 1000 --ocr-limit 1000 `
  --title "Holdout v4 - medicao oficial"
```

Resultado:

- código de retorno: **0**
- observações: **1368**
- native: 1000
- OCR: 368 chamadas (184 documentos × 2 variantes)
- dump SHA-256: `e423343db717e89ea491337cf2820bdd8c8ecf1b61a575e25959f44761dea6a7`
- log preservado: `docs/eval/holdout_v4_measurement.log`

A medição usa o pipeline/OCR e não calcula o score Logistic.

## 3. Falha na execução oficial do avaliador

Comando executado uma única vez:

```powershell
poetry run python -m app.ml.evaluate_holdout `
  --dump ../data/holdout/v4_seed2028/eval_run/evidence_dump.jsonl `
  --seal docs/eval/holdout_seal_v4.json `
  --model ../data/ml/frozen/logistic_v2_1_d4100dc5.joblib `
  --out docs/eval/holdout_result_v4.md
```

Código de retorno: **1**

Falha exata:

```text
File "D:\PaySentinelIQ\Back-end\app\ml\evaluate_holdout.py", line 503, in <module>
    main()
File "D:\PaySentinelIQ\Back-end\app\ml\evaluate_holdout.py", line 494, in main
    seal["threshold"],
    ~~~~^^^^^^^^^^^^^
KeyError: 'threshold'
```

O erro ocorre na montagem dos argumentos de `evaluate(...)`, depois do
`preflight_and_load` e antes de `evaluate` ser chamado. Portanto:

- não houve `predict_proba`;
- não houve score, métrica, matriz de confusão ou decisão de critério;
- não foi criado resultado oficial;
- o modelo congelado não foi alterado.

Log preservado: `docs/eval/holdout_v4_official_eval.log`  
SHA-256: `daabf82defb11f57551fbc26276c564cdfd3888e103637784fb9f777b3c5912b`

## 4. Consequência

- Execução oficial: **falhou**.
- Resultado oficial do holdout v4: **inexistente**.
- Candidato Logistic: **não promovido nesta rodada**.
- Não houve repetição da rodada, correção do avaliador após o selo, alteração
  de dados, modelo, features, C, threshold, baselines ou critérios.
- V0, FusionEngine, API, CanonicalPipeline, thresholds de produção e o
  artefato Logistic permanecem inalterados.
- 6C, Qwen, RAG e qualquer integração não foram iniciados.

Qualquer correção do avaliador ou nova tentativa exige novo protocolo e novo
holdout, com nova autorização humana.

## 5. Artefatos e hashes

| Artefato | SHA-256 |
|---|---|
| `docs/eval/holdout_preflight_v4_official.json` | `54c27e7964b3a7d64deadb53e314778f9620a5eec788314c39d662130ef7c166` |
| `docs/eval/holdout_seal_v4.json` | `12977cde4cb67bb2453355b883516ecb9c3f4ca6ae55e8e2f86c55b611579cd4` |
| dump de evidências | `e423343db717e89ea491337cf2820bdd8c8ecf1b61a575e25959f44761dea6a7` |
| `measurement.md` | `ffa31a7094a1c24d97a02c8f2823d1671487862a890b54b4d214a21683199213` |
| `measurement.log` | `6150fc04377df5ace96a0107c75bb2bd884a81193151fafd043ba0cf2e30a539` |
| `official_eval.log` | `daabf82defb11f57551fbc26276c564cdfd3888e103637784fb9f777b3c5912b` |

## 6. Limitações

O holdout v4 é sintético e não substitui validação representativa em documentos
reais/OOD. Nenhuma conclusão de desempenho pode ser tirada desta rodada.
