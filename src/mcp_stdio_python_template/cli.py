from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Sequence
from importlib.metadata import PackageNotFoundError, version
from typing import Literal, Protocol

from mcp_stdio_python_template.config import load_config
from mcp_stdio_python_template.server import build_server

PACKAGE_NAME = "mcp-stdio-python-template"


class RunnableServer(Protocol):
    def run(
        self,
        transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
        mount_path: str | None = None,
    ) -> None:
        raise NotImplementedError


ServerFactory = Callable[[], RunnableServer]


def default_server_factory() -> RunnableServer:
    return build_server()


def main(
    argv: Sequence[str] | None = None,
    server_factory: ServerFactory = default_server_factory,
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
        server_factory().run("stdio")
    except Exception as error:
        sys.stderr.write(f"mcp-stdio-python-template failed to start: {error}\n")
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
    return (
        f"{PACKAGE_NAME}\n\n"
        "Runs a minimal stdio MCP server.\n\n"
        "Usage:\n"
        "  mcp-stdio-python-template\n"
        "  mcp-stdio-python-template --version\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
