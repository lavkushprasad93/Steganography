import base64
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from secure_steganography import decode_png_bytes, encode_png_bytes
from secure_steganography.security import key_derivation

BACKEND_PATH = Path(__file__).parents[2] / "backend"
NODE_API_AVAILABLE = (
    shutil.which("node") is not None
    and (BACKEND_PATH / "node_modules" / "sharp").is_dir()
)


@pytest.mark.skipif(
    not NODE_API_AVAILABLE,
    reason="Node.js and backend npm dependencies are required for interop testing",
)
def test_python_and_node_exchange_payloads(cover_png, monkeypatch):
    monkeypatch.setattr(key_derivation, "KDF_ITERATIONS", 600_000)
    message = "Python ↔ Node interop ✓"
    password = "shared-format password"
    node_encode = (
        "const {encodePng}=require('./src/core');"
        "let chunks=[];"
        "process.stdin.on('data',chunk=>chunks.push(chunk));"
        "process.stdin.on('end',async()=>{"
        "try{const input=JSON.parse(Buffer.concat(chunks).toString());"
        "const output=await encodePng(Buffer.from(input.image,'base64'),input.message,input.password);"
        "process.stdout.write(output.toString('base64'));"
        "}catch(error){console.error(error.message);process.exitCode=1;}});"
    )
    node_decode = (
        "const {decodePng}=require('./src/core');"
        "let chunks=[];"
        "process.stdin.on('data',chunk=>chunks.push(chunk));"
        "process.stdin.on('end',async()=>{"
        "try{const input=JSON.parse(Buffer.concat(chunks).toString());"
        "process.stdout.write(await decodePng(Buffer.from(input.image,'base64'),input.password));"
        "}catch(error){console.error(error.message);process.exitCode=1;}});"
    )

    node_encoded = subprocess.run(
        ["node", "-e", node_encode],
        cwd=BACKEND_PATH,
        input=json.dumps(
            {
                "image": base64.b64encode(cover_png).decode("ascii"),
                "message": message,
                "password": password,
            }
        ),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    ).stdout
    assert decode_png_bytes(base64.b64decode(node_encoded), password) == message

    python_encoded = encode_png_bytes(cover_png, message, password)
    node_decoded = subprocess.run(
        ["node", "-e", node_decode],
        cwd=BACKEND_PATH,
        input=json.dumps(
            {
                "image": base64.b64encode(python_encoded).decode("ascii"),
                "password": password,
            }
        ),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    ).stdout
    assert node_decoded == message
