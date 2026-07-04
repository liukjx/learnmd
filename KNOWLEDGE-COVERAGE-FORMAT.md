# KNOWLEDGE-COVERAGE.md Format

`KNOWLEDGE-COVERAGE.md` is the source-to-course coverage ledger for a generated course. It is private by default because it may mention source files, local paths, transcript positions, paid material, or editorial decisions.

Use it when a course is generated from existing material and the user cares whether the course covers all important knowledge points. For source-derived course notes, this ledger is mandatory: it prevents a broad course overview from being mistaken for full course coverage.

## Template

```md
# Knowledge Coverage

## Source Inventory

| Source ID | Source | Type | Scope Used | Notes |
|---|---|---|---|---|
| SRC-001 | cleaned/transcript-01.txt | transcript | full file | Intro and core definitions |

## Coverage Ledger

| ID | Knowledge Point | Source | Importance | Status | Covered In | Treatment | Notes |
|---|---|---|---|---|---|---|---|
| KP-001 | A concise concept, procedure, distinction, warning, or skill | SRC-001 00:03:12-00:07:40 | required | covered | lessons/0001-example.md; reference/glossary.md | explain + practice |  |
| KP-002 | A duplicate or off-mission point | SRC-001 00:11:00-00:12:30 | optional | omitted |  | omit | Duplicate of KP-001 |

## Coverage Summary

- Required covered:
- Required pending:
- Optional covered:
- Optional omitted:
- Known risks:
- Source files inventoried:
- Source files not yet extracted:
```

## Rules

- **One row per distinct teachable unit.** Track concepts, procedures, distinctions, warnings, examples that carry a reusable pattern, and practice skills.
- **Inventory comes first.** Every in-scope source file, day, module, transcript batch, slide deck, notebook, or code group must appear in Source Inventory before final lessons are drafted.
- **Default to required for source lessons.** If a source lesson teaches a reproducible concept, procedure, code pattern, platform operation, environment step, project workflow, warning, or debugging technique, mark it `required` unless there is a concrete omission reason.
- **Do not track filler.** Greetings, transitions, anecdotes with no teaching value, repeated phrasing, and production noise do not need rows.
- **Use stable IDs.** Do not renumber existing `KP-*` rows once lessons reference them.
- **Importance values:** `required`, `optional`, or `context`.
- **Status values:** `planned`, `covered`, `omitted`, or `needs-review`.
- **Covered In:** use course-relative Markdown paths separated by semicolons. Leave blank only when status is `planned`, `omitted`, or `needs-review`.
- **Treatment:** write how the course handles the point, such as `explain`, `worked example`, `exercise`, `reference`, `glossary`, `diagram`, `self-test`, or `omit`.
- **Required points must not be omitted silently.** If a required point is omitted, explain why in `Notes`.
- **Resolve vague rows.** If a row says only "important idea" or "miscellaneous discussion", split it until a future reviewer can tell what was covered.
- **Do not let navigation count as coverage.** `index.md`, `00-course-map.md`, and broad module overview pages may orient the learner, but required source points should be covered in concrete lessons or reference files.
- **Compression must be auditable.** If several source lessons are merged into one lesson, each merged source point still needs its own `KP-*` row pointing to the merged lesson and a treatment that shows how it is handled.
- **Large courses may be incomplete, but not ambiguous.** If extraction or drafting is unfinished, mark the affected rows or source groups as `planned` or `needs-review` and list the risk in Coverage Summary.

## Extraction Granularity

Use one `KP-*` row for each:

- named concept, model, API, command, class, method, configuration option, or platform feature;
- demonstrated workflow or operation that the learner may need to reproduce;
- code walkthrough, notebook step, project module, integration boundary, or deployment step;
- comparison, decision rule, caveat, failure mode, troubleshooting step, or best practice;
- exercise, assignment, or self-test pattern that reinforces the source lesson.

Do not use one row for an entire day or chapter unless that source truly contains only one teachable idea.
