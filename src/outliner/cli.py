from __future__ import annotations

import argparse
from pathlib import Path

from .outline import OutlineError, format_outline, parse_python_file
from .tui import CursesUnavailableError, run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outliner",
        description="Open a two-pane terminal outline for a Python module.",
    )
    parser.add_argument("file", type=Path, help="Python file to browse")
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_outline",
        help="print the outline and exit instead of opening the TUI",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        root, source_lines = parse_python_file(args.file)
    except OutlineError as exc:
        parser.error(str(exc))

    if args.print_outline:
        print(format_outline(root))
        return 0

    try:
        run_tui(args.file, root, source_lines)
    except CursesUnavailableError as exc:
        parser.error(str(exc))

    return 0
