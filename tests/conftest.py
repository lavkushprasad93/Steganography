from io import BytesIO

import pytest
from PIL import Image

from secure_steganography.security import key_derivation


@pytest.fixture(autouse=True)
def fast_key_derivation(monkeypatch):
    monkeypatch.setattr(key_derivation, "KDF_ITERATIONS", 1_000)


@pytest.fixture
def cover_png():
    output = BytesIO()
    Image.new("RGB", (128, 128), (91, 137, 201)).save(output, format="PNG")
    return output.getvalue()
