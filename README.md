# Secure Image Steganography

**Author:** Lavkush Prasad

**Version:** 2.0.0

An educational project for encrypting text with AES-256-GCM and embedding it in PNG RGB channel bits. It includes a Python CLI and a React web interface backed by a stateless Express API.

## Features

- PNG-only LSB encoding with capacity validation.
- AES-256-GCM authenticated encryption and PBKDF2-HMAC-SHA256 key derivation (600,000 iterations).
- Fresh random salt and nonce for each message.
- Shared binary format between the Python CLI and Node API.
- React UI for hiding and extracting messages.
- Bounded API requests, rate limiting, same-origin configuration, and no request-body logging.
- No database, upload directory, or intentional server-side file persistence.

## Python CLI

Requirements: Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m stegano.cli encode cover.png secret.png
python -m stegano.cli decode secret.png
python -m stegano.cli capacity cover.png
python -m pytest -q
```

The CLI prompts for the password and message. Its output PNG is written to the path you choose.

## Run the web app locally

Requirements: Node.js 20+ and npm.

Terminal 1:

```powershell
cd backend
npm ci
npm start
```

Terminal 2:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`). The frontend calls the API at `http://localhost:8000` by default. Set `VITE_API_BASE_URL` in `frontend/.env` to use another API URL. Set `WEB_ORIGINS` in `backend/.env` to a comma-separated allowlist of exact browser origins.

Run API tests with `cd backend; npm test`; build the UI with `cd frontend; npm run build`.

## Deploy

### Render API

This repository includes `render.yaml`. Create a Render Blueprint from the repository, then set `WEB_ORIGINS` to the exact deployed Vercel site origin (for example `https://your-project.vercel.app`). Render supplies `PORT`.

### Vercel frontend

Import the repository into Vercel and set the project root directory to `frontend`. Configure this environment variable:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

Redeploy the frontend after changing environment variables. The API only allows browser origins listed in `WEB_ORIGINS`.

## API

The API accepts JSON requests with a base64-encoded PNG in the `image` field:

- `GET /api/health`
- `POST /api/capacity` with `{ "image": "..." }`
- `POST /api/encode` with `{ "image": "...", "message": "...", "password": "..." }`; returns a PNG download.
- `POST /api/decode` with `{ "image": "...", "password": "..." }`; returns `{ "message": "..." }`.

Limits: 8 MB JSON request body, 5 MB encoded PNG, 4 megapixels, 1 MB UTF-8 message, and 1,024 UTF-8 password bytes. Requests are processed in memory; the API does not use a database, disk-backed upload middleware, or application-level content logging. Responses use `Cache-Control: no-store`; request references are released when the response ends.

## Privacy and security limits

- “Zero data retention” here means the application does not intentionally persist request content. The hosting provider may retain operational metadata such as IP addresses and request timing according to its own policy.
- Node, Python, the image libraries, and the operating system may make internal copies. Garbage-collected runtimes cannot guarantee immediate physical erasure of passwords or plaintext from memory. Do not use this hosted demo for high-risk secrets.
- Use HTTPS and a trusted hosting provider. Anyone operating the server can potentially inspect data while it is being processed.
- This is not a guarantee of steganographic undetectability. LSB data can be detected; resizing, filtering, screenshots, and lossy conversion can destroy it.
- Use a strong, unique password. There is no password recovery. The web UI keeps a recovered message visible until you clear it or leave the page.

## Attribution

This enhanced version builds on the original LSB project: <https://github.com/lavkushprasad93/Steganography>.
