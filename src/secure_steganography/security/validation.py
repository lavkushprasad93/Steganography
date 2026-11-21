from ..config import MAX_MESSAGE_BYTES, MAX_PASSWORD_BYTES
from ..utils import SteganographyError


def validate_password(password: str) -> bytes:
    if not isinstance(password, str) or not password:
        raise SteganographyError("Password must not be empty.")
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise SteganographyError(f"Password must be {MAX_PASSWORD_BYTES} bytes or fewer.")
    return encoded


def validate_message(message: str) -> bytes:
    if not isinstance(message, str) or not message:
        raise SteganographyError("Message must not be empty.")
    encoded = message.encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise SteganographyError(f"Message must be {MAX_MESSAGE_BYTES} bytes or fewer.")
    return encoded
