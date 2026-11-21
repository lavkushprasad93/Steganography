from pathlib import Path

from ..config import GCM_TAG_SIZE, HEADER_SIZE
from ..image_processing import load_png_image


def maximum_ciphertext_bytes(channel_count: int) -> int:
    return max(0, channel_count // 8 - HEADER_SIZE)


def maximum_message_bytes(channel_count: int) -> int:
    return max(0, maximum_ciphertext_bytes(channel_count) - GCM_TAG_SIZE)


def capacity_bytes(source: str | Path | bytes) -> int:
    image = load_png_image(source)
    return maximum_message_bytes(image.width * image.height * 3)
