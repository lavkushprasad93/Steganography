from pathlib import Path

from ..config import MAX_IMAGE_BYTES
from ..core.encoder import encode_png_bytes
from ..image_processing import read_png_file
from ..utils import SteganographyError
from .output import prepare_output_path


def encode_image(
    input_path: str | Path,
    output_path: str | Path,
    message: str,
    password: str,
    force: bool = False,
) -> None:
    destination = prepare_output_path(input_path, output_path, force)
    if destination.suffix.lower() != ".png":
        raise SteganographyError("Output filename must end in .png.")
    encoded = encode_png_bytes(read_png_file(input_path), message, password)
    if len(encoded) > MAX_IMAGE_BYTES:
        raise SteganographyError("Encoded PNG exceeds the 5 MB limit.")
    destination.write_bytes(encoded)
