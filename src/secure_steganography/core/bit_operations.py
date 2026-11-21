from collections.abc import Iterator

from ..utils import SteganographyError


def iter_bits(data: bytes) -> Iterator[int]:
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def read_embedded_bytes(channel_data: bytes, byte_count: int, start_bit: int = 0) -> bytes:
    end_bit = start_bit + byte_count * 8
    if byte_count < 0 or start_bit < 0 or end_bit > len(channel_data):
        raise SteganographyError("Image ended before the complete payload could be read.")

    result = bytearray(byte_count)
    for byte_index in range(byte_count):
        value = 0
        for bit_index in range(8):
            channel_index = start_bit + byte_index * 8 + bit_index
            value = (value << 1) | (channel_data[channel_index] & 1)
        result[byte_index] = value
    return bytes(result)
