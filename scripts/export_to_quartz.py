#!/usr/bin/env python3
"""Export public learnmd course files into a Quartz content directory."""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path


PRIVATE_FILES = {
    "MISSION.md",
    "NOTES.md",
    "RESOURCES.md",
    "GLOSSARY-FORMAT.md",
    "LEARNING-RECORD-FORMAT.md",
    "MISSION-FORMAT.md",
    "RESOURCES-FORMAT.md",
}
PRIVATE_DIRS = {
    ".git",
    ".obsidian",
    ".trash",
    "learning-records",
    "raw",
    "source",
    "sources",
    "transcripts",
}
PUBLIC_ROOT_FILES = {"index.md", "00-course-map.md"}
PUBLIC_DIRS = {"lessons", "reference", "assets"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy public learnmd course files into a Quartz content course folder."
    )
    parser.add_argument("source", help="Course workspace directory.")
    parser.add_argument(
        "--target",
        help="Quartz course output directory, e.g. /Users/.../blogs/content/courses/course-slug.",
    )
    parser.add_argument(
        "--content-root",
        default="/Users/lishaojie/Documents/blogs/content/courses",
        help="Quartz courses root used when --target is omitted.",
    )
    parser.add_argument(
        "--slug",
        help="Course slug used with --content-root. Defaults to the source directory name.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write files. Without this flag, only print planned actions.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete target files that are not part of the public source set. Requires --apply.",
    )
    return parser.parse_args()


def is_draft_true(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    frontmatter = text[3:end]
    return re.search(r"(?mi)^\s*draft\s*:\s*true\s*$", frontmatter) is not None


def is_private_path(relative_path: Path) -> bool:
    parts = set(relative_path.parts)
    return (
        relative_path.name in PRIVATE_FILES
        or any(part in PRIVATE_DIRS for part in parts)
        or relative_path.name.startswith(".")
    )


def is_public_path(source: Path, path: Path) -> bool:
    rel = path.relative_to(source)
    if is_private_path(rel):
        return False
    if rel.name.endswith(".srt"):
        return False
    if rel.parts[0] in PUBLIC_DIRS:
        return not (path.suffix == ".md" and is_draft_true(path))
    if len(rel.parts) == 1 and rel.name in PUBLIC_ROOT_FILES:
        return not (path.suffix == ".md" and is_draft_true(path))
    return False


def collect_public_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in source.rglob("*"):
        if path.is_file() and is_public_path(source, path):
            files.append(path)
    return sorted(files)


def file_needs_copy(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    if src.stat().st_size != dst.stat().st_size:
        return True
    return not filecmp.cmp(src, dst, shallow=False)


def main() -> int:
    args = parse_args()
    source = Path(args.source).resolve()
    if not source.is_dir():
        print(f"error: source is not a directory: {source}", file=sys.stderr)
        return 2

    if args.target:
        target = Path(args.target).resolve()
    else:
        slug = args.slug or source.name
        target = (Path(args.content_root) / slug).resolve()

    if args.delete and not args.apply:
        print("error: --delete requires --apply", file=sys.stderr)
        return 2

    public_files = collect_public_files(source)
    expected_targets = {target / path.relative_to(source) for path in public_files}

    actions: list[tuple[str, Path, Path | None]] = []
    for src in public_files:
        dst = target / src.relative_to(source)
        if file_needs_copy(src, dst):
            actions.append(("copy", src, dst))

    if args.delete and target.exists():
        for dst in sorted(path for path in target.rglob("*") if path.is_file()):
            if dst not in expected_targets:
                actions.append(("delete", dst, None))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"{mode}: {source} -> {target}")
    if not actions:
        print("No changes.")
        return 0

    for action, src, dst in actions:
        if action == "copy":
            print(f"copy   {src.relative_to(source)} -> {dst}")
            if args.apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        elif action == "delete":
            print(f"delete {src}")
            if args.apply:
                src.unlink()

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
