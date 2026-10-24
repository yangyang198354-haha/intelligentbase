"""MOD-002 cli — argparse entry point (implements IFC-007…009)."""
from __future__ import annotations

import argparse
import sys

from .core import run


def build_parser() -> argparse.ArgumentParser:
    """IFC-007: define PATH plus --top / --ignore-case / --min-length."""
    parser = argparse.ArgumentParser(
        prog="wordfreq", description="Count word frequencies in a UTF-8 text file."
    )
    parser.add_argument("path", help="path to a UTF-8 text file")
    parser.add_argument(
        "--top", type=int, default=10, metavar="N", help="show top N words (default: 10)"
    )
    parser.add_argument(
        "--ignore-case", action="store_true", help="fold case before counting"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=1,
        metavar="L",
        help="ignore words shorter than L (default: 1)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """IFC-008: map success to 0, unreadable input to 2 with stderr text."""
    args = build_parser().parse_args(argv)
    try:
        output = run(
            args.path,
            top=args.top,
            ignore_case=args.ignore_case,
            min_length=args.min_length,
        )
    except (OSError, UnicodeDecodeError) as exc:
        print(f"wordfreq: error: {exc}", file=sys.stderr)
        return 2
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
