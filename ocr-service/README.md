# PaySentinelIQ OCR Service

Serviço isolado de OCR via HTTP. O PaddleOCR é o motor primário (CPU, `lang=latin`,
classificação de orientação ativa) e o Tesseract (`por+spa+eng`) é o fallback. O serviço
não extrai texto nativo de PDF; essa etapa continua no backend.

## Endpoints

- `GET /health` — 200 enquanto o processo estiver de pé; não carrega modelos.
- `GET /ready` — JSON `{"tesseract": bool, "paddle": bool, "default_engine": "..."}`.
  Tesseract é considerado pronto quando o binário existe e os idiomas `por`,
  `spa` e `eng` estão instalados. Paddle é considerado pronto depois da
  inicialização. HTTP 200 se ao menos um motor estiver pronto; 503 se nenhum.
  `default_engine` é `auto`, ou `tesseract` quando `OCR_SERVICE_FORCE_FALLBACK=1`.
- `POST /ocr` — multipart `file` (PDF/PNG/JPEG), `dpi`, `max_pages` e `engine`
  opcionais. `engine` aceita `auto` (padrão), `paddle` (sem fallback) ou `tesseract`
  (não inicializa o Paddle). Retorna `text`, `pages[]`, `confidence`, `provider`,
  `processing_time_seconds` e `metadata` com valores string.

Se `OCR_SERVICE_API_KEY` estiver definida, envie o header `X-OCR-Key`.

## Variáveis

| Variável | Padrão | Descrição |
|---|---:|---|
| `OCR_SERVICE_MAX_MB` | 25 | Tamanho máximo do arquivo |
| `OCR_SERVICE_MAX_PAGES` | 10 | Máximo de páginas; acima disso retorna 422 |
| `OCR_SERVICE_DPI` | 300 | DPI da rasterização de PDF |
| `OCR_SERVICE_API_KEY` | vazio | Chave opcional |
| `OCR_SERVICE_FORCE_FALLBACK` | 0 | `1` força Tesseract; inofensiva no padrão |

## Docker

```powershell
docker build -t psy-ocr-service ./ocr-service
docker run --rm -p 8010:8010 psy-ocr-service
```

No Compose local, o serviço sobe como `ocr` e o backend o acessa em
`http://ocr:8010`.

## Testes

```powershell
poetry run pytest ../ocr-service/tests
```
