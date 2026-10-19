"""Command line interface.

europii scan notes.txt --countries FI,SE
cat mail.txt | europii redact --style hash > mail.redacted.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import DEFAULT_THRESHOLD, __version__, redact, scan


def _read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="europii", description="Find and redact personal data in European text, locally."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("scan", "list findings as JSON lines"),
        ("redact", "print redacted text"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("file", nargs="?", default="-", help="input file, or - for stdin")
        p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
        p.add_argument("--countries", default="", help="expected countries, e.g. FI,SE")
        p.add_argument("--entities", default="", help="restrict to entity types, e.g. EMAIL,IBAN")
        if name == "redact":
            p.add_argument(
                "--style", choices=["placeholder", "mask", "hash"], default="placeholder"
            )
    args = parser.parse_args(argv)
    text = _read(args.file)
    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    entities = [e.strip().upper() for e in args.entities.split(",") if e.strip()] or None
    if args.command == "scan":
        for f in scan(text, entities=entities, threshold=args.threshold, countries=countries):
            print(json.dumps(f.to_dict(), ensure_ascii=False))
    else:
        sys.stdout.write(
            redact(
                text,
                entities=entities,
                threshold=args.threshold,
                countries=countries,
                style=args.style,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
