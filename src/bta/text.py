from __future__ import annotations

import re

HTML_TAG_PATTERN = re.compile(r"<[^<>]*>", re.DOTALL)
SENTENCE_PATTERN = re.compile(r".+?(?:[.!?]+[\"')\]]?(?=\s+|$)|$)", re.DOTALL)
WHITESPACE_PATTERN = re.compile(r"[ \t\f\v]+")


def clean_markdown_text(text: str) -> str:
    if not HTML_TAG_PATTERN.search(text):
        return text

    without_html = HTML_TAG_PATTERN.sub(" ", text)
    normalized_lines = [
        WHITESPACE_PATTERN.sub(" ", line).strip() for line in without_html.splitlines()
    ]
    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r" +([.,;:!?])", r"\1", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def chunk_text(text: str, target_chars: int) -> list[str]:
    if target_chars < 1:
        raise ValueError("target_chars must be a positive integer")

    chunks: list[str] = []
    current = ""
    for paragraph in split_paragraphs(text):
        units = paragraph_units(paragraph, target_chars)
        for index, unit in enumerate(units):
            separator = "\n\n" if index == 0 else " "
            current = append_unit(chunks, current, unit, separator, target_chars)

    if current:
        chunks.append(current)
    return chunks


def split_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", text) if paragraph.strip()]


def paragraph_units(paragraph: str, target_chars: int) -> list[str]:
    if len(paragraph) <= target_chars:
        return [paragraph]
    return split_sentences(paragraph)


def split_sentences(text: str) -> list[str]:
    return [match.group(0).strip() for match in SENTENCE_PATTERN.finditer(text) if match.group(0).strip()]


def append_unit(
    chunks: list[str],
    current: str,
    unit: str,
    separator: str,
    target_chars: int,
) -> str:
    if not current:
        return unit

    candidate = f"{current}{separator}{unit}"
    if len(candidate) <= target_chars:
        return candidate

    chunks.append(current)
    return unit
