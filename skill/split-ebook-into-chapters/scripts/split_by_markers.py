#!/usr/bin/env python3
"""Split an ebook text file into ordered files using semantic boundary markers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a text/Markdown ebook into files from marker lines."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--markers-json",
        required=True,
        type=Path,
        help="JSON array of objects with file and marker fields.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Input/output encoding. Default: utf-8.",
    )
    parser.add_argument(
        "--clean-page-markers",
        action="store_true",
        help="Remove standalone page/navigation marker lines such as 'v'.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(path: Path, encoding: str) -> str:
    read_encoding = "utf-8-sig" if encoding.lower().replace("_", "-") == "utf-8" else encoding
    return path.read_text(encoding=read_encoding)


def find_marker(text: str, marker: str) -> int:
    pattern = r"(?m)^" + re.escape(marker.strip()) + r"\s*$"
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"Could not find marker as standalone line: {marker!r}")
    return match.start()


def clean_chunk(chunk: str, clean_page_markers: bool) -> str:
    if clean_page_markers:
        chunk = re.sub(r"\n\s*v\s*(\n|$)", "\n", chunk)
    chunk = re.sub(r"[ \t]+\n", "\n", chunk)
    chunk = re.sub(r"\n{3,}", "\n\n", chunk)
    return chunk.strip() + "\n"


def main() -> None:
    args = parse_args()
    text = normalize_text(read_text(args.input_file, args.encoding))
    markers = json.loads(read_text(args.markers_json, args.encoding))

    if not isinstance(markers, list) or not markers:
        raise ValueError("markers-json must contain a non-empty JSON array")

    positions = []
    for item in markers:
        if not isinstance(item, dict) or "file" not in item or "marker" not in item:
            raise ValueError("Each marker entry must have file and marker fields")
        positions.append(
            {
                "file": item["file"],
                "marker": item["marker"],
                "index": find_marker(text, item["marker"]),
            }
        )

    positions.sort(key=lambda item: item["index"])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for index, item in enumerate(positions):
        start = item["index"]
        end = positions[index + 1]["index"] if index + 1 < len(positions) else len(text)
        chunk = clean_chunk(text[start:end], args.clean_page_markers)
        output_path = args.output_dir / item["file"]
        output_path.write_text(chunk, encoding=args.encoding)

    for item in positions:
        print(item["file"])


if __name__ == "__main__":
    main()
