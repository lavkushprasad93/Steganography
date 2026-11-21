from io import BytesIO

import pytest
from PIL import Image

from secure_steganography import encode_png_bytes
from secure_steganography.security.validation import (
    validate_message,
    validate_new_password,
    validate_password,
)
from secure_steganography.utils import SteganographyError


def test_empty_or_oversized_credentials_are_rejected():
    with pytest.raises(SteganographyError, match="Message must not be empty"):
        validate_message("")
    with pytest.raises(SteganographyError, match="Password must not be empty"):
        validate_password("")
    with pytest.raises(SteganographyError, match="Password must be"):
        validate_password("x" * 1_025)
    with pytest.raises(SteganographyError, match="at least 12 characters"):
        validate_new_password("x" * 11)
    validate_new_password("x" * 12)
    validate_new_password("🌍" * 12)


def test_new_encodings_reject_passwords_shorter_than_twelve_characters(cover_png):
    with pytest.raises(SteganographyError, match="at least 12 characters"):
        encode_png_bytes(cover_png, "message", "short")


def test_jpeg_and_non_image_data_are_rejected(cover_png):
    jpeg = BytesIO()
    Image.new("RGB", (64, 64), "white").save(jpeg, format="JPEG")

    with pytest.raises(SteganographyError, match="Only PNG"):
        encode_png_bytes(jpeg.getvalue(), "message", "correct horse battery staple")
    with pytest.raises(SteganographyError, match="valid PNG"):
        encode_png_bytes(b"not an image", "message", "correct horse battery staple")


def test_truncated_png_decode_errors_are_normalized(cover_png):
    with pytest.raises(SteganographyError, match="valid PNG"):
        encode_png_bytes(
            cover_png[: len(cover_png) // 2],
            "message",
            "correct horse battery staple",
        )


def test_decompression_bomb_errors_are_normalized_without_global_changes(
    monkeypatch, cover_png
):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)

    with pytest.raises(SteganographyError, match="valid PNG"):
        encode_png_bytes(cover_png, "message", "correct horse battery staple")

    assert Image.MAX_IMAGE_PIXELS == 10


def test_messages_over_limit_are_rejected():
    with pytest.raises(SteganographyError, match="Message must be"):
        validate_message("x" * 1_000_001)


def test_images_over_pixel_limit_are_rejected():
    oversized = BytesIO()
    Image.new("RGB", (2_001, 2_000), "black").save(oversized, format="PNG")

    with pytest.raises(SteganographyError, match="pixels"):
        encode_png_bytes(
            oversized.getvalue(),
            "message",
            "correct horse battery staple",
        )
