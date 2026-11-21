from secure_steganography import decode_image, encode_image


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
        encode_png_bytes(output.getvalue(), "x" * 1_000, "password")
