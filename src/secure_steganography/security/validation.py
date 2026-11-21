from ..config import MAX_MESSAGE_BYTES, MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH
from ..utils import SteganographyError


def validate_password(password: str) -> bytes:
    if not isinstance(password, str) or not password:
        raise SteganographyError("Password must not be empty.")
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise SteganographyError(f"Password must be {MAX_PASSWORD_BYTES} bytes or fewer.")
    return encoded


def validate_new_password(password: str) -> None:
    validate_password(password)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SteganographyError(
            f"New passwords must be at least {MIN_PASSWORD_LENGTH} characters."
        )


def validate_message(message: str) -> bytes:
    if not isinstance(message, str) or not message:
        raise SteganographyError("Message must not be empty.")
    encoded = message.encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise SteganographyError(f"Message must be {MAX_MESSAGE_BYTES} bytes or fewer.")
    return encoded
