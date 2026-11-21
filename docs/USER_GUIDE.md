# User guide

## Install and run the Python CLI

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m secure_steganography encode cover.png hidden.png
python -m secure_steganography encode cover.png hidden.png --message-file message.txt
python -m secure_steganography decode hidden.png --output recovered.txt
python -m secure_steganography capacity cover.png
```

Encoding requires at least 12 Unicode characters in the new password, prompts twice, and asks for confirmation before writing. Supply `--message` for a command-line message or `--message-file` for UTF-8 text. Extraction prompts once and continues to accept shorter passwords used by existing images; use `--output` to write the recovered text to a file. Existing output files are preserved unless `--force` is provided, and input/output paths must differ. Capacity reports the exact maximum plaintext bytes supported by the image; choose a PNG with enough capacity for your message.

## Run the web interface

Start the Express service from `backend/` with `npm ci` and `npm start`. Start the React app from `frontend/` with `npm ci` and `npm run dev`. Configure `WEB_ORIGINS` and `VITE_API_BASE_URL` for deployed origins as described in the README.

The web UI downloads the encoded PNG and displays recovered text only for the current page session. Use its Clear button or leave the page when finished.
