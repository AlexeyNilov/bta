---
name: ebook-export-cleanup
description: Clean ebook export files for text-to-speech. Use when Codex is asked to prepare Markdown, HTML-ish Markdown, EPUB/Calibre exports, copied ebook text, or converted book notes for TTS/audio by removing markup, image references, internal anchors, table-of-contents links, worksheet blanks, bare URLs, and other visual-only structure. Also use when the user mentions ebook_export_cleanup.
---

# Ebook Export Cleanup

## Goal

Prepare ebook-export text so a TTS engine can read it clearly. Preserve the author's prose and useful reading order; remove or rewrite anything that only makes sense visually.

## Workflow

1. Inspect the file before editing. Identify the source pattern: Calibre export, HTML pasted into Markdown, EPUB split anchors, OCR text, or normal Markdown with a few artifacts.
2. Run `scripts/clean_ebook_export.py` on a copy or with `--in-place` when the user asked to modify the file directly.
3. Review the diff or sample output. Fix any content-specific problems the script cannot know, especially:
   - split emphasis fragments, such as `Every / thing / is complex`
   - visual diagrams whose text needs summary or removal
   - bare resource lists, website lists, or page-navigation blocks
   - worksheet prompts with blanks or download-only instructions
   - abbreviations a TTS voice may spell awkwardly
4. Validate with searches for residual non-speech artifacts.

## What to Remove

Remove export-only or visual-only material:

- HTML tags, SVG blocks, image tags, cover images, and Calibre classes.
- Internal anchors such as `index_split`, `filepos`, generated IDs, and table-of-contents links.
- Markdown image syntax and links where the URL is the only value. Keep visible link text only when it reads naturally.
- Fill-in-the-blank worksheet lines made from underscores.
- Bare URLs, raw domains, and download prompts unless the user explicitly wants references preserved.
- Repeated table-of-contents blocks, page-break notices, and navigation fragments.

## What to Preserve

Preserve content that still reads naturally aloud:

- Dedications, introductions, body prose, stories, questions, definitions, and acknowledgments.
- Useful lists, but convert them to paragraph-separated lines or simple numbered items.
- Book metadata only if it is meaningful to the user. ISBN lines and copyright pages can usually remain, but remove them if the target is a clean listening script.

## Script Usage

Use the bundled cleaner:

```powershell
& <python> <skill-dir>\scripts\clean_ebook_export.py <input-file> --in-place
```

Or write to a separate file:

```powershell
& <python> <skill-dir>\scripts\clean_ebook_export.py <input-file> --output <clean-file>
```

On Windows in Codex, use the bundled Python path when global `python` is unavailable.

## Validation Searches

After cleanup, search for likely leftovers:

```powershell
rg -n '(<|>|\[|\]|http|_{3,}|\\_|#|`|\|)| - |Table of Contents|Download|filepos|index_split|calibre|svg|\.com|\.org|\.net|\.pdf' <file>
```

Treat matches as review prompts, not automatic failures. Words like "online", "image", or "worksheet" may be legitimate prose.

## Judgment Rules

Do not summarize or rewrite the book unless the user asks. This skill is for making existing text speakable, not for abridging it.

When unsure whether a section is content or navigation, prefer preserving it in readable prose, then mention the uncertainty. When a line cannot be clearly translated into speech and adds no content, remove it.
