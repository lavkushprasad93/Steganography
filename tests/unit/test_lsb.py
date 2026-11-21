import pytest

from secure_steganography.algorithms.lsb import embed_payload, extract_payload
from secure_steganography.utils import SteganographyError


def test_payload_round_trip_preserves_non_lsb_bits():
    source = bytes(range(64))
    payload = b"\xa5\x00"

    encoded = embed_payload(source, payload)

    assert extract_payload(encoded, len(payload)) == payload
    assert all((before & 0xFE) == (after & 0xFE) for before, after in zip(source, encoded))


def test_embedding_rejects_payload_that_does_not_fit():
    with pytest.raises(SteganographyError, match="does not fit"):
        embed_payload(bytes(7), b"\x00")
