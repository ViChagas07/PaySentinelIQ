# Upload / Ingress Production Checklist

This checklist is for the deployment proxy/ingress in front of the API.
It is **not** applied by the application and was **not** configured in this
repository. Values below are requirements/recommendations, not load-test
results.

## Application-level limits already enforced

| Layer | Limit | Behaviour |
|---|---|---|
| Upload file | 10 MiB (`MAX_UPLOAD_SIZE_MB`) | File-level validation returns 413 |
| Multipart request body | 12 MiB (`MAX_UPLOAD_SIZE_MB` + 2 MiB overhead) | Path-scoped ASGI middleware returns 413 before multipart parsing |
| PDF pages | 10 (`OCR_MAX_PAGES`) | 422 |
| PDF page size/area | 5000 pt per side / 10,000,000 pt² | 422 |
| Image dimensions/pixels | 10,000 px per side / 25,000,000 px | 422 |
| OCR remote call | `OCR_SERVICE_TIMEOUT` (default 120 s) | 503 `ocr_timeout` / `ocr_unavailable` |
| Canonical pipeline | Runs in `asyncio.to_thread` | Client cancellation stops persistence; the worker thread is not killed |

Upload paths: `POST /api/documents/analyze` and
`POST /api/verifications/upload`.

## Proxy / ingress requirements

- [ ] Enforce a request body limit of **12 MiB** for upload paths, matching the
      application cap plus multipart overhead. Do not set it below 12 MiB for
      these paths unless the application cap is lowered first.
- [ ] Enforce a reasonable body-read timeout (for example 30 s) so a slow
      upload cannot hold a connection indefinitely. The application does not
      implement a network read timeout.
- [ ] Set an upstream/connect timeout compatible with the slowest allowed
      analysis. Remote OCR can use up to 120 s; the legacy/current pipeline can
      also wait on local OCR. Do not silently set an upstream timeout shorter
      than the application's expected processing window.
- [ ] Set a response/write timeout. A client that disconnects must not leave
      the ingress retrying the upload.
- [ ] Limit concurrent connections and per-client request rate. The
      application does not provide a distributed DoS protection layer.
- [ ] Preserve/forward `X-Correlation-ID` on 5xx responses. The application
      generates the ID when the client does not supply a trusted one; do not
      overwrite it with an internal trace ID that is not returned to the client.
- [ ] Configure the 413 response consistently (JSON body, no automatic retry).
      Ensure CORS headers are preserved on 413/5xx responses.
- [ ] Do not retry non-idempotent analysis requests automatically; retries can
      duplicate documents and alerts.
- [ ] Configure log redaction at the ingress for query strings, authorization
      headers and multipart bodies. The application never logs raw document
      bytes or credentials.

## Timeout/cancellation map

| Stage | Current mechanism | Can the server kill the work? |
|---|---|---|
| Request body reception | ASGI middleware counts actual bytes | Yes, rejects at 12 MiB; network read timeout is proxy responsibility |
| Upload validation | Bounded bytes + `asyncio.to_thread` | Yes for cancellation of the await; local CPU work is bounded by PR-05 limits |
| Remote OCR | httpx timeout + `asyncio.wait_for` when the provider advertises hard-timeout support | Yes, the async HTTP request is cancelled |
| Local Tesseract/Paddle OCR | Synchronous CPU/subprocess inside async provider | **No** — the provider is not hard-timeout capable; it continues until return |
| Canonical pipeline | `asyncio.to_thread` | **No hard kill** — client cancellation stops persistence, thread continues |
| LLM background enrichment | Daemon thread, fire-and-forget | **No** — intentionally asynchronous; results may arrive after the response |
| LLM sync comparison | Caller waits up to 60 s | Caller returns; the worker thread continues |
| Legacy document pipeline | Async route; OCR may block | No hard OCR kill; failed operation returns explicit failure and compensates uploaded storage |
| S3 upload/download | boto3 client defaults | No explicit per-operation override in the application |
| Database | Pool timeout 30 s | No per-query timeout configured in the application |

This means a client-side timeout is **not** proof that the server stopped
OCR, LLM or pipeline work. Proxy/ingress timeouts are additionally required.

## Error/status contract

- Anonymous request with an otherwise valid upload: **401**, no business work.
- File/request too large: **413**, no OCR/LLM/storage/database effect.
- Unsupported or mismatched type: **415**, no effect.
- Empty/malformed/truncated or over page/pixel limits: **400/422**, no effect.
- OCR timeout/unavailable: **503**, no persistence, no `persistence_status`.
- OCR invalid response: **502**, no persistence.
- Insufficient/empty OCR evidence: **422** `analysis_inconclusive`, no persistence.
- Unexpected analysis error: **500** generic with correlation ID; no raw
  exception, SQL, paths, stack trace or document content.
- Legacy pipeline failure: HTTP 200 with `status="failed"` (existing
  contract), generic message, correlation ID, no `s3_key`/`presigned_url`.

## Not covered by this checklist

- Antivirus/malware scanning and sandboxing.
- Recursive inspection of embedded PDF images.
- Real PostgreSQL/S3 or load tests.
- Railway configuration changes.
