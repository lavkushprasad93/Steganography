from secure_steganography import capacity_bytes
from secure_steganography.config import GCM_TAG_SIZE, HEADER_SIZE


def test_capacity_accounts_for_header_and_gcm_tag(cover_png):
    assert capacity_bytes(cover_png) == (128 * 128 * 3) // 8 - HEADER_SIZE - GCM_TAG_SIZE
