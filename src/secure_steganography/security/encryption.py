from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..utils import SteganographyError
from .key_derivation import derive_key


def encrypt_message(
    plaintext: bytes,
    password: str,
    salt: bytes,
    nonce: bytes,
    associated_data: bytes,
) -> bytes:
    return AESGCM(derive_key(password, salt)).encrypt(nonce, plaintext, associated_data)


def decrypt_message(
    ciphertext: bytes,
    password: str,
    salt: bytes,
    nonce: bytes,
    associated_data: bytes,
) -> bytes:
    try:
        return AESGCM(derive_key(password, salt)).decrypt(nonce, ciphertext, associated_data)
    except InvalidTag as exc:
        raise SteganographyError(
            "Incorrect password or the embedded data has been modified."
        ) from exc
