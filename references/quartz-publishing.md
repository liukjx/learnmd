# Quartz Publishing Guide

Use this reference when a learnmd workspace should become a public Quartz course.

## Source And Public Directories

Keep the learning workspace separate from the Quartz public content directory.

Source workspace:

```text
course-workspace/
  MISSION.md              # private
  NOTES.md                # private
  RESOURCES.md            # private by default
  learning-records/       # private
  lessons/                # public
  reference/              # selected public references
  assets/                 # public assets only
```

Quartz public output:

```text
/Users/lishaojie/Documents/blogs/content/courses/course-slug/
  index.md                # recommended course landing page
  00-course-map.md        # recommended course map
  lessons/
  reference/              # optional, only useful public references
  assets/
```

Do not publish private learning state. `MISSION.md`, `NOTES.md`, `learning-records/`, raw subtitles, local-only source files, and private links should stay in the source workspace.

## Index Pages

`content/index.md` is the site home page. Do not create or overwrite it for each course.

Each course should usually have its own `index.md`:

```text
content/courses/course-slug/index.md
```

This is recommended, not mandatory. It gives the course a clean landing URL and a place for the course summary, audience, prerequisites, and chapter links.

Do not add `index.md` to every child directory by default. Add `lessons/index.md` or `reference/index.md` only when the subdirectory needs a custom landing page.

## Public Content Policy

Publish by default:

- `index.md`
- `00-course-map.md`
- `lessons/**/*.md`
- selected `reference/**/*.md`
- assets referenced by public Markdown

Do not publish by default:

- `MISSION.md`
- `NOTES.md`
- `RESOURCES.md`
- `learning-records/`
- raw SRT files
- private PDFs, paid course materials, local screenshots, and temporary drafts

`RESOURCES.md` may be published only when it is intentionally written as a public reading list with no private paths, tokens, paid-course links, or local-only notes.

## Quartz Frontmatter

Use Quartz-friendly frontmatter for public pages:

```yaml
---
title: "Lesson Title"
description: "One sentence summary for search, previews, and navigation."
date: YYYY-MM-DD
tags:
  - course
  - topic-name
aliases:
  - Alternative Title
draft: false
---
```

Fields to prefer:

- `title`: page title. Quartz can infer it, but explicit titles are better for courses.
- `description`: used for previews and search context.
- `date`: publication date in `YYYY-MM-DD`.
- `tags`: use lowercase dash-case tags.
- `aliases`: optional alternate names.
- `draft`: set `true` only for pages that must not publish.
- `permalink`: optional stable URL when file paths may change.

Avoid Obsidian-only or local-only metadata in public pages unless the Quartz config intentionally uses it.

## Links And Assets

Use Obsidian wikilinks for internal links:

```markdown
See [[01-introduction]] and [[../reference/glossary|Glossary]].
```

Use relative links for assets:

```markdown
![[../assets/diagram.png]]
![Diagram](../assets/diagram.png)
```

Never use absolute local paths such as `/Users/...` or `file://...` in public Markdown.

## Export Workflow

Run a dry-run export first:

```bash
python3 <skill-dir>/scripts/export_to_quartz.py . \
  --target /Users/lishaojie/Documents/blogs/content/courses/course-slug
```

Apply the export only after reviewing the planned actions:

```bash
python3 <skill-dir>/scripts/export_to_quartz.py . \
  --target /Users/lishaojie/Documents/blogs/content/courses/course-slug \
  --apply
```

Optionally remove files from the target that no longer exist in the public source set:

```bash
python3 <skill-dir>/scripts/export_to_quartz.py . \
  --target /Users/lishaojie/Documents/blogs/content/courses/course-slug \
  --apply --delete
```

## Prepublish Check

After export, check the public directory:

```bash
python3 <skill-dir>/scripts/check_quartz_ready.py \
  /Users/lishaojie/Documents/blogs/content/courses/course-slug
```

Fix all errors before pushing to GitHub. Warnings are review items; they may be acceptable when intentional.

The checker should catch:

- private files leaked into public content
- missing or weak Quartz frontmatter
- `draft: true` pages
- unresolved wikilinks
- missing Markdown image/embed assets
- local absolute paths
- residual SRT timestamps

## Local Preview

From the Quartz project root:

```bash
npx quartz build --serve
```

Then review the course landing page, graph links, explorer navigation, callouts, diagrams, equations, and images before syncing or pushing.
