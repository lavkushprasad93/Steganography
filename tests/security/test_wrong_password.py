import struct
from io import BytesIO

import pytest
from PIL import Image

from secure_steganography import decode_png_bytes, encode_png_bytes
from secure_steganography.algorithms import embed_payload
from secure_steganography.config import GCM_TAG_SIZE, MAGIC, NONCE_SIZE, SALT_SIZE
from secure_steganography.security import encrypt_message
from secure_steganography.utils import SteganographyError


def test_wrong_password_is_rejected(cover_png):
    encoded = encode_png_bytes(cover_png, "secret", "correct horse battery staple")

    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_png_bytes(encoded, "wrong password")


def test_legacy_short_password_remains_decodable(cover_png):
    password = "legacy"
    message = "previously encoded"
    salt = bytes(range(SALT_SIZE))
    nonce = bytes(range(NONCE_SIZE))
    ciphertext_size = len(message.encode("utf-8")) + GCM_TAG_SIZE
    header = MAGIC + salt + nonce + struct.pack(">I", ciphertext_size)
    ciphertext = encrypt_message(message.encode("utf-8"), password, salt, nonce, header)

    with Image.open(BytesIO(cover_png)) as image:
        rgb = image.convert("RGB")
    channels = embed_payload(rgb.tobytes(), header + ciphertext)
    encoded = BytesIO()
    Image.frombytes("RGB", rgb.size, channels).save(encoded, format="PNG")

    assert decode_png_bytes(encoded.getvalue(), password) == message
