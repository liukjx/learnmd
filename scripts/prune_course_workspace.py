#!/usr/bin/env python3
"""Prune non-public clutter from a learnmd course workspace."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


APPLEDOUBLE_PREFIX = "._"
DEFAULT_PRIVATE_FILES = {
    "MISSION.md",
    "NOTES.md",
    "RESOURCES.md",
}
DEFAULT_PRIVATE_DIRS = {
    "learning-records",
}
CLEANED_DIRS = {
    "cleaned",
    ".learnmd/cleaned",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove AppleDouble metadata and optional intermediate/private learnmd files."
    )
    parser.add_argument("workspace", help="Course workspace directory.")
    parser.add_argument(
        "--drop-cleaned",
        action="store_true",
        help="Remove cleaned transcript directories such as cleaned/ and .learnmd/cleaned/.",
    )
    parser.add_argument(
        "--drop-private-state",
        action="store_true",
        help="Remove personal learning state files such as MISSION.md, NOTES.md, RESOURCES.md, and learning-records/.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete files. Without this flag, only print planned deletions.",
    )
    return parser.parse_args()


def collect_appledouble(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob(f"{APPLEDOUBLE_PREFIX}*") if path.exists())


def collect_cleaned(root: Path) -> list[Path]:
    return sorted(path for name in CLEANED_DIRS if (path := root / name).exists())


def collect_private_state(root: Path) -> list[Path]:
    paths: list[Path] = []
    paths.extend(root / name for name in DEFAULT_PRIVATE_FILES if (root / name).exists())
    paths.extend(root / name for name in DEFAULT_PRIVATE_DIRS if (root / name).exists())
    return sorted(paths)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def remove_descendants(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    for path in sorted(paths, key=lambda item: (len(item.parts), item.as_posix())):
        if any(parent == path or parent in path.parents for parent in result):
            continue
        result.append(path)
    return sorted(result)


def main() -> int:
    args = parse_args()
    root = Path(args.workspace).resolve()
    if not root.is_dir():
        print(f"error: workspace is not a directory: {root}", file=sys.stderr)
        return 2

    planned: list[Path] = []
    planned.extend(collect_appledouble(root))
    if args.drop_cleaned:
        planned.extend(collect_cleaned(root))
    if args.drop_private_state:
        planned.extend(collect_private_state(root))

    unique = remove_descendants(list(set(planned)))
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"{mode}: prune {root}")
    if not unique:
        print("No matching clutter found.")
        return 0

    for path in unique:
        print(f"delete {path.relative_to(root)}")
        if args.apply:
            remove_path(path)

    if not args.apply:
        print("Dry-run only. Re-run with --apply to delete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
