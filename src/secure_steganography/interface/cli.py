import argparse
import getpass
import sys
from pathlib import Path

from ..config import MAX_MESSAGE_BYTES
from ..core.capacity import capacity_bytes
from ..services import decode_image, decode_image_to_file, encode_image
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
    message_source = encode.add_mutually_exclusive_group()
    message_source.add_argument("--message", help="Message (omit to enter it interactively)")
    message_source.add_argument("--message-file", help="UTF-8 text file containing the message")
    encode.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    decode = commands.add_parser("decode", help="Extract and decrypt a message from a PNG")
    decode.add_argument("image", help="Stego PNG")
    decode.add_argument("--output", help="Write the recovered message to a UTF-8 text file")
    decode.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    capacity = commands.add_parser("capacity", help="Show the maximum message size for a PNG")
    capacity.add_argument("image", help="Cover PNG")
    return parser


def _read_message_file(path: str) -> str:
    with Path(path).open("rb") as message_file:
        message_bytes = message_file.read(MAX_MESSAGE_BYTES + 1)
    if len(message_bytes) > MAX_MESSAGE_BYTES:
        raise SteganographyError(f"Message must be {MAX_MESSAGE_BYTES:,} bytes or fewer.")
    try:
        return message_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SteganographyError("Message file must contain valid UTF-8 text.") from exc


def _prompt_password(confirm: bool = False) -> str:
    password = getpass.getpass("Password: ")
    if confirm and password != getpass.getpass("Confirm password: "):
        raise SteganographyError("Passwords do not match.")
    return password


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capacity":
            print(f"Maximum plaintext capacity: {capacity_bytes(args.image)} bytes")
            return 0

        if args.command == "encode":
            if args.message_file is not None:
                message = _read_message_file(args.message_file)
            else:
                message = args.message if args.message is not None else input("Message to hide: ")
            password = _prompt_password(confirm=True)
            encode_image(args.image, args.output, message, password, force=args.force)
            print(f"Message encrypted and embedded successfully: {args.output}")
        else:
            if args.force and args.output is None:
                raise SteganographyError("--force requires --output.")
            password = _prompt_password()
            if args.output is not None:
                decode_image_to_file(args.image, args.output, password, force=args.force)
                print(f"Recovered message written to: {args.output}")
            else:
                print("Recovered message:")
                print(decode_image(args.image, password))
        return 0
    except (SteganographyError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
