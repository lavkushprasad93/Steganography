import struct

from ..algorithms import extract_payload
from ..config import GCM_TAG_SIZE, HEADER_SIZE, MAGIC, NONCE_SIZE, SALT_SIZE
from ..image_processing import load_png_image
from ..security import decrypt_message, validate_password
from ..utils import SteganographyError
from .capacity import maximum_ciphertext_bytes


def decode_png_bytes(image_data: bytes, password: str) -> str:
    validate_password(password)
    image = load_png_image(image_data)
    channels = image.tobytes()
    header = extract_payload(channels, HEADER_SIZE)
    if header[: len(MAGIC)] != MAGIC:
        raise SteganographyError("No supported hidden message was found in this image.")

    salt_start = len(MAGIC)
    salt = header[salt_start : salt_start + SALT_SIZE]
    nonce_start = salt_start + SALT_SIZE
    nonce = header[nonce_start : nonce_start + NONCE_SIZE]
    ciphertext_size = struct.unpack(">I", header[nonce_start + NONCE_SIZE : HEADER_SIZE])[0]
    if ciphertext_size < GCM_TAG_SIZE or ciphertext_size > maximum_ciphertext_bytes(len(channels)):
        raise SteganographyError("Invalid payload length; the image may be damaged.")

    ciphertext = extract_payload(channels, ciphertext_size, HEADER_SIZE * 8)
    plaintext = decrypt_message(ciphertext, password, salt, nonce, header)
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SteganographyError("The authenticated message is not valid UTF-8.") from exc
