# Architecture

## Components

- `src/secure_steganography/config.py` defines shared payload limits and the binary format constants.
- `algorithms/lsb.py` embeds and reads payload bytes using the least significant bit of RGB channels.
- `security/` validates messages and passwords, derives keys, and performs AES-GCM encryption.
- `image_processing/` loads PNGs, validates dimensions and animation state, and converts images to RGB.
- `core/` composes image, LSB, capacity, and cryptographic operations into byte-oriented encoder and decoder functions.
- `services/` provides path-based workflows for the CLI.
- `interface/cli.py` and `__main__.py` expose the command-line application.
- `backend/` implements the same payload format in Node/Express for the web application.
- `frontend/` contains the React/Vite interface; it does not persist data in browser storage.

## Data flow

Encoding validates the input image, message, and password, derives a 256-bit key, authenticates and encrypts the UTF-8 message, then writes the header and ciphertext into RGB LSBs. Decoding validates the image, reads the fixed header, checks the declared length, authenticates/decrypts, and decodes UTF-8.

The Python core exposes byte-based functions so tests and other local integrations do not require temporary files. The CLI's path-based service writes the requested output PNG. The web API accepts bounded JSON/base64 requests and does not use a database or disk-backed upload middleware.

## Deliberate scope

Only the standard RGB LSB algorithm is implemented. Adaptive embedding, stealth claims, quality metrics, and steganalysis are not part of this version.
