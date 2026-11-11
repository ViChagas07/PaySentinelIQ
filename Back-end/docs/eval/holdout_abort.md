# Holdout v3 — ABORTADO NO PREFLIGHT

**Status:** abortado antes de qualquer inferência, score, predição ou métrica.
Nenhum resultado oficial foi produzido. `holdout_result.md` não foi gerado.

## 1. Preflight executado

Data/hora: `2026-11-11T22:21:09.918993+00:00`  
HEAD: `6ad8e3477ab40a2ab69feabfc16700bb04f836d0`  
Selo: `docs/eval/holdout_seal.json`  
SHA-256 do selo: `180c73548b020efda1a349da669b4353e351fbe331cec91134e50703aa13b224`

Checks de integridade e configuração:

| Check | Resultado |
|---|---|
| Selo existe | OK |
| Nenhum resultado anterior do holdout | OK |
| `records_sha256` | OK |
| `manifest_sha256` | OK |
| Todos os arquivos presentes | OK |
| Todos os hashes de arquivos | OK |
| `files_sha256` | OK |
| `lineage_hashes_sha256` | OK |
| Hash da amostra OCR | OK |
| Hash da amostra OCR primária | OK |
| SHA-256 do artefato congelado | OK |
| SHA-256 das features | OK |
| SHA-256 de `features.py` | OK |
| SHA-256 do protocolo | OK |
| SHA-256 do gerador v3 | OK |
| SHA-256 do avaliador | OK |
| Threshold Logistic = 0,809 | OK |
| Deterministic = 0,5 e Fusion = 0,4 | OK |
| Versões de ambiente | OK |
| HEAD descendente do selo e árvore selada limpa | OK |

Nenhum arquivo selado foi alterado. Nenhum modelo foi carregado; nenhum
documento do holdout foi pontuado.

## 2. Falha que determinou o aborto

A chamada oficial ao verificador congelado:

```python
from app.ml.evaluate_holdout import verify_seal
verify_seal(seal, model_path, dataset_manifest_path)
```

falhou com:

```text
KeyError: 'artifact_sha256'
```

Causa: incompatibilidade de schema entre o selo versionado e o verificador
congelado. O selo usa chaves aninhadas; o verificador espera chaves planas:

| Verificador espera | Selo contém |
|---|---|
| `seal["artifact_sha256"]` | `seal["artifact"]["sha256"]` |
| `seal["dataset_manifest_sha256"]` | `seal["dataset"]["manifest_sha256"]` |
| `seal["feature_names_sha256"]` | `seal["features"]["names_sha256"]` |
| `seal["threshold"]` | `seal["artifact"]["threshold"]` |

A falha ocorre antes de qualquer hashing de inferência ou de carregar o
classificador. É uma divergência de contrato entre componentes selados, não
uma divergência de integridade dos dados.

## 3. Decisão

- **Preflight: reprovado.**
- **Execução oficial: não realizada.**
- **Resultado oficial: inexistente.**
- **Candidato Logistic: não promovido nesta rodada.**
- Não houve segunda tentativa, contorno, alteração do selo, do avaliador, do
  holdout ou do modelo.
- V0, FusionEngine, API, thresholds e caminho de produção permanecem
  inalterados.
- 6C, Qwen, RAG, banco vetorial e qualquer integração não foram iniciados.

Qualquer tentativa de corrigir o verificador ou o schema do selo invalida esta
rodada e exige novo protocolo e novo holdout, com nova autorização humana.

## 4. Artefatos

- Preflight detalhado: `docs/eval/holdout_preflight.json`
- Este relatório: `docs/eval/holdout_abort.md`
- Selo preservado: `docs/eval/holdout_seal.json`
- Holdout preservado: `data/holdout/v3_seed2027/`
- Nenhum `docs/eval/holdout_result.md`

## 5. Limitações

O holdout é sintético e não substitui validação representativa em documentos
reais/OOD. Mesmo que uma rodada futura seja aprovada, o resultado será apenas
elegibilidade para nova revisão humana, nunca ativação automática.
