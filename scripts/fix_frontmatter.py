#!/usr/bin/env python3
"""Conservatively normalize Markdown frontmatter for Quartz publishing."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix common learnmd frontmatter issues.")
    parser.add_argument("path", help="Markdown file or directory.")
    parser.add_argument(
        "--add-description",
        help="Description to add when a Markdown file has no description.",
    )
    parser.add_argument(
        "--fix-mermaid",
        action="store_true",
        help="Also replace risky Mermaid label syntax: ASCII quotes and leading '1.' list labels.",
    )
    parser.add_argument("--apply", action="store_true", help="Write changes. Dry-run by default.")
    return parser.parse_args()


def markdown_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix == ".md" else []
    return sorted(path.rglob("*.md"))


def split_frontmatter(text: str) -> tuple[list[str], str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[3:end].strip("\n").splitlines(), text[end + 4 :].lstrip("\n")


def has_key(lines: list[str], key: str) -> bool:
    return any(line.startswith(f"{key}:") for line in lines)


def normalize_frontmatter(text: str, description: str | None) -> tuple[str, list[str]]:
    split = split_frontmatter(text)
    if split is None:
        return text, []

    lines, body = split
    changes: list[str] = []
    new_lines: list[str] = []
    date_value: str | None = None

    for line in lines:
        if line.startswith("created:"):
            date_value = line.split(":", 1)[1].strip()
            changes.append("created -> date")
            continue
        if line.startswith("status: draft"):
            changes.append("remove status: draft")
            continue
        new_lines.append(line)

    if date_value and not has_key(new_lines, "date"):
        new_lines.append(f"date: {date_value}")
    if not has_key(new_lines, "draft"):
        new_lines.append("draft: false")
        changes.append("add draft: false")
    if description and not has_key(new_lines, "description"):
        insert_at = 1 if new_lines and new_lines[0].startswith("title:") else len(new_lines)
        new_lines.insert(insert_at, f'description: "{description}"')
        changes.append("add description")

    return "---\n" + "\n".join(new_lines) + "\n---\n\n" + body, changes


def fix_mermaid_block(block: str) -> str:
    block = block.replace('"', "”")
    block = re.sub(r"([\[\(\{])\s*(\d+)\.\s+", r"\1\2、", block)
    return block


def fix_mermaid(text: str) -> tuple[str, bool]:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        fixed = fix_mermaid_block(match.group(1))
        if fixed != match.group(1):
            changed = True
        return "```mermaid\n" + fixed + "```"

    return MERMAID_BLOCK_RE.sub(replace, text), changed


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    files = markdown_files(root)

    for path in files:
        original = path.read_text(encoding="utf-8-sig", errors="replace")
        updated, changes = normalize_frontmatter(original, args.add_description)
        if args.fix_mermaid:
            updated, mermaid_changed = fix_mermaid(updated)
            if mermaid_changed:
                changes.append("fix mermaid compatibility")

        if not changes:
            continue

        print(f"{path}: {', '.join(changes)}")
        if args.apply:
            path.write_text(updated, encoding="utf-8")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
