#!/usr/bin/env python3
"""Clean ebook export text for text-to-speech."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


TOC_LINE = re.compile(
    r"^(?:\d+\.\s+)?(?:Identify the Mess|State Your Intent|State your Intent|Face Reality|"
    r"Choose a Direction|Measure the Distance|Play with Structure|Prepare to Adjust|"
    r"Resources\.?|Indexed Lexicon|Lexicon|Thank You|Thanks)$",
    re.IGNORECASE,
)


def normalize_common_tts_tokens(text: str) -> str:
    replacements = {
        "\u00a0": " ",
        " & ": " and ",
        "eBook": "ebook",
        "ISBN-13": "ISBN 13",
        "Doing/Do": "Doing or Do",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\be\.g\.,?", "for example", text)
    text = re.sub(r"\(n\.\)", "(noun)", text)
    text = re.sub(r"\(v\.\)", "(verb)", text)
    text = re.sub(r"\(adj\.\)", "(adjective)", text)
    text = re.sub(r"\(adv\.\)", "(adverb)", text)
    text = re.sub(r"\b(\d+)\.([A-Za-z])", r"\1. \2", text)
    text = text.replace(" - ", "\n\n")
    text = text.replace(" -- ", ", ")
    text = text.replace(" --- ", ", ")
    text = text.replace("\u2014", ", ")
    text = text.replace("\u2013", ", ")
    return text


def strip_markup(text: str) -> str:
    text = re.sub(r"(?is)^!\[[^\r\n]*\]\([^\r\n]*\)\s*", "", text)
    text = re.sub(r"(?is)<svg\b.*?</svg>", "", text)
    text = re.sub(r"(?is)<img\b[^>]*>", "", text)
    text = re.sub(r"(?is)<span\s+id=\"[^\"]+\"\s*>\s*</span>", "", text)
    text = re.sub(r"(?is)<s>.*?</s>", "", text)
    text = re.sub(r"(?is)</?(span|div|p|br|li)[^>]*>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = html.unescape(text)
    return text


def strip_links(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\bfilepos\d+\b", "", text)
    return text


def is_visual_or_navigation(paragraph: str) -> bool:
    if not paragraph:
        return True
    if re.fullmatch(r"[-,\s]+", paragraph):
        return True
    if re.search(r"(?:\\?_){5,}", paragraph):
        return True
    if re.search(r"https?://|www\.|(?:^|\s)[A-Za-z0-9.-]+\.(?:com|org|net|pdf)(?:\b|/)", paragraph):
        return True
    if re.search(r"\b(index_split|filepos|calibre|xhtml|svg)\b", paragraph, re.IGNORECASE):
        return True
    if re.fullmatch(r"Download a printable worksheet\.?", paragraph, re.IGNORECASE):
        return True
    if re.fullmatch(r"Table of Contents", paragraph, re.IGNORECASE):
        return True
    if TOC_LINE.fullmatch(paragraph):
        return True
    return False


def clean_paragraphs(text: str) -> str:
    paragraphs = re.split(r"(?:\r?\n\s*){2,}", text.strip())
    out: list[str] = []

    for paragraph in paragraphs:
        paragraph = re.sub(r"\r?\n\s*", " ", paragraph)
        paragraph = re.sub(r"^\s*[-*]\s+", "", paragraph)
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        paragraph = re.sub(r"\s+([,.?!:;])", r"\1", paragraph)
        paragraph = re.sub(r":{2,}", ":", paragraph)

        if is_visual_or_navigation(paragraph):
            continue
        out.append(paragraph)

    text = "\n\n".join(out)

    # Split flattened numbered lists into separate speakable paragraphs.
    text = re.sub(r"(?<!^)\s+(?=\d+\.\s)", "\n\n", text)

    # Rejoin fragments created by inline emphasis tags.
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"([^\.\?!:;\"\u201d\)\]])\n\n([a-z])", r"\1 \2", text)

    text = re.sub(r"\s+([,.?!:;])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    return text.strip() + "\n"


def clean_text(text: str) -> str:
    text = strip_markup(text)
    text = strip_links(text)
    text = normalize_common_tts_tokens(text)
    return clean_paragraphs(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    if args.in_place and args.output:
        parser.error("Use either --in-place or --output, not both.")
    if not args.in_place and not args.output:
        parser.error("Specify --in-place or --output.")

    source = args.input.read_text(encoding="utf-8")
    cleaned = clean_text(source)

    target = args.input if args.in_place else args.output
    assert target is not None
    target.write_text(cleaned, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
