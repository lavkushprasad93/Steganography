import secrets
import struct
from io import BytesIO

from PIL import Image

from ..algorithms import embed_payload
from ..config import (
    GCM_TAG_SIZE,
    HEADER_SIZE,
    MAGIC,
    MAX_IMAGE_BYTES,
    NONCE_SIZE,
    SALT_SIZE,
)
from ..image_processing import load_png_image
from ..security import encrypt_message, validate_message, validate_password
from ..utils import SteganographyError
from .capacity import maximum_ciphertext_bytes


def encode_png_bytes(image_data: bytes, message: str, password: str) -> bytes:
    plaintext = validate_message(message)
    validate_password(password)
    image = load_png_image(image_data)
    channels = image.tobytes()
    ciphertext_size = len(plaintext) + GCM_TAG_SIZE
    if ciphertext_size > maximum_ciphertext_bytes(len(channels)):
        raise SteganographyError(
            f"Message exceeds this image's capacity ({max(0, maximum_ciphertext_bytes(len(channels)) - GCM_TAG_SIZE)} bytes)."
        )
    if ciphertext_size > 0xFFFFFFFF:
        raise SteganographyError("Message is too large.")

    salt = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    header = MAGIC + salt + nonce + struct.pack(">I", ciphertext_size)
    ciphertext = encrypt_message(plaintext, password, salt, nonce, header)
    payload = header + ciphertext
    if len(payload) != HEADER_SIZE + ciphertext_size:
        raise RuntimeError("Encrypted payload length does not match its header.")

    encoded_channels = embed_payload(channels, payload)
    encoded_image = Image.frombytes("RGB", image.size, encoded_channels)
    output = BytesIO()
    encoded_image.save(output, format="PNG", optimize=True)
    result = output.getvalue()
    if len(result) > MAX_IMAGE_BYTES:
        raise SteganographyError("Encoded PNG exceeds the 5 MB limit.")
    return result
