# HTTP API

The Express service defaults to `http://localhost:8000`. Configure browser origins with the comma-separated `WEB_ORIGINS` environment variable.

All request bodies are JSON. The `image` field is base64-encoded PNG data without a data-URL prefix.

## Endpoints

- `GET /api/health` returns `{ "status": "ok" }`.
- `POST /api/capacity` accepts `{ "image": "..." }` and returns image dimensions and maximum plaintext bytes.
- `POST /api/encode` accepts `{ "image": "...", "message": "...", "password": "..." }` and returns an `image/png` attachment.
- `POST /api/decode` accepts `{ "image": "...", "password": "..." }` and returns `{ "message": "..." }`.

## Request constraints

The JSON body is limited to 8 MB; the encoded PNG is limited to 5 MB and 4 megapixels; UTF-8 messages are limited to 1 MB; passwords are limited to 1,024 UTF-8 bytes. Malformed, truncated, corrupt, and non-PNG image input returns a sanitized `400` response.

The API limits each client to `RATE_LIMIT_PER_MINUTE` requests per minute (default `20`) before parsing JSON, returning `429` when exceeded. At most `MAX_CONCURRENT_JOBS` capacity, encode, and decode operations run at once (default `2`); excess work returns `503` with `Retry-After`. Both settings must be positive integers. Responses include `Cache-Control: no-store`. The API does not log request content or persist uploaded content.
