"""Password-protected PNG steganography."""

from .core.capacity import capacity_bytes
from .core.decoder import decode_png_bytes
from .core.encoder import encode_png_bytes
from .services.extract_service import decode_image
from .services.hide_service import encode_image
from .utils import SteganographyError

__all__ = [
    "SteganographyError",
    "capacity_bytes",
    "decode_image",
    "decode_png_bytes",
    "encode_image",
    "encode_png_bytes",
]
