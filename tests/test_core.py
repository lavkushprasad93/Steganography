from PIL import Image
import pytest
from stegano.core import SteganographyError, decode_image, encode_image


def test_round_trip(tmp_path):
    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    Image.new("RGB", (200, 200), (120, 80, 160)).save(cover)
    encode_image(cover, encoded, "Lavkush Prasad — secure message ✓", "strong test password")
    assert decode_image(encoded, "strong test password") == "Lavkush Prasad — secure message ✓"


def test_wrong_password(tmp_path):
    cover, encoded = tmp_path / "cover.png", tmp_path / "encoded.png"
    Image.new("RGB", (200, 200), "white").save(cover)
    encode_image(cover, encoded, "secret", "correct")
    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_image(encoded, "wrong")


def test_reject_jpeg(tmp_path):
    cover = tmp_path / "cover.jpg"
    Image.new("RGB", (100, 100), "white").save(cover)
    with pytest.raises(SteganographyError, match="PNG"):
        encode_image(cover, tmp_path / "out.png", "secret", "password")
from PIL import Image
import pytest

from stegano import core
from stegano.core import SteganographyError, capacity_bytes, decode_image, encode_image


@pytest.fixture(autouse=True)
def fast_key_derivation(monkeypatch):
    monkeypatch.setattr(core, "ITERATIONS", 1_000)


def create_cover(path, size=(128, 128)):
    Image.new("RGB", size, (91, 137, 201)).save(path, format="PNG")


def test_round_trip_unicode_message(tmp_path):
    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    create_cover(cover)

    encode_image(cover, encoded, "hello, こんにちは 🌍", "correct horse battery staple")

    assert decode_image(encoded, "correct horse battery staple") == "hello, こんにちは 🌍"


def test_wrong_password_and_tampering_are_rejected(tmp_path):
    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    create_cover(cover)
    encode_image(cover, encoded, "secret", "password")

    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_image(encoded, "wrong")

    with Image.open(encoded) as image:
        pixels = bytearray(image.convert("RGB").tobytes())
        pixels[core.HEADER_SIZE * 8] ^= 1
        modified = Image.frombytes("RGB", image.size, bytes(pixels))
    modified.save(encoded, format="PNG")

    with pytest.raises(SteganographyError, match="Incorrect password"):
        decode_image(encoded, "password")


def test_capacity_is_derived_from_rgb_channels(tmp_path):
    cover = tmp_path / "cover.png"
    create_cover(cover, (32, 32))

    assert capacity_bytes(cover) == (32 * 32 * 3) // 8 - core.HEADER_SIZE


def test_oversized_message_fails_before_writing_output(tmp_path):
    cover = tmp_path / "cover.png"
    output = tmp_path / "output.png"
    create_cover(cover, (16, 16))

    with pytest.raises(SteganographyError, match="too large"):
        encode_image(cover, output, "x" * 1_000, "password")

    assert not output.exists()
