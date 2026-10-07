from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import build_handoff, parse_notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn plain-text triage notes into a Markdown handoff.")
    parser.add_argument("input", type=Path, help="Source .txt file")
    parser.add_argument("-o", "--output", type=Path, help="Write Markdown to this file (defaults to stdout)")
    parser.add_argument("--title", default="Incident handoff", help="Handoff title")
    args = parser.parse_args()
    try:
        items, warnings = parse_notes(args.input.read_text(encoding="utf-8"))
    except OSError as error:
        parser.error(str(error))
    result = build_handoff(items, args.title)
    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(result)
    if warnings:
        print("\n".join(f"warning: {warning}" for warning in warnings), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
