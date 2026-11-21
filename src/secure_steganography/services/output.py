from pathlib import Path

from ..utils import SteganographyError


def prepare_output_path(
    input_path: str | Path,
    output_path: str | Path,
    force: bool,
) -> Path:
    source = Path(input_path)
    destination = Path(output_path)
    if source.resolve() == destination.resolve():
        raise SteganographyError("Input and output paths must be different.")
    if destination.exists() and not force:
        raise SteganographyError(
            f"Output file already exists: {destination}. Use --force to overwrite."
        )
    return destination
