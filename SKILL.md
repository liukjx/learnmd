---
name: learnmd
description: Create stateful Obsidian-friendly Markdown learning workspaces and minimal Quartz/blog-ready course notes, especially full-coverage course notes from source materials. Use when the user wants multi-session learning notes, full course generation, complete course knowledge-point extraction, SRT/PDF/doc/slide-to-lesson conversion, source-to-note coverage audits, Obsidian study materials, or Quartz/blog-ready course publishing. For source-derived courses, default to exhaustive knowledge-point coverage, not a course overview or learning-path summary.
---

The user has asked you to teach them something. This is a stateful request — they intend to learn the topic over multiple sessions. All lessons are generated as **Obsidian-friendly Markdown** files.

## Working with Source Materials

Users may provide course subtitles in SRT format as source material. SRT files contain timestamps and sequence numbers that are not useful for lesson generation.

### SRT Processing

When given an SRT file, clean it with the bundled `scripts/clean_srt.py` before generating lessons, reference documents, or glossary entries. Resolve the script path relative to this `SKILL.md`, not relative to the teaching workspace:

```bash
python3 <skill-dir>/scripts/clean_srt.py path/to/subtitles.srt -o path/to/cleaned.txt
```

The script removes sequence numbers, timestamp lines, and blank gaps, then joins subtitle text into lesson-ready plain text. It accepts stdin when no input file is provided, and it supports glob patterns and batch output:

```bash
python3 <skill-dir>/scripts/clean_srt.py "*.srt" --output-dir .learnmd/cleaned/
```

Example SRT input:
```
1
00:00:01,500 --> 00:00:05,200
The derivative represents the instantaneous
rate of change of a function.

2
00:00:05,500 --> 00:00:09,800
We can think of it as the slope of
the tangent line at any given point.
```

After processing → plain text:
```
The derivative represents the instantaneous rate of change of a function. We can think of it as the slope of the tangent line at any given point.
```

## Teaching Workspace

Treat the **session start directory** as the learning home — always use the directory where the user launched the session, not any directory that happens to be current during the conversation.

When creating a new course or multi-lesson workspace, create it under a dedicated course notes directory:

```text
<session-start-directory>/课程笔记/<course-slug>/
```

Use a short dash-cased `course-slug` derived from the course topic unless the user provides a name. Create `课程笔记/` lazily, only when a new course workspace is needed. If the user is continuing an existing course, use the existing course workspace rather than creating a duplicate.

The state of each course is captured inside its course workspace in several files:

- `MISSION.md`: A document capturing the _reason_ the user is interested in the topic. This should be used to ground all teaching. Use the format in [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `./reference/*.md`: A directory of reference materials. These are the compressed learnings from the lessons — cheat sheets, reference algorithms, syntax, glossaries. They are designed for quick reference and review in Obsidian. They use Markdown formatting with LaTeX formulas, Mermaid diagrams, and callout blocks as appropriate.
- `RESOURCES.md`: A list of resources which can be explored to ground your teaching in contextual knowledge, or to acquire knowledge and wisdom. Use the format in [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `./learning-records/*.md`: A directory of learning records, which capture what the user has learned. These are loosely equivalent to architectural decision records in software development — they capture non-obvious lessons and key insights that may need to be revised later, or drive future sessions. These should be used to calculate the zone of proximal development. They are titled `0001-<dash-case-name>.md`, where the number increments each time. Use the format in [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `./lessons/*.md`: A directory of lessons. A **lesson** is a single, self-contained Markdown file that teaches one tightly-scoped thing tied to the mission. This is the primary unit of teaching in this workspace. Lessons are designed to be read and studied in Obsidian.
- `./assets/*`: Reusable **components** shared across lessons — Mermaid diagram templates, CSS snippets for Obsidian, shared LaTeX macros, etc. See [Assets](#assets).
- `NOTES.md`: A scratchpad for you to jot down user preferences, or working notes.

Private learning state and public course output are different things. Treat `MISSION.md`, `NOTES.md`, `RESOURCES.md`, and `./learning-records/` as private by default. Publish only lesson content, selected public references, course index/map pages, and assets that are intentionally safe for the reader.

### Blog-Ready Minimal Mode

When the user says the result will be published as a blog, Quartz site, or copied into `/Users/lishaojie/Documents/blogs/content`, default to a minimal public output surface:

- Create public files only when they are useful to readers: `index.md`, `00-course-map.md`, `lessons/*.md`, `reference/*.md`, and referenced `assets/*`.
- Keep mandatory audit files private and out of Quartz export. `KNOWLEDGE-COVERAGE.md` may remain in the course workspace root for checking, but it must not be copied manually into the blog content tree.
- Do not create `MISSION.md`, `NOTES.md`, `RESOURCES.md`, `learning-records/`, or a CSS asset unless the user is using this as an ongoing personal learning workspace or the file is needed for the task.
- Put generated intermediate source text under `.learnmd/cleaned/` instead of a public-looking `cleaned/` directory. Do not publish `.learnmd/`, `cleaned/`, raw transcripts, source PDFs, or AppleDouble `._*` files.
- If the user wants a clean handoff after generation, run the workspace pruner in dry-run mode first, then apply only after reviewing the planned deletions:

```bash
python3 <skill-dir>/scripts/prune_course_workspace.py <course-workspace> --drop-cleaned
python3 <skill-dir>/scripts/prune_course_workspace.py <course-workspace> --drop-cleaned --apply
```

For blog publishing, prefer the bundled Quartz exporter over manual copying. It copies only the public whitelist and avoids private state:

```bash
python3 <skill-dir>/scripts/export_to_quartz.py <course-workspace> \
  --target /Users/lishaojie/Documents/blogs/content/courses/<course-slug> \
  --apply
```

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources
- **Skills**, acquired through highly-relevant interactive lessons devised by you, based on the knowledge
- **Wisdom**, which comes from interacting with other learners and practitioners

Before the `RESOURCES.md` is well-populated, your focus should be to find high-quality resources which will help the user acquire knowledge. Never trust your parametric knowledge.

Some topics may require more skills than knowledge. Learning more about theoretical physics might be more knowledge-based. For yoga, more skills-based.

### Fluency vs Storage Strength

You should be careful to split between two types of learning:

- **Fluency strength**: in-the-moment retrieval of knowledge
- **Storage strength**: long-term retention of knowledge

Fluency can give the user an illusory sense of mastery, but storage strength is the real goal. Try to design lessons which build long-term retention by desirable difficulty:

- Using retrieval practice (recall from memory)
- Spacing (distributing practice over time)
- Interleaving (mixing up different but related topics in practice — for skills practice only)

## Obsidian Markdown Standards

Generated content must be clean, well-structured Markdown that renders well in Obsidian. When creating or revising any lesson or reference document, read [references/obsidian-markdown.md](./references/obsidian-markdown.md) and choose formats based on the knowledge shape.

Keep the style rich but purposeful:

- Use YAML frontmatter for lessons.
- Use ATX headings without skipping levels.
- Use `[[wikilinks]]` to connect lessons and reference documents.
- Use callouts for key insights, warnings, examples, and retrieval prompts.
- Use LaTeX for mathematical precision.
- Use Mermaid diagrams for processes, relationships, sequences, states, and concept maps.
- Use tables for comparisons and quick lookup.
- Use fenced code blocks with language tags.
- Use footnotes for citations and asides.
- Use `<details>` blocks for hidden answers and worked solutions.

Do not use every format in every lesson. Pick the few formats that make the idea easier to understand, review, or recall.

## Full Course Generation

Default to **full source coverage** when the user asks to generate course notes from existing course material, subtitles, lecture recordings, slide decks, PDFs, code, notebooks, or a course directory. A full course is not a course overview. `index.md`, `00-course-map.md`, and learning-path summaries are only navigation pages; they do not count as the course content.

In full source coverage mode:

- Preserve the source course's module/day/lesson granularity unless the user explicitly asks to compress it.
- Generate notes that account for every teachable concept, procedure, command, code pattern, warning, example pattern, assignment, environment step, troubleshooting point, and project workflow found in the sources.
- Do not skip foundational modules such as Git, Linux, MySQL, Docker, FastAPI, or data structures merely because the learner may already know them. If the mission makes them lower priority, mark them as quick-review coverage, not omitted.
- Do not merge many source lessons into one broad overview unless the coverage ledger proves every source knowledge point is still covered in a lesson or reference.
- Prefer many focused lessons or module/day notes over a small set of high-level essays when source volume is large.
- Treat omissions as explicit editorial decisions recorded in `KNOWLEDGE-COVERAGE.md`, never as silent compression.

When the user asks for a full course, create a course workspace before writing individual lessons:

- `index.md`: public course landing page with audience, outcome, prerequisites, and lesson links.
- `00-course-map.md`: public course map showing the learning path and dependencies.
- `KNOWLEDGE-COVERAGE.md`: private source-to-course coverage ledger. Use the format in [KNOWLEDGE-COVERAGE-FORMAT.md](./KNOWLEDGE-COVERAGE-FORMAT.md).
- `lessons/*.md`: numbered lessons using stable, dash-cased filenames.
- `reference/*.md`: selected public review material such as glossary, cheat sheets, formulas, commands, or diagrams.
- `assets/*`: only assets referenced by public Markdown.

Generate the course from a plan, not lesson-by-lesson improvisation. First inventory all source files, extract the knowledge coverage ledger, outline modules, lesson sequence, prerequisites, references, practice progression, and source-material coverage. Then write lessons in order and keep cross-links consistent.

Before drafting any final lesson from source material, create `KNOWLEDGE-COVERAGE.md` with:

- a complete source inventory covering every source file considered in scope;
- stable `SRC-*` IDs for source files or source groups;
- stable `KP-*` IDs for extracted knowledge points;
- a planned target lesson/reference for each required knowledge point.

If the source corpus is too large to finish in one run, create the coverage ledger and mark unfinished rows or modules as `planned`/`needs-review` rather than pretending the course is complete.

### Multi-Agent Course Generation

For short lesson work, single-lesson revisions, or a small sequence of up to three lessons, keep the work in the main agent. The overhead of delegation is not worth it.

For full courses, complex source material, more than five planned lessons, multiple transcripts/PDFs/books, or Quartz-ready course publishing, use subagents when available. The main agent remains the editor-in-chief: it owns the mission fit, course structure, terminology, file naming, cross-links, final quality bar, and all final writes.

Use subagents for bounded work products, not open-ended course ownership:

- **Source extractor**: extract teachable knowledge points from source material into a draft `KNOWLEDGE-COVERAGE.md`.
- **Curriculum planner**: propose modules, lesson sequence, prerequisites, practice progression, and reference documents from the mission and coverage ledger.
- **Lesson drafter**: draft a limited batch of lessons, usually two or three at a time, from the approved plan and coverage rows.
- **Coverage reviewer**: compare drafted lessons against `KNOWLEDGE-COVERAGE.md` and flag missing, duplicated, vague, or weakly covered required points.
- **Markdown/publishing reviewer**: check Obsidian structure, YAML frontmatter, wikilinks, Mermaid, static lesson endings, public/private separation, and Quartz readiness.

Do not let multiple subagents independently invent the course shape. Give each subagent the relevant mission, source scope, coverage rows, file conventions, and acceptance criteria. Merge their work only after checking consistency with `MISSION.md`, `RESOURCES.md`, `GLOSSARY.md`, `KNOWLEDGE-COVERAGE.md`, and existing lessons.

Before treating a delegated course as complete, the main agent must run the deterministic checkers described below and resolve failures. Subagent review is a quality gate, not a substitute for scripts.

### Source Coverage Discipline

When generating a course from source material such as transcripts, books, articles, notes, PDFs, or slide decks, do not rely on the lesson outline alone to imply completeness. Build an explicit source-to-course coverage ledger before drafting lessons:

1. Inventory every in-scope source file before extraction. For directories, list module/day/lesson source groups so missing days are visible.
2. Extract every distinct teachable knowledge point from the source material into `KNOWLEDGE-COVERAGE.md`.
3. Give each item a stable ID such as `KP-001`, a concise name, source location, importance, and intended treatment.
4. Map each knowledge point to one or more lesson or reference files before writing the final course.
5. Mark truly skipped material as `omitted`, and record the reason. Acceptable reasons include off-mission, duplicate, prerequisite already assumed, too shallow to teach, unsafe/private for public output, or already covered verbatim by an upstream reference. Do not use "overview", "too much content", or "learner probably knows this" as an omission reason for required source material.
6. After lessons are drafted, update the ledger with the actual files that cover each point.
7. Before treating the course as done, run the bundled coverage checker and resolve missing required coverage:

```bash
python3 <skill-dir>/scripts/check_knowledge_coverage.py <course-workspace>
```

The goal is not to mechanically reproduce every sentence in the source. The goal is to account for every distinct concept, procedure, distinction, warning, example pattern, and practice skill so omissions are intentional and visible.

### Coverage Audit Loop

Use a closed extraction-to-audit loop for source-derived courses. Do not mark a course complete after drafting notes unless the ledger and the note text agree.

1. Extract atomic `KP-*` rows before drafting final lessons. The row text should be specific enough that another reviewer can search for it in the final notes.
2. Draft lessons and references from the ledger, not only from a high-level outline.
3. After drafting, update `Covered In` with the actual lesson/reference paths that cover each point.
4. Run the bundled checker in strict mode with its default note-text evidence scan:

```bash
python3 <skill-dir>/scripts/check_knowledge_coverage.py <course-workspace> --strict
```

5. For every missing or weak-evidence finding, inspect the source row and target note:
   - If the point is relevant and teachable, add it to the most fitting lesson/reference and rerun the checker.
   - If the point is off-mission, duplicate, logistics-only, unsafe/private, or not reusable teaching content, set `Status` to `omitted` and write the specific reason in `Notes`.
   - If the source is ambiguous or too shallow to teach responsibly, set `Status` to `needs-review` and summarize the uncertainty in `Notes`.

The checker uses deterministic local text evidence rather than a full embedding database, so it can produce false positives when the note paraphrases heavily. Treat a weak-evidence warning as a required human/LLM review item: either strengthen the note with explicit terminology, improve the `Knowledge Point` wording, or record why the row is intentionally omitted/needs-review. Do not silence warnings by pointing many rows at broad overview pages.

For lecture-style courses, use this extraction granularity:

- one row for each named concept, API, command, algorithm, model, workflow node, platform feature, or configuration field;
- one row for each demonstrated procedure or code walkthrough that a learner may need to reproduce;
- one row for each important comparison, caveat, error case, debugging step, or deployment detail;
- one row for each project workflow step and integration boundary;
- no rows for greetings, repeated transitions, logistics, or anecdotes with no reusable teaching value.

Quality bar for a complete source-derived course:

- every in-scope source file appears in the source inventory;
- every required knowledge point is `covered`;
- every `covered` row points to an existing Markdown lesson or reference;
- every omitted required point has a specific reason;
- no lesson is only a high-level summary when its coverage rows require procedures, code, commands, or project steps;
- `python3 <skill-dir>/scripts/check_knowledge_coverage.py <course-workspace> --strict` exits successfully.

Use the bundled lesson scaffold for new lesson files so Quartz frontmatter is complete from the start. For numbered lessons, the filename number and display title number have different jobs:

- lesson filenames must start with a four-digit order key: `0001-<dash-case-name>.md`, `0002-...`, `0032-...`;
- lesson display titles and page H1 must start with a two-digit Chinese prefix for lessons 1-99: `第01课：...`, `第02课：...`, `第32课：...`;
- never mix display title forms such as `第1课`, `第 1 课`, `第0001课`, or `第0027课`;
- supplemental lessons must use filenames like `s01-<dash-case-name>.md` and display titles like `补充课01：...`; do not use `第S07课`.

```bash
python3 <skill-dir>/scripts/scaffold_lesson.py <course-workspace> \
  --title "NLP到底是什么？" \
  --slug 0001-nlp-shi-shen-me \
  --number 1 \
  --tags nlp,module-1 \
  --description "NLP的定义、起源、三个好学问标准"
```

## Quartz Publishing

When the user wants to move a course into a Quartz blog, read [references/quartz-publishing.md](./references/quartz-publishing.md) before changing or exporting files.

Default Quartz target pattern:

```bash
/Users/lishaojie/Documents/blogs/content/courses/<course-slug>
```

Do not overwrite `/Users/lishaojie/Documents/blogs/content/index.md`; that is the site home page. Each course should usually have its own `index.md`, but child directories such as `lessons/` and `reference/` do not need `index.md` unless a custom landing page is useful.

Use the bundled exporter for public course output:

```bash
python3 <skill-dir>/scripts/export_to_quartz.py <course-workspace> \
  --target /Users/lishaojie/Documents/blogs/content/courses/<course-slug>
```

The exporter is dry-run by default. Add `--apply` only after reviewing the planned copies. Add `--delete` only when the target should mirror the current public source set.

After export, run the bundled checker:

```bash
python3 <skill-dir>/scripts/check_quartz_ready.py \
  /Users/lishaojie/Documents/blogs/content/courses/<course-slug>
```

Fix errors before pushing to GitHub. Warnings are review items.

For older generated lessons, use the conservative frontmatter fixer before checking:

```bash
python3 <skill-dir>/scripts/fix_frontmatter.py <course-workspace> \
  --add-description "Course lesson" --fix-mermaid
```

The fixer is dry-run by default. Add `--apply` only after reviewing the planned changes.

## Lessons

A lesson is the main thing you produce — the unit in which knowledge and skills reach the user. Each lesson is one self-contained Markdown file, saved to `./lessons/` and titled `0001-<dash-case-name>.md` where the four-digit number increments each time. **The YAML `title` and page H1 must always start with `第NN课：`** for standard lessons (e.g. `第01课：NLP到底是什么？`). Use `--number` with `scaffold_lesson.py` to auto-generate this prefix rather than writing it manually. Supplemental lessons must use `sNN-<dash-case-name>.md` and `补充课NN：...`.

A lesson should be **beautiful** — clean structure, well-paced sections, and thoughtful use of diagrams, callouts, and formatting — since the user will return to these later to review in Obsidian.

The lesson should be short, and completable very quickly. Learners' working memory is very small, and we need to stay within it. But each lesson should give the user a single tangible win that they can build on. It should be directly tied to the mission, and should be in the user's zone of proximal development.

If possible, open the lesson file for the user by running a CLI command.

Each lesson should link via `[[wikilinks]]` to other lessons and reference documents. This builds Obsidian's graph view.

Each lesson should recommend a primary source for the user to read or watch. This should be the most high-quality, high-trust resource you found on the topic.

All lessons are static publishable course pages. Do not end with chat-style prompts such as "想继续吗？", "有什么问题想先问吗？", "有什么问题想先问问的吗？", "告诉我你的体验", or "有什么不明白的地方吗？". End with a useful static close instead: next lesson link, review task, application assignment, self-test, or checklist.

Use the lesson skeleton in [references/obsidian-markdown.md](./references/obsidian-markdown.md) when drafting a new lesson.

### Public Example Selection

Choose examples that teach the concept without pulling the reader into unrelated identity, political, religious, gender, or national-position debates. Prefer neutral workplace, learning, product, family-routine, or everyday communication examples.

When the source course uses a sensitive example, do not reproduce it casually. Either:

- replace it with a neutral analogy that teaches the same mechanism, or
- explicitly attribute it as the instructor's quoted/transcribed example and keep the framing analytical.

For concepts such as "abstract words hide different meanings", use examples like "大家都说要高效", "客户说要专业", or "团队说要重视质量" instead of politically charged examples.

## Assets

Lessons are built from reusable **components**, stored in `./assets/`: Mermaid diagram templates, CSS snippets for Obsidian, shared LaTeX macro definitions, quiz templates, etc.

Reuse is the default, not the exception. Before authoring a lesson, read `./assets/` and build from the components already there. When a lesson needs something new and reusable, write it as a component in `./assets/` and link to it — never inline code a future lesson would duplicate.

A shared Obsidian CSS snippet is the first component every workspace earns. As the workspace grows, so should the component library.

## The Mission

Every lesson should be tied into the mission — the reason that the user is interested in learning about the topic.

If the user is unclear about the mission, or the `MISSION.md` is not populated, your first job should be to question the user on why they want to learn this.

Failing to understand the mission will mean knowledge acquisition is not grounded in real-world goals. Lessons will feel too abstract. You will have no way of judging what the user should do next.

Missions may change as the user develops more skills and knowledge. This is normal — make sure to update the `MISSION.md` and add a learning record to capture the change. Confirm with the user before changing the mission.

## Zone Of Proximal Development

Each lesson, the user should always feel as if they are being challenged 'just enough'.

The user may specify an exact thing they want to learn. If they don't, figure out their zone of proximal development by:

- Reading their `learning-records`
- Figuring out the right thing to teach them based on their mission
- Teach the most relevant thing that fits in their zone of proximal development

## Knowledge

Lessons should be designed around a skill the user is going to learn. The knowledge in the lesson should be only what's required to acquire that skill. You teach the knowledge first, then get the user to practice the skills via exercises and self-checks inside the Markdown.

Knowledge should first be gathered from trusted resources. Use `RESOURCES.md` to keep track of them. Lessons should be littered with citations — links to external resources to back up any claim made. This increases the trustworthiness of the lesson.

For acquiring knowledge, difficulty is the enemy. It eats working memory you need for understanding.

## Skills

If knowledge is all about acquisition, skills are about durability and flexibility. Make the knowledge stick.

For skill acquisition, difficulty is the tool. Effortful retrieval is what builds storage strength. Within Markdown lessons, use these tools:

- Self-check quizzes with answers hidden behind `<details>` blocks (the user reveals them after attempting)
- Step-by-step guided exercises
- Practice problems with worked solutions (also behind `<details>`)
- Reflection prompts using `> [!QUESTION]` callouts when they ask the learner to recall, apply, diagnose, or choose a next action

Each of these should give the user immediate feedback — the answer is right there in the document, but only after they attempt it.

For concrete practice block examples, use [references/obsidian-markdown.md](./references/obsidian-markdown.md). Avoid leaking answers through option length, formatting, or order.

## Acquiring Wisdom

Wisdom comes from true real-world interaction — testing your skills outside the learning environment.

When the user asks a question that appears to require wisdom, your default posture should be to attempt to answer — but to ultimately delegate to a **community**.

A community is a place (online or offline) where the user can test their skills in the real world. This might be a forum, a subreddit, a real-world class (budget permitting) or a local interest group.

You should attempt to find high-reputation communities the user can join. If the user expresses a preference that they don't want to join a community, respect it.

## Reference Documents

While creating lessons, you should also create reference documents in `./reference/*.md`. Lessons can reference these documents via `[[wikilinks]]` — they are useful for tracking raw units of knowledge useful across lessons.

Lessons will rarely be revisited later — reference documents will be. They should be the compressed essence of the lesson, in a format designed for quick reference in Obsidian.

Reference documents should make heavy use of:
- **Tables** for syntax, commands, and comparisons
- **Mermaid diagrams** for processes and relationships
- **LaTeX formulas** for mathematical concepts
- **Callout blocks** for warnings and important notes

Some learning topics lend themselves to reference:

- Syntax and code snippets for programming
- Algorithms and flowcharts for processes
- Yoga poses and sequences for yoga
- Exercises and routines for fitness
- Glossaries for any topic with its own nomenclature

Glossaries, in particular, are an essential reference. Once one is created, it should be adhered to in every lesson. Glossaries live at `GLOSSARY.md` in the workspace root. Use the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).

## `NOTES.md`

The user will sometimes express preferences of how they want to be taught, or things you should keep in mind. This is the place to record those preferences, so you can refer back to them when designing lessons or working with the user.
