from pathlib import Path

from ..core.decoder import decode_png_bytes
from ..image_processing import read_png_file
from .output import prepare_output_path


def decode_image(image_path: str | Path, password: str) -> str:
    return decode_png_bytes(read_png_file(image_path), password)


def decode_image_to_file(
    image_path: str | Path,
    output_path: str | Path,
    password: str,
    force: bool = False,
) -> None:
    destination = prepare_output_path(image_path, output_path, force)
    message = decode_image(image_path, password)
    destination.write_text(message, encoding="utf-8")
