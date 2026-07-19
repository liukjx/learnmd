#!/usr/bin/env python3
"""Create a Quartz-ready learnmd lesson file with a standard skeleton."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a Quartz-ready lesson.")
    parser.add_argument("workspace", help="Course workspace directory.")
    parser.add_argument("--title", required=True, help="Lesson title.")
    parser.add_argument("--slug", required=True, help="Dash-cased filename slug without .md.")
    parser.add_argument("--description", required=True, help="Quartz description.")
    parser.add_argument(
        "--tags",
        default="course",
        help="Comma-separated tags. Defaults to 'course'.",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Publication date in YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--dir",
        default="lessons",
        help="Output subdirectory under workspace. Defaults to lessons.",
    )
    parser.add_argument(
        "--number",
        type=int,
        default=None,
        help="Standard lesson number. When provided, auto-prepends '第NN课：' and requires slug prefix NNNN-.",
    )
    parser.add_argument(
        "--supplement-number",
        type=int,
        default=None,
        help="Supplemental lesson number. Auto-prepends '补充课NN：' and requires slug prefix sNN-.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing file.",
    )
    return parser.parse_args()


def validate_slug(slug: str) -> None:
    if not re.fullmatch(r"[0-9a-z][0-9a-z-]*", slug):
        raise SystemExit("error: --slug must be lowercase dash-case letters/digits/hyphens")


def validate_numbering(args: argparse.Namespace) -> None:
    if args.number is not None and args.supplement_number is not None:
        raise SystemExit("error: use either --number or --supplement-number, not both")
    if args.number is not None:
        expected = f"{args.number:04d}-"
        if not args.slug.startswith(expected):
            raise SystemExit(f"error: --number {args.number} requires --slug to start with {expected}")
    if args.supplement_number is not None:
        expected = f"s{args.supplement_number:02d}-"
        if not args.slug.startswith(expected):
            raise SystemExit(
                f"error: --supplement-number {args.supplement_number} requires --slug to start with {expected}"
            )


def parse_tags(raw: str) -> list[str]:
    tags = [tag.strip() for tag in raw.split(",") if tag.strip()]
    return tags or ["course"]


def render_frontmatter(title: str, description: str, lesson_date: str, tags: list[str]) -> str:
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "{description}"\n'
        f"date: {lesson_date}\n"
        "tags:\n"
        f"{tag_lines}\n"
        "draft: false\n"
        "---\n"
    )


def render_lesson(args: argparse.Namespace) -> str:
    tags = parse_tags(args.tags)
    title = args.title
    if args.number is not None:
        title = f"第{args.number:02d}课：{title}"
    elif args.supplement_number is not None:
        title = f"补充课{args.supplement_number:02d}：{title}"
    return (
        render_frontmatter(title, args.description, args.date, tags)
        + "\n"
        + f"# {title}\n\n"
        + "## Learning Objectives\n"
        + "- \n"
        + "- \n\n"
        + "## Core Idea\n\n"
        + "...\n\n"
        + "> [!TIP] Key Insight\n"
        + "> ...\n\n"
        + "## Worked Example\n\n"
        + "...\n\n"
        + "## Practice\n\n"
        + "> [!QUESTION] Self-check\n"
        + "> ...\n\n"
        + "<details>\n"
        + "<summary>Reveal answer</summary>\n\n"
        + "...\n"
        + "</details>\n\n"
        + "## Next Step\n\n"
        + "Continue with the next lesson or complete the review task above before moving on.\n"
    )


def main() -> int:
    args = parse_args()
    validate_slug(args.slug)
    validate_numbering(args)

    workspace = Path(args.workspace).resolve()
    output_dir = workspace / args.dir
    output_path = output_dir / f"{args.slug}.md"

    if output_path.exists() and not args.force:
        raise SystemExit(f"error: file already exists: {output_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_lesson(args), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
