from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from bta.config import load_config

PACKAGE_NAME = "bta"


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if wants_help(args):
        sys.stdout.write(help_text())
        return 0
    if args == ["--version"]:
        sys.stdout.write(f"{PACKAGE_NAME} {package_version()}\n")
        return 0
    if args[:1] == ["convert"]:
        return convert(args[1:])
    if args:
        sys.stderr.write(f"Unknown command: {args[0]}\n\n{help_text()}")
        return 2

    sys.stderr.write(f"Missing command\n\n{help_text()}")
    return 2


def convert(args: Sequence[str]) -> int:
    try:
        input_path = parse_input_path(args)
        config = load_config()
        logging.basicConfig(level=config.log_level)
    except CliUsageError as error:
        sys.stderr.write(f"{error}\n\n{help_text()}")
        return 2
    except Exception as error:
        sys.stderr.write(f"bta failed to start: {error}\n")
        return 1

    logging.info(
        "Accepted conversion request for %s with target chunk size %s and voice %s",
        input_path,
        config.chunk_target_chars,
        config.voice,
    )
    return 0


def parse_input_path(args: Sequence[str]) -> Path:
    if not args:
        raise CliUsageError("Missing input path")
    if len(args) > 1:
        unexpected = " ".join(args[1:])
        raise CliUsageError(f"Unexpected argument(s): {unexpected}")

    raw_path = args[0]
    if raw_path == "-":
        raise CliUsageError("stdin is not supported; provide a local Markdown file path")

    input_path = Path(raw_path).expanduser()
    if input_path.suffix.lower() != ".md":
        raise CliUsageError("Input file must be a Markdown .md file")
    if not input_path.exists():
        raise CliUsageError(f"Input file does not exist: {input_path}")
    if not input_path.is_file():
        raise CliUsageError(f"Input path is not a file: {input_path}")

    return input_path


class CliUsageError(ValueError):
    pass


def wants_help(args: Sequence[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in args)


def package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.0.0"


def help_text() -> str:
    return (
        f"{PACKAGE_NAME}\n\n"
        "Convert Markdown documents into audiobook WAV chunks.\n\n"
        "Usage:\n"
        "  bta convert <input.md>\n"
        "  bta --version\n"
        "  bta --help\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
