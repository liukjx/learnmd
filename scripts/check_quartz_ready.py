#!/usr/bin/env python3
"""Check a public Quartz course directory for publish-readiness."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PRIVATE_NAMES = {
    "MISSION.md",
    "NOTES.md",
    "RESOURCES.md",
    "learning-records",
    "raw",
    "source",
    "sources",
    "transcripts",
}
SRT_TIMESTAMP_RE = re.compile(
    r"\b\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\b"
)
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
LOCAL_PATH_RE = re.compile(r"(?:file://|/Users/|/Volumes/|~/)")
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
MERMAID_LABEL_DOUBLE_QUOTE_RE = re.compile(r"[\[\(\{][^\]\)\}\n]*\"[^\]\)\}\n]*[\]\)\}]")
MERMAID_LABEL_LIST_RE = re.compile(r"[\[\(\{]\s*(?:\d+\.|[-*+]\s+)[^\]\)\}\n]*[\]\)\}]")
CHAT_STYLE_PROMPT_RE = re.compile(
    r"(想继续吗|有什么问题.*先问|有什么不明白的地方吗|告诉我你的体验|告诉我.*感受|随时.*问)"
)
SENSITIVE_EXAMPLE_RE = re.compile(
    r"(日本帝国主义|帝国主义|纳粹|种族|民族仇恨|政治立场|宗教冲突|性别对立)"
)


@dataclass
class Finding:
    level: str
    path: Path
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a public Quartz course directory before publishing."
    )
    parser.add_argument("path", help="Public Quartz course directory to check.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line or line.startswith((" ", "-")):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def all_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def build_stem_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in markdown_files(root):
        index.setdefault(path.stem, []).append(path)
    return index


def resolve_wikilink(root: Path, current: Path, target: str, stem_index: dict[str, list[Path]]) -> bool:
    target = target.strip()
    if not target:
        return True
    candidates: list[Path] = []

    if "/" in target:
        base = (current.parent / target).resolve()
        root_base = (root / target).resolve()
        candidates.extend(
            [
                base,
                base.with_suffix(".md"),
                base / "index.md",
                root_base,
                root_base.with_suffix(".md"),
                root_base / "index.md",
            ]
        )
    else:
        candidates.extend(stem_index.get(Path(target).stem, []))

    return any(candidate.exists() and candidate.is_file() for candidate in candidates)


def resolve_asset(root: Path, current: Path, target: str) -> bool:
    target = target.strip().strip("<>")
    if not target or "://" in target or target.startswith("#"):
        return True
    target = target.split("#", 1)[0].split("?", 1)[0]
    if target.startswith("/"):
        candidate = root / target.lstrip("/")
    else:
        candidate = current.parent / target
    return candidate.exists()


def check_private_leaks(root: Path, findings: list[Finding]) -> None:
    for path in all_files(root):
        rel = path.relative_to(root)
        if any(part in PRIVATE_NAMES for part in rel.parts):
            findings.append(Finding("error", rel, "private learning file or directory is in public output"))


def check_markdown(root: Path, findings: list[Finding]) -> None:
    stem_index = build_stem_index(root)
    for path in markdown_files(root):
        rel = path.relative_to(root)
        text = read_text(path)
        fm = frontmatter(text)

        if fm is None:
            findings.append(Finding("error", rel, "missing YAML frontmatter"))
        else:
            if not fm.get("title"):
                findings.append(Finding("error", rel, "missing frontmatter title"))
            if not fm.get("description"):
                findings.append(Finding("warning", rel, "missing frontmatter description"))
            if fm.get("draft", "").lower() == "true":
                findings.append(Finding("error", rel, "draft: true page is still in public output"))

        if LOCAL_PATH_RE.search(text):
            findings.append(Finding("error", rel, "contains local absolute path or file:// link"))
        if SRT_TIMESTAMP_RE.search(text):
            findings.append(Finding("error", rel, "contains residual SRT timestamp"))
        if CHAT_STYLE_PROMPT_RE.search(text):
            findings.append(
                Finding(
                    "warning",
                    rel,
                    "contains chat-style prompt; static course pages should end with next steps, review tasks, or self-tests",
                )
            )
        if SENSITIVE_EXAMPLE_RE.search(text):
            findings.append(
                Finding(
                    "warning",
                    rel,
                    "contains potentially sensitive example; prefer a neutral teaching example or explicit instructor attribution",
                )
            )

        for block in MERMAID_BLOCK_RE.findall(text):
            if MERMAID_LABEL_DOUBLE_QUOTE_RE.search(block):
                findings.append(
                    Finding(
                        "warning",
                        rel,
                        "Mermaid label contains ASCII double quotes; use Chinese quotes or remove quotes for Obsidian/Quartz compatibility",
                    )
                )
            if MERMAID_LABEL_LIST_RE.search(block):
                findings.append(
                    Finding(
                        "warning",
                        rel,
                        "Mermaid label looks like a Markdown list; use circled numbers, Step N, or Chinese numbering to avoid Obsidian 'Unsupported markdown: list'",
                    )
                )

        for link_target in WIKILINK_RE.findall(text):
            if not resolve_wikilink(root, path, link_target, stem_index):
                findings.append(Finding("error", rel, f"unresolved wikilink: [[{link_target}]]"))

        for asset_target in MD_IMAGE_RE.findall(text):
            if not resolve_asset(root, path, asset_target):
                findings.append(Finding("error", rel, f"missing linked asset: {asset_target}"))


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: path is not a directory: {root}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    check_private_leaks(root, findings)
    check_markdown(root, findings)

    if not findings:
        print(f"OK: {root} looks Quartz-ready.")
        return 0

    for finding in findings:
        print(f"{finding.level.upper()}: {finding.path}: {finding.message}")

    has_error = any(finding.level == "error" for finding in findings)
    if has_error or args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
