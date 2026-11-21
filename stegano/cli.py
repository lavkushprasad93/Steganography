from __future__ import annotations
import argparse
import getpass
import sys
from .core import SteganographyError, capacity_bytes, decode_image, encode_image


def main() -> int:
    parser = argparse.ArgumentParser(prog="stegano", description="Hide and recover encrypted messages in PNG images.")
    sub = parser.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encode", help="Encrypt and hide a message in a PNG")
    enc.add_argument("image", help="Input cover PNG")
    enc.add_argument("output", help="Output stego PNG")
    enc.add_argument("--message", help="Message (omit to enter it interactively)")
    dec = sub.add_parser("decode", help="Extract and decrypt a message from a PNG")
    dec.add_argument("image", help="Stego PNG")
    cap = sub.add_parser("capacity", help="Show approximate message capacity")
    cap.add_argument("image", help="Cover PNG")
    args = parser.parse_args()
    try:
        if args.command == "capacity":
            plaintext_capacity = max(0, capacity_bytes(args.image) - 16)
            print(f"Approximate maximum plaintext capacity: {plaintext_capacity} bytes")
            return 0
        password = getpass.getpass("Password: ")
        if args.command == "encode":
            message = args.message if args.message is not None else input("Message to hide: ")
            encode_image(args.image, args.output, message, password)
            print(f"Message encrypted and embedded successfully: {args.output}")
        else:
            print("Recovered message:")
            print(decode_image(args.image, password))
        return 0
    except (SteganographyError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
