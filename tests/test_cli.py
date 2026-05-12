from mcp_stdio_python_template.cli import main


class FakeServer:
    def __init__(self) -> None:
        self.transports: list[str] = []

    def run(self, transport: str = "stdio") -> None:
        self.transports.append(transport)


def test_main_runs_mcp_server_over_stdio_without_stdout(capsys):
    server = FakeServer()

    exit_code = main([], server_factory=lambda: server)

    captured = capsys.readouterr()

    assert exit_code == 0
    assert server.transports == ["stdio"]
    assert captured.out == ""
    assert captured.err == ""


def test_main_prints_help_without_starting_server(capsys):
    server = FakeServer()

    exit_code = main(["--help"], server_factory=lambda: server)

    captured = capsys.readouterr()

    assert exit_code == 0
    assert server.transports == []
    assert "stdio MCP server" in captured.out


def test_main_version_option_prints_package_version_without_starting_server(monkeypatch, capsys):
    server = FakeServer()
    monkeypatch.setattr("mcp_stdio_python_template.cli.package_version", lambda: "9.8.7")

    exit_code = main(["--version"], server_factory=lambda: server)

    captured = capsys.readouterr()

    assert exit_code == 0
    assert server.transports == []
    assert captured.out == "mcp-stdio-python-template 9.8.7\n"
    assert captured.err == ""


def test_main_rejects_version_command(capsys):
    exit_code = main(["version"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Unknown command: version" in captured.err


def test_main_reports_unknown_command(capsys):
    exit_code = main(["wat"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Unknown command" in captured.err
