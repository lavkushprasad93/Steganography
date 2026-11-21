import pytest

from secure_steganography.security import decrypt_message, encrypt_message
from secure_steganography.utils import SteganographyError


def test_aes_gcm_round_trip_and_authentication():
    message = "authenticated text"
    salt = bytes(range(16))
    nonce = bytes(range(12))
    associated_data = b"STG2 authenticated header"
    encrypted = encrypt_message(message.encode(), "password", salt, nonce, associated_data)

    assert decrypt_message(encrypted, "password", salt, nonce, associated_data) == message.encode()
    with pytest.raises(SteganographyError, match="Incorrect password"):
        decrypt_message(encrypted, "wrong", salt, nonce, associated_data)
