from io import BytesIO

import pytest
from PIL import Image

from secure_steganography import decode_png_bytes, encode_png_bytes
from secure_steganography.config import HEADER_SIZE
from secure_steganography.utils import SteganographyError


def test_modified_ciphertext_is_rejected(cover_png):
    encoded = encode_png_bytes(cover_png, "secret", "password")
    with Image.open(BytesIO(encoded)) as image:
        pixels = bytearray(image.convert("RGB").tobytes())
        pixels[HEADER_SIZE * 8] ^= 1
        modified = Image.frombytes("RGB", image.size, bytes(pixels))
    output = BytesIO()
    modified.save(output, format="PNG")

    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_png_bytes(output.getvalue(), "password")
