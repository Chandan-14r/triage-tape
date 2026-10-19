from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import build_handoff, build_handoff_json, parse_notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn plain-text triage notes into a Markdown handoff.")
    parser.add_argument("input", type=Path, help="Source .txt file")
    parser.add_argument("-o", "--output", type=Path, help="Write Markdown to this file (defaults to stdout)")
    parser.add_argument("--title", default="Incident handoff", help="Handoff title")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--since",
        type=Path,
        metavar="PREVIOUS_NOTES",
        help="Compare against the previous shift's notes and highlight changes",
    )
    args = parser.parse_args()
    try:
        items, warnings = parse_notes(args.input.read_text(encoding="utf-8"))
        previous_items = None
        if args.since:
            previous_items, previous_warnings = parse_notes(args.since.read_text(encoding="utf-8"))
            warnings += [f"Previous notes: {warning}" for warning in previous_warnings]
    except OSError as error:
        parser.error(str(error))
    result = (
        build_handoff_json(items, args.title, previous_items=previous_items)
        if args.format == "json"
        else build_handoff(items, args.title, previous_items=previous_items)
    )
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
