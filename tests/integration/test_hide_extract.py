import pytest

from secure_steganography import decode_image, encode_image
from secure_steganography.utils import SteganographyError


def test_file_workflow_round_trips_utf8_message(tmp_path, cover_png):
    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    cover.write_bytes(cover_png)

    encode_image(cover, encoded, "hello, こんにちは 🌍", "correct horse battery staple")

    assert decode_image(encoded, "correct horse battery staple") == "hello, こんにちは 🌍"


def test_capacity_error_does_not_create_output(tmp_path):
    from io import BytesIO

    import pytest
    from PIL import Image

    from secure_steganography import encode_png_bytes
    from secure_steganography.utils import SteganographyError

    output = BytesIO()
    Image.new("RGB", (16, 16), (0, 0, 0)).save(output, format="PNG")

    with pytest.raises(SteganographyError, match="capacity"):
        encode_png_bytes(
            output.getvalue(),
            "x" * 1_000,
            "correct horse battery staple",
        )


def test_encode_refuses_input_alias_and_existing_output_without_force(tmp_path, cover_png):
    cover = tmp_path / "cover.png"
    output = tmp_path / "output.png"
    cover.write_bytes(cover_png)

    with pytest.raises(SteganographyError, match="must be different"):
        encode_image(cover, cover, "message", "correct horse battery staple")
    assert cover.read_bytes() == cover_png

    output.write_bytes(b"keep this file")
    with pytest.raises(SteganographyError, match="already exists"):
        encode_image(cover, output, "message", "correct horse battery staple")
    assert output.read_bytes() == b"keep this file"

    encode_image(cover, output, "message", "correct horse battery staple", force=True)
    assert decode_image(output, "correct horse battery staple") == "message"


def test_decode_to_file_refuses_input_alias_and_requires_force(tmp_path, cover_png):
    from secure_steganography.services import decode_image_to_file

    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    message_file = tmp_path / "message.txt"
    cover.write_bytes(cover_png)
    encode_image(cover, encoded, "message", "correct horse battery staple")

    with pytest.raises(SteganographyError, match="must be different"):
        decode_image_to_file(encoded, encoded, "correct horse battery staple")

    message_file.write_text("keep this file", encoding="utf-8")
    with pytest.raises(SteganographyError, match="already exists"):
        decode_image_to_file(encoded, message_file, "correct horse battery staple")
    assert message_file.read_text(encoding="utf-8") == "keep this file"

    decode_image_to_file(encoded, message_file, "correct horse battery staple", force=True)
    assert message_file.read_text(encoding="utf-8") == "message"
