# User guide

## Install and run the Python CLI

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m secure_steganography encode cover.png hidden.png
python -m secure_steganography decode hidden.png
python -m secure_steganography capacity cover.png
```

Encoding prompts for a password and message. Extraction prompts for the password. Choose a PNG large enough for the message; capacity excludes the format header and GCM tag.

## Run the web interface

Start the Express service from `backend/` with `npm ci` and `npm start`. Start the React app from `frontend/` with `npm ci` and `npm run dev`. Configure `WEB_ORIGINS` and `VITE_API_BASE_URL` for deployed origins as described in the README.

The web UI downloads the encoded PNG and displays recovered text only for the current page session. Use its Clear button or leave the page when finished.
