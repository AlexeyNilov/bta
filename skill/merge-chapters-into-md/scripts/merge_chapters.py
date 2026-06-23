#!/usr/bin/env python3
"""Merge ordered chapter Markdown files into one Markdown file."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--glob", default="*.md", help="Source file glob. Default: *.md")
    parser.add_argument(
        "--separator",
        default="\n\n",
        help="Text inserted between chapter files. Default: a blank line.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow an empty source directory and write an empty output file.",
    )
    return parser.parse_args()


def sorted_source_files(source_dir: Path, pattern: str) -> list[Path]:
    return sorted(path for path in source_dir.glob(pattern) if path.is_file())


def ensure_output_is_not_inside_source(source_dir: Path, output_file: Path) -> None:
    resolved_source = source_dir.resolve()
    resolved_output = output_file.resolve()
    if resolved_output == resolved_source or resolved_source in resolved_output.parents:
        raise ValueError("output_file must not be inside source_dir")


def merge_files(source_files: list[Path], separator: str) -> str:
    chunks = [path.read_text(encoding="utf-8").strip() for path in source_files]
    return separator.join(chunk for chunk in chunks if chunk).strip() + "\n"


def main() -> int:
    args = parse_args()
    if not args.source_dir.is_dir():
        raise SystemExit(f"source_dir is not a directory: {args.source_dir}")

    ensure_output_is_not_inside_source(args.source_dir, args.output_file)
    source_files = sorted_source_files(args.source_dir, args.glob)
    if not source_files and not args.allow_empty:
        raise SystemExit(f"no files matched {args.glob!r} in {args.source_dir}")

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(merge_files(source_files, args.separator), encoding="utf-8")

    for path in source_files:
        print(path)
    print(f"merged_count={len(source_files)}")
    print(f"output_file={args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
