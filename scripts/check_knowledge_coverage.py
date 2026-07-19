#!/usr/bin/env python3
"""Validate a learnmd source-to-course knowledge coverage ledger."""

from __future__ import annotations

import argparse
import csv
import difflib
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
CJK_RE = re.compile(r"[\u3400-\u9fff]+")
ASCII_TOKEN_RE = re.compile(r"[a-z0-9_][a-z0-9_./:#-]{1,}")


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
    parser.add_argument(
        "--no-evidence-scan",
        action="store_true",
        help="Only validate ledger structure and file paths; skip note-text evidence checks.",
    )
    parser.add_argument(
        "--evidence-threshold",
        type=float,
        default=0.22,
        help="Minimum lightweight semantic evidence score for covered rows. Default: 0.22.",
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


def strip_markdown_noise(text: str) -> str:
    text = re.sub(r"\A---\s*\n.*?\n---\s*", " ", text, flags=re.DOTALL)
    text = re.sub(r"```[^\n]*\n", "\n", text)
    text = text.replace("```", " ")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    text = re.sub(r"[#>*_~|]", " ", text)
    return text


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def tokenize(value: str) -> set[str]:
    lowered = value.lower()
    tokens = set(ASCII_TOKEN_RE.findall(lowered))

    for match in CJK_RE.findall(lowered):
        if len(match) == 1:
            tokens.add(match)
            continue
        if len(match) <= 8:
            tokens.add(match)
        for size in (2, 3):
            if len(match) >= size:
                tokens.update(match[i : i + size] for i in range(len(match) - size + 1))

    return {token for token in tokens if token.strip()}


def chunk_text(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n|(?=^#{1,6}\s)", text, flags=re.MULTILINE) if part.strip()]
    chunks: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= 1600:
            chunks.append(paragraph)
            continue
        for start in range(0, len(paragraph), 1200):
            chunks.append(paragraph[start : start + 1600])

    return chunks or [text]


def evidence_score(point: str, text: str) -> float:
    point_clean = strip_markdown_noise(point)
    text_clean = strip_markdown_noise(text)

    if not point_clean.strip() or not text_clean.strip():
        return 0.0
    if normalize_text(point_clean) in normalize_text(text_clean):
        return 1.0

    point_tokens = tokenize(point_clean)
    if not point_tokens:
        return 0.0

    doc_tokens = tokenize(text_clean)
    doc_overlap = len(point_tokens & doc_tokens) / len(point_tokens)
    best_chunk = 0.0

    for chunk in chunk_text(text_clean):
        chunk_tokens = tokenize(chunk)
        if not chunk_tokens:
            continue
        overlap = len(point_tokens & chunk_tokens) / len(point_tokens)
        ratio = difflib.SequenceMatcher(None, normalize_text(point_clean), normalize_text(chunk)[:1200]).ratio()
        best_chunk = max(best_chunk, (overlap * 0.85) + (ratio * 0.15))

    return max(best_chunk, doc_overlap * 0.75)


def best_coverage_evidence(workspace: Path, covered_paths: list[str], point: str) -> tuple[float, str]:
    best_score = 0.0
    best_path = ""

    for path_text in covered_paths:
        if re.match(r"https?://", path_text):
            continue
        clean = path_text.split("#", 1)[0].strip()
        candidate = workspace / clean
        if candidate.suffix == "":
            candidate = candidate.with_suffix(".md")
        if not candidate.exists() or not candidate.is_file():
            continue

        try:
            text = candidate.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

        score = evidence_score(point, text)
        if score > best_score:
            best_score = score
            best_path = path_text

    return best_score, best_path


def validate(workspace: Path, evidence_scan: bool = True, evidence_threshold: float = 0.22) -> list[Finding]:
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
            if evidence_scan and covered_paths:
                score, best_path = best_coverage_evidence(workspace, covered_paths, point)
                if score < evidence_threshold:
                    suffix = f" best score {score:.2f}"
                    if best_path:
                        suffix += f" in {best_path}"
                    findings.append(
                        Finding(
                            "warning",
                            f"{label}: weak textual evidence that Covered In actually covers the knowledge point;{suffix}",
                        )
                    )
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

    findings = validate(
        workspace,
        evidence_scan=not args.no_evidence_scan,
        evidence_threshold=args.evidence_threshold,
    )
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
