from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ..config import MAX_IMAGE_BYTES
from ..utils import SteganographyError
from .image_validator import validate_png_image


def load_png_image(source: str | Path | bytes) -> Image.Image:
    if isinstance(source, bytes):
        if not source or len(source) > MAX_IMAGE_BYTES:
            raise SteganographyError("PNG data must be non-empty and no larger than 5 MB.")
        image_source = BytesIO(source)
    else:
        image_path = Path(source)
        if image_path.stat().st_size > MAX_IMAGE_BYTES:
            raise SteganographyError("PNG image exceeds the 5 MB limit.")
        image_source = image_path

    try:
        with Image.open(image_source) as image:
            validate_png_image(image)
            return image.convert("RGB")
    except UnidentifiedImageError as exc:
        raise SteganographyError("Input is not a valid PNG image.") from exc


def read_png_file(path: str | Path) -> bytes:
    image_path = Path(path)
    if image_path.stat().st_size > MAX_IMAGE_BYTES:
        raise SteganographyError("PNG image exceeds the 5 MB limit.")
    data = image_path.read_bytes()
    if not data:
        raise SteganographyError("PNG image must not be empty.")
    return data
