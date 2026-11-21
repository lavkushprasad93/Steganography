# Secure Image Steganography

**Author:** Lavkush Prasad

**Version:** 2.1.0

An educational project that encrypts text with AES-256-GCM and embeds it in PNG RGB channel bits. The Python core is organized as an installable `src/` package with a CLI; the existing React frontend and Express API remain separate.

## Features

- PNG-only LSB encoding with image and capacity validation.
- AES-256-GCM authenticated encryption and PBKDF2-HMAC-SHA256 key derivation (600,000 iterations).
- Fresh random salt and nonce per message; the complete payload header is authenticated.
- Python and Node implementations share the same versioned binary format.
- React UI, stateless Express API, and Python command-line interface.
- Automated Python/Node tests and GitHub Actions checks.

## Install the Python package

Requirements: Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Python CLI

```powershell
python -m secure_steganography encode cover.png secret.png
python -m secure_steganography encode cover.png secret.png --message-file message.txt
python -m secure_steganography decode secret.png --output recovered.txt
python -m secure_steganography capacity cover.png
```

Encoding requires a password of at least 12 Unicode characters and prompts twice for confirmation. Unless supplied with `--message` or `--message-file`, it asks for the message interactively. Decoding prompts once; previously encoded messages with shorter passwords remain readable. Use `--output` to save recovered UTF-8 text to a file. Existing output files are not overwritten unless `--force` is supplied, and input/output paths must differ. The capacity command reports the exact maximum plaintext byte count. The legacy `python LSB_LP.py ...` launcher and `stegano` console command remain available.

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

Open the Vite URL (usually `http://localhost:5173`). Set `VITE_API_BASE_URL` in `frontend/.env` to select the API URL. Set `WEB_ORIGINS` in `backend/.env` to a comma-separated allowlist of exact browser origins.

Run Python tests and lint with `python -m pytest -q` and `ruff check src tests`. Run API tests with `cd backend; npm test`; build the UI with `cd frontend; npm run build`.
<!-- 
## Deploy

### Render API

This repository includes `render.yaml`. Create a Render Blueprint, then set `WEB_ORIGINS` to the exact deployed Vercel site origin. Render supplies `PORT`.

### Vercel frontend

Import the repository into Vercel with project root `frontend` and set:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

The API only allows browser origins listed in `WEB_ORIGINS`.
-->

## Project layout

- `src/secure_steganography/`: Python package, separated into algorithms, cryptography, image validation, core encoding/decoding, services, and CLI.
- `tests/`: Python unit, integration, and security tests.
- `backend/`: Express API and Node implementation of the shared PNG format.
- `frontend/`: React/Vite user interface.
- `docs/`: architecture, algorithm, API, security, and user documentation.
- `.github/workflows/tests.yml`: Python, Node API, and frontend build checks.

## Limits and privacy

The hosted API accepts JSON requests up to 8 MB, PNGs up to 5 MB and 4 megapixels, messages up to 1 MB, and passwords up to 1,024 UTF-8 bytes. Web requests are processed in memory; the application does not intentionally persist request content. Hosting providers may retain operational metadata, and garbage-collected runtimes cannot guarantee immediate physical memory erasure. Avoid using the hosted demo for high-risk secrets.

LSB embedding is not undetectable. Resizing, filtering, screenshots, and lossy conversion can destroy the payload. Use a strong, unique password; there is no password recovery.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Algorithms and payload format](docs/ALGORITHMS.md)
- [HTTP API](docs/API.md)
- [Security and data handling](docs/SECURITY.md)
- [User guide](docs/USER_GUIDE.md)

## Attribution

This enhanced version builds on the original LSB project: <https://github.com/lavkushprasad93/Steganography>.
