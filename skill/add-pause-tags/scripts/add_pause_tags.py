#!/usr/bin/env python3
"""Add BTA-compatible pause tags to prepared Markdown."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PAUSE_TAG_RE = re.compile(r"\s*\[(\d+(?:\.\d+)?)s\]\s*$")
SENTENCE_END_RE = re.compile(r"[.!?…][\"')\]]?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--chapter-pause", type=float, default=4.0)
    parser.add_argument("--section-pause", type=float, default=2.0)
    parser.add_argument("--paragraph-pause", type=float, default=1.0)
    parser.add_argument("--chapter-heading", action="append", default=[])
    parser.add_argument("--section-heading", action="append", default=[])
    parser.add_argument(
        "--use-heading-heuristics",
        action="store_true",
        help="Infer short title-like and all-caps single-line blocks as headings.",
    )
    return parser.parse_args()


def format_pause(seconds: float) -> str:
    if seconds.is_integer():
        return f"[{int(seconds)}s]"
    return f"[{seconds:g}s]"


def strip_trailing_pause(text: str) -> str:
    return PAUSE_TAG_RE.sub("", text).rstrip()


def split_blocks(text: str) -> list[str]:
    return re.split(r"(\n\s*\n)", text)


def is_separator(block: str) -> bool:
    return not block.strip()


def is_single_line(block: str) -> bool:
    return "\n" not in block.strip()


def looks_like_section_heading(text: str) -> bool:
    if len(text) > 90 or SENTENCE_END_RE.search(text):
        return False
    if text.isupper() and any(char.isalpha() for char in text):
        return True
    return bool(re.fullmatch(r"\d+\.\s+[A-Z][A-Za-z0-9'’:\- ]{2,60}", text))


def looks_like_chapter_heading(text: str) -> bool:
    if len(text) > 70 or SENTENCE_END_RE.search(text):
        return False
    return bool(
        re.fullmatch(r"(?:Dedication|Introduction|Afterword|Acknowledgments)", text)
        or re.fullmatch(r"\d+\.\s+[A-Z][A-Za-z0-9'’:\- ]{2,50}", text)
    )


def pause_for_block(
    block: str,
    chapter_headings: set[str],
    section_headings: set[str],
    use_heading_heuristics: bool,
    chapter_pause: float,
    section_pause: float,
    paragraph_pause: float,
) -> float:
    candidate = strip_trailing_pause(block.strip())

    if is_single_line(block):
        if candidate in chapter_headings:
            return chapter_pause
        if candidate in section_headings:
            return section_pause
        if use_heading_heuristics and looks_like_chapter_heading(candidate):
            return chapter_pause
        if use_heading_heuristics and looks_like_section_heading(candidate):
            return section_pause

    return paragraph_pause


def add_pause_tags(
    text: str,
    chapter_headings: set[str],
    section_headings: set[str],
    use_heading_heuristics: bool,
    chapter_pause: float,
    section_pause: float,
    paragraph_pause: float,
) -> str:
    output: list[str] = []

    for block in split_blocks(text):
        if is_separator(block):
            output.append(block)
            continue

        stripped = block.rstrip()
        trailing = block[len(stripped) :]
        base = strip_trailing_pause(stripped)
        seconds = pause_for_block(
            block,
            chapter_headings,
            section_headings,
            use_heading_heuristics,
            chapter_pause,
            section_pause,
            paragraph_pause,
        )
        output.append(f"{base} {format_pause(seconds)}{trailing}")

    return "".join(output).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    if args.in_place and args.output:
        raise SystemExit("Use either --in-place or --output, not both.")
    if not args.in_place and args.output is None:
        raise SystemExit("Specify --in-place or --output.")

    text = args.input.read_text(encoding="utf-8")
    paused = add_pause_tags(
        text,
        set(args.chapter_heading),
        set(args.section_heading),
        args.use_heading_heuristics,
        args.chapter_pause,
        args.section_pause,
        args.paragraph_pause,
    )

    target = args.input if args.in_place else args.output
    assert target is not None
    target.write_text(paused, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
