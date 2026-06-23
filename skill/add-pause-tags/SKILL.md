---
name: add-pause-tags
description: Add or update inline BTA pause tags in prepared Markdown for audiobook/TTS narration. Use when Codex needs to insert silence markers such as [1s], [2s], or [4s] after paragraphs, chapter headings, section headings, or other narration boundaries before running bta convert.
---

# Add Pause Tags

## Goal

Shape prepared Markdown for narration by adding BTA-compatible inline pause tags. Preserve prose exactly except for trailing pause tags.

Supported BTA syntax is `[1s]`, `[1.5s]`, or `[0.25s]`. Unsupported pause text will be spoken, so validate tags after editing.

## Default Timing

- Chapter-level headings: `[4s]`
- Section-level headings: `[2.5s]`
- Ordinary paragraphs: `[1.5s]`

Use different timings if the user asks. Avoid adding pauses inside ordinary sentences unless the user explicitly wants line-level dramatic pacing.

## Workflow

1. Inspect the target Markdown.
   - Confirm it is already cleaned for TTS.
   - Identify chapter-level headings and section-level headings.
   - Check whether pause tags already exist.

2. Choose exact heading sets when possible.
   - Chapter headings are major audiobook breaks: dedication, introduction, chapter titles, afterword, acknowledgments.
   - Section headings are internal breaks: all-caps subheads, short numbered concept headings, scene labels.
   - Do not classify numbered list content as a heading just because it starts with `1.`.

3. Run `scripts/add_pause_tags.py`.
   - Prefer exact heading arguments for books with numbered lists or short transcript lines.
   - The script is idempotent for trailing pause tags: rerunning replaces the trailing pause for matched blocks rather than stacking another tag.

4. Validate with the project parser or a regex.
   - Count total pause tags.
   - Confirm only supported tag syntax appears.
   - Spot-check the start, a middle chapter transition, and the end.

## Script

Use the bundled script from the skill directory:

```bash
python skill/add-pause-tags/scripts/add_pause_tags.py input/book.md --in-place \
  --chapter-heading "Introduction" \
  --chapter-heading "1. Assess" \
  --section-heading "AVIATION"
```

Or write to a separate file:

```bash
python skill/add-pause-tags/scripts/add_pause_tags.py input/book.md --output input/book_paused.md
```

Useful options:

- `--chapter-pause 4`
- `--section-pause 2`
- `--paragraph-pause 1`
- `--chapter-heading "Exact heading text"`
- `--section-heading "Exact heading text"`
- `--use-heading-heuristics`

Only use `--use-heading-heuristics` when exact heading lists are unnecessary. Heuristics treat short title-like lines and all-caps lines as headings, which can be wrong for transcripts or broken OCR.

## Validation

For BTA projects, validate through the parser when available:

```bash
python -c "from pathlib import Path; from bta.pause_tags import PauseEvent, parse_pause_tags; text=Path('input/book.md').read_text(); pauses=[e.seconds for e in parse_pause_tags(text) if isinstance(e, PauseEvent)]; print(len(pauses), sum(pauses), sorted(set(pauses)))"
```

Also search for bracketed text that is not a pause tag:

```bash
rg -n '\[[^]]*\]' input/book.md
```
