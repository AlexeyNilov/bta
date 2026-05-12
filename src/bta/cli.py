from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version

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
    if args:
        sys.stderr.write(f"Unknown command: {args[0]}\n\n{help_text()}")
        return 2

    try:
        config = load_config()
        logging.basicConfig(level=config.log_level)
    except Exception as error:
        sys.stderr.write(f"bta failed to start: {error}\n")
        return 1
    return 0


def wants_help(args: Sequence[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in args)


def package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.0.0"


def help_text() -> str:
    return f"{PACKAGE_NAME}\n\nRuns a minimal stdio MCP server.\n\nUsage:\n  bta\n  bta --version\n"


if __name__ == "__main__":
    raise SystemExit(main())
