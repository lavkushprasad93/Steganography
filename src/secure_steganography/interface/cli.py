import argparse
import getpass
import sys

from ..core.capacity import capacity_bytes
from ..services import decode_image, encode_image
from ..utils import SteganographyError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secure-steganography",
        description="Hide and recover encrypted messages in PNG images.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    encode = commands.add_parser("encode", help="Encrypt and hide a message in a PNG")
    encode.add_argument("image", help="Input cover PNG")
    encode.add_argument("output", help="Output stego PNG")
    encode.add_argument("--message", help="Message (omit to enter it interactively)")
    decode = commands.add_parser("decode", help="Extract and decrypt a message from a PNG")
    decode.add_argument("image", help="Stego PNG")
    capacity = commands.add_parser("capacity", help="Show the maximum message size for a PNG")
    capacity.add_argument("image", help="Cover PNG")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capacity":
            print(f"Approximate maximum plaintext capacity: {capacity_bytes(args.image)} bytes")
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
