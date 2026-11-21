# Algorithms and payload format

## Encryption

The UTF-8 message is encrypted using AES-256-GCM. A random 16-byte salt feeds PBKDF2-HMAC-SHA256 with 600,000 iterations to derive the 32-byte key. Each encoding uses a fresh 12-byte nonce. The GCM tag is appended to the ciphertext.

## Version 2 payload

All multibyte integers are big-endian. The payload is:

| Field | Size |
|---|---:|
| Magic/version (`STG2`) | 4 bytes |
| Salt | 16 bytes |
| Nonce | 12 bytes |
| Ciphertext length, including GCM tag | 4 bytes |
| Ciphertext and GCM tag | Variable |

The complete fixed header is supplied as AES-GCM associated data. Header modifications, a wrong password, or ciphertext changes therefore fail authentication. Python and Node use this same layout.

## LSB encoding

Bytes are emitted most-significant bit first. Each successive RGB channel value stores one bit in its least significant position. Capacity is based on `width × height × 3` channel bits, less the header and 16-byte GCM tag. PNG is required because lossy transformations can alter embedded bits.

The algorithm is educational; basic LSB embedding does not make messages undetectable.
