from pathlib import Path

import bta.cli
from bta.cli import StderrProgressReporter, main
from bta.conversion import ConversionRequest, ConversionResult


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
    monkeypatch.setattr(bta.cli, "PocketTtsSynthesizer", FakePocketTtsSynthesizer)
    monkeypatch.setattr(bta.cli, "ScipyWavWriter", FakeScipyWavWriter)
    monkeypatch.setattr(bta.cli, "convert_markdown", fake_convert_markdown)

    exit_code = main(["convert", str(input_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""


def test_convert_wires_configured_conversion_dependencies(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    input_file = tmp_path / "book.md"
    input_file.write_text("# Book\n", encoding="utf-8")
    monkeypatch.setenv("BTA_CHUNK_TARGET_CHARS", "1200")
    monkeypatch.setenv("BTA_VOICE", "bruce")
    calls: dict[str, object] = {}

    class TrackingPocketTtsSynthesizer:
        sample_rate = 24_000

    class TrackingScipyWavWriter:
        def __init__(self, sample_rate: int) -> None:
            calls["sample_rate"] = sample_rate

    def tracking_convert_markdown(
        request: ConversionRequest,
        synthesizer: object,
        writer: object,
        progress_reporter: object | None = None,
    ) -> ConversionResult:
        calls["request"] = request
        calls["synthesizer"] = synthesizer
        calls["writer"] = writer
        calls["progress_reporter"] = progress_reporter
        return ConversionResult(
            total_chunks=1,
            written_chunks=1,
            skipped_chunks=0,
            resumed=False,
            completed=True,
        )

    monkeypatch.setattr(bta.cli, "PocketTtsSynthesizer", TrackingPocketTtsSynthesizer)
    monkeypatch.setattr(bta.cli, "ScipyWavWriter", TrackingScipyWavWriter)
    monkeypatch.setattr(bta.cli, "convert_markdown", tracking_convert_markdown)

    exit_code = main(["convert", str(input_file)])

    assert exit_code == 0
    assert calls["request"] == ConversionRequest(
        input_path=input_file,
        chunk_target_chars=1200,
        voice="bruce",
    )
    assert isinstance(calls["synthesizer"], TrackingPocketTtsSynthesizer)
    assert isinstance(calls["writer"], TrackingScipyWavWriter)
    assert calls["sample_rate"] == 24_000
    assert isinstance(calls["progress_reporter"], StderrProgressReporter)


def test_convert_wires_parallel_conversion_without_parent_tts_model(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    input_file = tmp_path / "book.md"
    input_file.write_text("# Book\n", encoding="utf-8")
    monkeypatch.setenv("BTA_TTS_WORKERS", "3")
    calls: dict[str, object] = {}

    class FailingPocketTtsSynthesizer:
        def __init__(self) -> None:
            raise AssertionError("parent process should not load a TTS model")

    def tracking_convert_markdown(
        request: ConversionRequest,
        synthesizer: object | None = None,
        writer: object | None = None,
        progress_reporter: object | None = None,
    ) -> ConversionResult:
        calls["request"] = request
        calls["synthesizer"] = synthesizer
        calls["writer"] = writer
        calls["progress_reporter"] = progress_reporter
        return ConversionResult(
            total_chunks=1,
            written_chunks=1,
            skipped_chunks=0,
            resumed=False,
            completed=True,
        )

    monkeypatch.setattr(bta.cli, "PocketTtsSynthesizer", FailingPocketTtsSynthesizer)
    monkeypatch.setattr(bta.cli, "convert_markdown", tracking_convert_markdown)

    exit_code = main(["convert", str(input_file)])

    assert exit_code == 0
    assert calls["request"] == ConversionRequest(
        input_path=input_file,
        chunk_target_chars=2000,
        voice="alba",
        tts_workers=3,
    )
    assert calls["synthesizer"] is None
    assert calls["writer"] is None
    assert isinstance(calls["progress_reporter"], StderrProgressReporter)


def test_stderr_progress_reporter_prints_current_chunk_of_total(capsys):
    reporter = StderrProgressReporter()

    reporter.report(current_chunk=2, total_chunks=5)

    captured = capsys.readouterr()
    assert captured.err == "Completed chunk 2 of 5\n"


class FakePocketTtsSynthesizer:
    sample_rate = 24_000


class FakeScipyWavWriter:
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate


def fake_convert_markdown(
    request: ConversionRequest,
    synthesizer: object,
    writer: object,
    progress_reporter: object | None = None,
) -> ConversionResult:
    return ConversionResult(
        total_chunks=1,
        written_chunks=1,
        skipped_chunks=0,
        resumed=False,
        completed=True,
    )
