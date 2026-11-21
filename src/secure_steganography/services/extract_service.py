from pathlib import Path

from ..core.decoder import decode_png_bytes
from ..image_processing import read_png_file


def decode_image(image_path: str | Path, password: str) -> str:
    return decode_png_bytes(read_png_file(image_path), password)
