#!/usr/bin/env python3
"""Strip SRT numbering and timestamps into lesson-ready plain text."""

from __future__ import annotations

import argparse
import difflib
import glob
import re
import sys
from pathlib import Path


TIMESTAMP_RE = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}.*$"
)


def clean_srt(text: str) -> str:
    """Return subtitle text with counters, timestamps, and blank gaps removed."""
    chunks: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue
        if line.isdigit():
            continue
        if TIMESTAMP_RE.match(line):
            continue

        chunks.append(line)

    return " ".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert SRT subtitles to plain text for learnmd lesson generation."
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="SRT file(s) or glob pattern(s) to clean. Reads stdin when omitted or set to '-'.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output file. Only valid with one input file.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for cleaned files. Defaults to stdout for stdin or <stem>-cleaned.txt beside each file for file inputs.",
    )
    return parser.parse_args()


def expand_inputs(patterns: list[str]) -> list[Path] | None:
    if not patterns or patterns == ["-"]:
        return None

    paths: list[Path] = []
    missing: list[str] = []

    for pattern in patterns:
        if pattern == "-":
            return None
        matches = [Path(match) for match in glob.glob(pattern)]
        if matches:
            paths.extend(matches)
            continue

        path = Path(pattern)
        if path.exists():
            paths.append(path)
        else:
            missing.append(pattern)

    if missing:
        for pattern in missing:
            print_missing_hint(pattern)
        raise SystemExit(2)

    return sorted(set(paths))


def print_missing_hint(pattern: str) -> None:
    path = Path(pattern)
    parent = path.parent if str(path.parent) != "." else Path.cwd()
    print(f"error: no SRT file matched: {pattern}", file=sys.stderr)
    if not parent.exists():
        print(f"hint: parent directory does not exist: {parent}", file=sys.stderr)
        return

    candidates = [candidate.name for candidate in parent.glob("*.srt")]
    close = difflib.get_close_matches(path.name, candidates, n=5, cutoff=0.35)
    if close:
        print("did you mean:", file=sys.stderr)
        for name in close:
            print(f"  {parent / name}", file=sys.stderr)


def read_input(input_path: Path | None) -> str:
    if input_path is None:
        return sys.stdin.read()
    return input_path.read_text(encoding="utf-8-sig")


def output_path_for(input_path: Path, output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir) / f"{input_path.stem}-cleaned.txt"
    return input_path.with_name(f"{input_path.stem}-cleaned.txt")


def main() -> int:
    args = parse_args()
    input_paths = expand_inputs(args.input)

    if input_paths is None:
        if args.output_dir:
            print("error: --output-dir cannot be used with stdin", file=sys.stderr)
            return 2
        cleaned = clean_srt(read_input(None))
        if args.output:
            Path(args.output).write_text(cleaned + "\n", encoding="utf-8")
        else:
            sys.stdout.write(cleaned)
            if cleaned:
                sys.stdout.write("\n")
        return 0

    if args.output and len(input_paths) != 1:
        print("error: --output can only be used with exactly one input file", file=sys.stderr)
        return 2

    for input_path in input_paths:
        cleaned = clean_srt(read_input(input_path))
        out_path = Path(args.output) if args.output else output_path_for(input_path, args.output_dir)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cleaned + "\n", encoding="utf-8")
        print(f"wrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
