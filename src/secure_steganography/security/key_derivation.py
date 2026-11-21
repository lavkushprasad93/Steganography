from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import KDF_ITERATIONS
from .validation import validate_password


def derive_key(password: str, salt: bytes) -> bytes:
    password_bytes = validate_password(password)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password_bytes)
