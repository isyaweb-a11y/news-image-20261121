#!/usr/bin/env python3
"""Hand the grader the front page for Saturday 21 November 2026.

The repository carries one finished picture, ``entry.png``: a single
1024x1024 front page that sums up the world news of Saturday
21 November 2026 — 45 stories, from Poland's call for a NATO shield to
the claimed proof of the Riemann hypothesis. This program is the
entrypoint. It does not draw anything; it delivers the committed image
to the output directory and proves, before it reports success, that
what landed there is exactly what was committed.

Where the image goes, in order of precedence:

1. the first command-line argument, when one is given;
2. the ``MAKEFUN_OUTPUT_DIR`` environment variable;
3. ``/output``, the grader's directory.

To try it outside the grader:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Python 3 standard library only. No network, no writes anywhere but the
output directory, and the same bytes on every run.
"""

import hashlib
import os
import struct
import sys
from pathlib import Path

IMAGE_FILENAME = "entry.png"
BYTE_CAP = 1_048_576  # the bounty allows at most 1 MiB
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
FALLBACK_OUTPUT = "/output"
OUTPUT_ENV = "MAKEFUN_OUTPUT_DIR"


class DeliveryError(Exception):
    """The image could not be delivered intact."""


def source_image() -> Path:
    """The committed picture sits beside this file."""
    return Path(__file__).resolve().parent / IMAGE_FILENAME


def destination_dir(argv) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    return Path(os.environ.get(OUTPUT_ENV, FALLBACK_OUTPUT))


def load_verified_image(path: Path) -> bytes:
    """Read the picture, rejecting anything that is not a capped PNG."""
    if not path.is_file():
        raise DeliveryError(f"the committed image is missing: {path}")
    blob = path.read_bytes()
    if len(blob) > BYTE_CAP:
        raise DeliveryError(
            f"{path.name} weighs {len(blob)} bytes, over the {BYTE_CAP} cap"
        )
    if blob[:8] != PNG_MAGIC:
        raise DeliveryError(f"{path.name} does not open with a PNG signature")
    if len(blob) < 24 or blob[12:16] != b"IHDR":
        raise DeliveryError(f"{path.name} has no readable IHDR header")
    width, height = struct.unpack(">II", blob[16:24])
    if (width, height) != (1024, 1024):
        raise DeliveryError(
            f"{path.name} is {width}x{height}, not the expected 1024x1024"
        )
    if b"IEND" not in blob[-16:]:
        raise DeliveryError(f"{path.name} ends early: no IEND trailer")
    return blob


def place_image(blob: bytes, folder: Path) -> Path:
    """Copy the bytes into place, then read them back and compare."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / IMAGE_FILENAME
    target.write_bytes(blob)
    if target.read_bytes() != blob:
        raise DeliveryError(f"the copy at {target} is not byte-identical")
    return target


def run(argv) -> int:
    try:
        blob = load_verified_image(source_image())
        target = place_image(blob, destination_dir(argv))
    except (DeliveryError, OSError) as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 1
    print(
        f"delivered {target} "
        f"({len(blob)} bytes, sha256 {hashlib.sha256(blob).hexdigest()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv))
