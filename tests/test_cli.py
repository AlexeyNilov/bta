from pathlib import Path

from bta.cli import main


def test_help_shows_convert_usage(capsys):
    exit_code = main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Usage:" in captured.out
    assert "bta convert <input.md>" in captured.out
    assert "MCP" not in captured.out


def test_version_shows_package_name(capsys):
    exit_code = main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("bta ")


def test_unknown_command_exits_with_usage(capsys):
    exit_code = main(["unknown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unknown command: unknown" in captured.err
    assert "bta convert <input.md>" in captured.err


def test_convert_requires_input_path(capsys):
    exit_code = main(["convert"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Missing input path" in captured.err


def test_convert_rejects_stdin(capsys):
    exit_code = main(["convert", "-"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "stdin is not supported" in captured.err


def test_convert_rejects_missing_local_file(capsys, tmp_path):
    missing_file = tmp_path / "missing.md"

    exit_code = main(["convert", str(missing_file)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert f"Input file does not exist: {missing_file}" in captured.err


def test_convert_rejects_non_markdown_file(capsys, tmp_path):
    text_file = tmp_path / "book.txt"
    text_file.write_text("text", encoding="utf-8")

    exit_code = main(["convert", str(text_file)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Input file must be a Markdown .md file" in captured.err


def test_convert_accepts_local_markdown_file(capsys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    input_file = Path("book.md")
    input_file.write_text("# Book\n", encoding="utf-8")

    exit_code = main(["convert", str(input_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
