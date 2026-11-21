"""PNG LSB steganography with password-based authenticated encryption."""
from __future__ import annotations

import secrets
import struct
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image

MAGIC = b"STG2"
SALT_SIZE = 16
NONCE_SIZE = 12
ITERATIONS = 600_000
HEADER_SIZE = len(MAGIC) + SALT_SIZE + NONCE_SIZE + 4
MAX_PASSWORD_BYTES = 1024


class SteganographyError(Exception):
    """Raised for invalid images, passwords, or embedded payloads."""


def _derive_key(password: str, salt: bytes) -> bytes:
    if not isinstance(password, str) or not password:
        raise SteganographyError("Password must not be empty.")
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise SteganographyError("Password is too long.")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return kdf.derive(password_bytes)


def _bits(data: bytes):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def _read_bytes(channel_values, byte_count: int) -> bytes:
    out = bytearray()
    value = 0
    count = 0
    for bit in channel_values:
        value = (value << 1) | (int(bit) & 1)
        count += 1
        if count == 8:
            out.append(value)
            if len(out) == byte_count:
                return bytes(out)
            value = 0
            count = 0
    raise SteganographyError("Image ended before the complete payload could be read.")


def capacity_bytes(image_path: str | Path) -> int:
    """Return maximum encrypted payload bytes (excluding metadata)."""
    with Image.open(image_path) as im:
        if im.format != "PNG":
            raise SteganographyError("Use a PNG cover image. JPEG and other lossy formats are not supported.")
        rgb = im.convert("RGB")
        return max(0, (rgb.width * rgb.height * 3) // 8 - HEADER_SIZE)


def encode_image(input_path: str | Path, output_path: str | Path, message: str, password: str) -> None:
    if not isinstance(message, str) or not message:
        raise SteganographyError("Message must not be empty.")
    destination = Path(output_path)
    if destination.suffix.lower() != ".png":
        raise SteganographyError("Output filename must end in .png.")
    with Image.open(input_path) as source:
        if source.format != "PNG":
            raise SteganographyError("Cover image must be PNG to preserve embedded bits.")
        image = source.convert("RGB")

    salt, nonce = secrets.token_bytes(SALT_SIZE), secrets.token_bytes(NONCE_SIZE)
    plaintext = message.encode("utf-8")
    ciphertext_size = len(plaintext) + 16
    pixels = bytearray(image.tobytes())
    available = max(0, len(pixels) // 8 - HEADER_SIZE)
    if ciphertext_size > available:
        raise SteganographyError(
            f"Message is too large. Approximate encrypted capacity: {available} bytes; "
            f"message uses {ciphertext_size} bytes before metadata."
        )
    if ciphertext_size > 0xFFFFFFFF:
        raise SteganographyError("Message is too large.")

    header = MAGIC + salt + nonce + struct.pack(">I", ciphertext_size)
    ciphertext = AESGCM(_derive_key(password, salt)).encrypt(nonce, plaintext, header)
    payload = header + ciphertext

    for index, bit in enumerate(_bits(payload)):
        pixels[index] = (pixels[index] & 0xFE) | bit

    encoded = Image.frombytes("RGB", image.size, bytes(pixels))
    encoded.save(destination, format="PNG", optimize=True)


def decode_image(image_path: str | Path, password: str) -> str:
    with Image.open(image_path) as source:
        if source.format != "PNG":
            raise SteganographyError("Stego image must be PNG. Do not convert or recompress it.")
        pixels = source.convert("RGB").tobytes()

    lsb_stream = (value & 1 for value in pixels)
    header = _read_bytes(lsb_stream, HEADER_SIZE)
    if header[:len(MAGIC)] != MAGIC:
        raise SteganographyError("No supported hidden message was found in this image.")
    offset = len(MAGIC)
    salt = header[offset:offset + SALT_SIZE]
    offset += SALT_SIZE
    nonce = header[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE
    ciphertext_size = struct.unpack(">I", header[offset:offset + 4])[0]
    if ciphertext_size < 16 or ciphertext_size > (len(pixels) // 8 - HEADER_SIZE):
        raise SteganographyError("Invalid payload length; the image may be damaged.")
    ciphertext = _read_bytes(lsb_stream, ciphertext_size)
    try:
        plaintext = AESGCM(_derive_key(password, salt)).decrypt(nonce, ciphertext, header)
        return plaintext.decode("utf-8")
    except (InvalidTag, UnicodeDecodeError) as exc:
        raise SteganographyError("Incorrect password or the embedded data has been modified.") from exc
