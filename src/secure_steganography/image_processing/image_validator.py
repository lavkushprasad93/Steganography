from PIL import Image

from ..config import MAX_IMAGE_PIXELS
from ..utils import SteganographyError


def validate_png_image(image: Image.Image) -> None:
    if image.format != "PNG":
        raise SteganographyError("Only PNG images are supported.")
    if image.width < 1 or image.height < 1 or image.width * image.height > MAX_IMAGE_PIXELS:
        raise SteganographyError(
            f"Image dimensions must not exceed {MAX_IMAGE_PIXELS:,} pixels."
        )
    if getattr(image, "n_frames", 1) != 1:
        raise SteganographyError("Animated PNG images are not supported.")
