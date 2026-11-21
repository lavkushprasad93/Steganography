import pytest

from secure_steganography import decode_png_bytes, encode_png_bytes
from secure_steganography.utils import SteganographyError


def test_wrong_password_is_rejected(cover_png):
    encoded = encode_png_bytes(cover_png, "secret", "correct password")

    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_png_bytes(encoded, "wrong password")
