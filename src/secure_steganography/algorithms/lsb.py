from ..core.bit_operations import iter_bits, read_embedded_bytes
from ..utils import SteganographyError


def embed_payload(channel_data: bytes, payload: bytes) -> bytes:
    if len(payload) * 8 > len(channel_data):
        raise SteganographyError("Payload does not fit in the image.")
    result = bytearray(channel_data)
    for index, bit in enumerate(iter_bits(payload)):
        result[index] = (result[index] & 0xFE) | bit
    return bytes(result)


def extract_payload(channel_data: bytes, byte_count: int, start_bit: int = 0) -> bytes:
    return read_embedded_bytes(channel_data, byte_count, start_bit)
