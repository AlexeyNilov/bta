---
name: merge-chapters-into-md
description: Merge ordered chapter Markdown files back into one Markdown document for audiobook/TTS workflows. Use when Codex needs to combine files from a chapter-split output directory, preserve reading order, create a single input/*.md file, or verify chapter merge completeness before bta convert.
---

# Merge Chapters Into Markdown

## Goal

Combine chapter-sized Markdown files into one readable Markdown file while preserving order and prose. This is typically used after `split-ebook-into-chapters` and cleanup, before adding pause tags or running `bta convert`.

## Workflow

1. Inspect the source directory.
   - List `*.md` files sorted by filename.
   - Confirm the set matches the user's intent. Do not recreate or restore missing files unless explicitly asked.
   - Prefer zero-padded filenames such as `00_front_matter.md`, `01_introduction.md`, `02_chapter.md`.

2. Choose the target file.
   - Write to the user-requested path.
   - If no path is requested, use a clear new file under `input/`, such as `input/book_merged.md`.
   - Do not overwrite the original source export unless the user explicitly asks.

3. Run `scripts/merge_chapters.py`.
   - The script sorts files lexicographically by filename.
   - It strips outer whitespace from each file and joins chapters with blank lines.
   - It fails if the target path is inside the source directory, preventing accidental self-inclusion.

4. Validate the result.
   - Confirm source file count.
   - Check the first and last few lines of the merged file.
   - Confirm line/byte count if useful.

## Script

Use the bundled helper:

```bash
python skill/merge-chapters-into-md/scripts/merge_chapters.py \
  output/book_chapters \
  input/book_merged.md
```

Useful options:

- `--glob "*.md"` to change the source pattern.
- `--separator "\n\n---\n\n"` to add an explicit divider between chapters.
- `--allow-empty` to allow an empty source directory, generally only for tests.

## Judgment Rules

- Treat the current files in the source directory as authoritative unless the user asks to regenerate missing sections.
- Keep merge behavior mechanical; do not clean, rewrite, summarize, or add pause tags in this skill.
- If the source directory contains non-chapter Markdown files, stop and ask or use a narrower `--glob`.
