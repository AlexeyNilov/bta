---
name: split-ebook-into-chapters
description: Split ebook exports, copied book text, Markdown, or HTML-ish Markdown into separate logical chapter/section files for text-to-speech. Use when Codex needs to prepare long-form book text for TTS pauses, audiobook-style processing, semantic chapter boundaries, or ordered output files in a target folder. Also use when the user mentions split_ebook_into_chapters.
---

# Split Ebook Into Chapters

## Goal

Create ordered, TTS-ready text files from one long ebook source. Preserve the author's prose and reading order. Split by meaning, argument, or chapter-like movement, not by equal file size.

## Workflow

1. Inspect the source before writing files.
   - Check length, first and last sections, heading patterns, repeated story/exercise patterns, and obvious export artifacts.
   - Use fast searches for standalone title-like lines and recurring markers such as `Introduction`, `Chapter`, `Part`, or repeated numbered sections.

2. Identify logical boundaries.
   - Prefer explicit book headings when present.
   - If headings are missing, infer boundaries from conceptual turns: a new central claim, a new named step, a repeated chapter pattern, a new case study, or a transition from body matter to back matter.
   - Keep front matter, introduction, body chapters, appendices, lexicon/glossary, references, acknowledgments, and thanks as separate files when they are substantial enough to read independently.
   - Do not split inside a tightly coupled explanation just to reduce size.

3. Choose stable output names.
   - Prefix files with zero-padded order numbers: `00_front_matter.md`, `01_introduction.md`, `02_<chapter-title>.md`.
   - Use lowercase ASCII slugs for file names. Preserve the original title text inside the file.

4. Write files to the requested output directory.
   - Preserve paragraph spacing.
   - Remove only speech-hostile export artifacts: stray page markers, empty navigation fragments, image-only references, internal anchors, bare URLs, or worksheet blanks.
   - Do not summarize, abridge, modernize, or rewrite prose unless the user explicitly asks.

5. Validate the split.
   - Confirm every output file starts at the intended boundary.
   - Confirm chapter order is correct.
   - Search output for residual artifacts:

```powershell
rg -n '(<|>|\[|\]|http|_{3,}|\\_|#|`|\|)|Table of Contents|Download|filepos|index_split|calibre|svg|^\\s*v\\s*$' <output-dir>
```

Treat matches as prompts for review, not automatic failures.

## Script

Use `scripts/split_by_markers.py` after selecting the boundary markers. The script is intentionally small: it handles deterministic file writing once Codex has made the semantic boundary decisions.

Example:

```powershell
& <python> <skill-dir>\scripts\split_by_markers.py <input-file> <output-dir> --markers-json <markers.json>
```

Marker JSON format:

```json
[
  {"file": "00_front_matter.md", "marker": "To Joe, my father..."},
  {"file": "01_introduction.md", "marker": "Introduction"},
  {"file": "02_first_body_chapter.md", "marker": "First body chapter title"}
]
```

Each marker must appear as its own non-empty line, except the first marker may be the first line of the source. The script writes from each marker up to the next marker.

## Judgment Rules

- A "logical chapter" is a coherent idea block, not necessarily an official published chapter.
- If a book uses repeated micro-headings under a larger argument, keep the micro-headings together unless they can stand alone for TTS.
- If a source has broken encoding, duplicated tables of contents, or heavy markup, clean or repair those issues before splitting.
- When uncertain, prefer fewer, larger coherent files over many tiny fragments. TTS pauses are helped by meaningful boundaries; excessive fragmentation can hurt listening flow.
