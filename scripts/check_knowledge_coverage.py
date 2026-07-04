#!/usr/bin/env python3
"""Validate a learnmd source-to-course knowledge coverage ledger."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


LEDGER_NAME = "KNOWLEDGE-COVERAGE.md"
VALID_IMPORTANCE = {"required", "optional", "context"}
VALID_STATUS = {"planned", "covered", "omitted", "needs-review"}
REQUIRED_COLUMNS = [
    "ID",
    "Knowledge Point",
    "Source",
    "Importance",
    "Status",
    "Covered In",
    "Treatment",
    "Notes",
]
SOURCE_COLUMNS = ["Source ID", "Source", "Type", "Scope Used", "Notes"]
NAVIGATION_ONLY_FILES = {"index.md", "00-course-map.md"}


@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate KNOWLEDGE-COVERAGE.md for missing or broken course coverage."
    )
    parser.add_argument("workspace", help="Course workspace directory.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser.parse_args()


def extract_coverage_table(text: str) -> tuple[list[str], list[list[str]]]:
    return extract_markdown_table(text, "## Coverage Ledger")


def extract_source_inventory_table(text: str) -> tuple[list[str], list[list[str]]]:
    return extract_markdown_table(text, "## Source Inventory")


def extract_markdown_table(text: str, section_heading: str) -> tuple[list[str], list[list[str]]]:
    in_section = False
    table_lines: list[str] = []
    target = section_heading.strip().lower()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped.startswith("|"):
            table_lines.append(stripped)

    if len(table_lines) < 2:
        return [], []

    header = parse_table_row(table_lines[0])
    rows = [parse_table_row(line) for line in table_lines[2:]]
    return header, rows


def parse_table_row(line: str) -> list[str]:
    trimmed = line.strip().strip("|")
    return [cell.strip() for cell in next(csv.reader([trimmed], delimiter="|"))]


def normalize(value: str) -> str:
    return value.strip().lower()


def existing_markdown_path(workspace: Path, raw_path: str) -> bool:
    clean = raw_path.strip()
    if not clean:
        return False
    clean = clean.split("#", 1)[0].strip()
    if re.match(r"https?://", clean):
        return True

    candidate = workspace / clean
    if candidate.exists() and candidate.is_file():
        return True
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".md")
    return candidate.exists() and candidate.is_file()


def split_covered_in(value: str) -> list[str]:
    return [part.strip() for part in re.split(r";|,", value) if part.strip()]


def validate(workspace: Path) -> list[Finding]:
    findings: list[Finding] = []
    ledger = workspace / LEDGER_NAME

    if not ledger.exists():
        return [Finding("error", f"missing {LEDGER_NAME}")]

    text = ledger.read_text(encoding="utf-8-sig", errors="replace")
    source_header, source_rows = extract_source_inventory_table(text)
    header, rows = extract_coverage_table(text)

    if not source_header:
        findings.append(Finding("error", "missing Source Inventory markdown table"))
    else:
        missing_source_columns = [column for column in SOURCE_COLUMNS if column not in source_header]
        if missing_source_columns:
            findings.append(
                Finding("error", f"Source Inventory missing columns: {', '.join(missing_source_columns)}")
            )
        if not source_rows:
            findings.append(Finding("error", "Source Inventory has no source rows"))

    if not header:
        findings.append(Finding("error", "missing Coverage Ledger markdown table"))
        return findings

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing_columns:
        findings.append(Finding("error", f"Coverage Ledger missing columns: {', '.join(missing_columns)}"))
        return findings

    index = {name: header.index(name) for name in REQUIRED_COLUMNS}
    seen_ids: set[str] = set()

    for line_number, row in enumerate(rows, start=1):
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))

        kp_id = row[index["ID"]].strip()
        point = row[index["Knowledge Point"]].strip()
        importance = normalize(row[index["Importance"]])
        status = normalize(row[index["Status"]])
        covered_in = row[index["Covered In"]].strip()
        treatment = row[index["Treatment"]].strip()
        notes = row[index["Notes"]].strip()

        label = kp_id or f"row {line_number}"

        if not re.fullmatch(r"KP-\d{3,}", kp_id):
            findings.append(Finding("error", f"{label}: ID must look like KP-001"))
        elif kp_id in seen_ids:
            findings.append(Finding("error", f"{label}: duplicate knowledge point ID"))
        seen_ids.add(kp_id)

        if len(point) < 6:
            findings.append(Finding("warning", f"{label}: knowledge point is too vague"))
        if importance not in VALID_IMPORTANCE:
            findings.append(
                Finding("error", f"{label}: invalid Importance '{importance}'")
            )
        if status not in VALID_STATUS:
            findings.append(Finding("error", f"{label}: invalid Status '{status}'"))

        covered_paths = split_covered_in(covered_in)
        if status == "covered":
            if not covered_paths:
                findings.append(Finding("error", f"{label}: status is covered but Covered In is blank"))
            for path_text in covered_paths:
                if not existing_markdown_path(workspace, path_text):
                    findings.append(Finding("error", f"{label}: covered file does not exist: {path_text}"))
            if importance == "required":
                normalized_paths = {
                    Path(path_text.split("#", 1)[0].strip()).as_posix()
                    for path_text in covered_paths
                    if not re.match(r"https?://", path_text)
                }
                if normalized_paths and normalized_paths.issubset(NAVIGATION_ONLY_FILES):
                    findings.append(
                        Finding(
                            "error",
                            f"{label}: required point is covered only by navigation pages, not a lesson/reference",
                        )
                    )

        if importance == "required" and status in {"planned", "needs-review"}:
            findings.append(Finding("error", f"{label}: required point is not covered yet"))
        if importance == "required" and status == "omitted" and not notes:
            findings.append(Finding("error", f"{label}: required point is omitted without a reason"))
        if importance == "required" and status == "covered" and not covered_paths:
            findings.append(Finding("error", f"{label}: required point has no coverage target"))
        if importance == "required" and status == "covered" and normalize(treatment) in {"overview", "summary"}:
            findings.append(
                Finding("warning", f"{label}: required point uses weak treatment '{treatment}'")
            )

    if not rows:
        findings.append(Finding("error", "Coverage Ledger has no knowledge point rows"))

    return findings


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"error: workspace is not a directory: {workspace}", file=sys.stderr)
        return 2

    findings = validate(workspace)
    if not findings:
        print(f"OK: {workspace / LEDGER_NAME} has complete required coverage.")
        return 0

    for finding in findings:
        print(f"{finding.level.upper()}: {finding.message}")

    has_error = any(finding.level == "error" for finding in findings)
    if has_error or args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
