import logging
from pathlib import Path

import pytest

from bta.conversion import ConversionRequest, convert_markdown
from bta.output import build_conversion_state, hash_file, load_state, save_state


class FakeSynthesizer:
    def __init__(self, failure_on_call: int | None = None) -> None:
        self.failure_on_call = failure_on_call
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, voice: str) -> bytes:
        self.calls.append((text, voice))
        if self.failure_on_call == len(self.calls):
            raise RuntimeError("synthesis failed")
        return f"audio-{len(self.calls)}".encode()


class FakeWavWriter:
    def __init__(self, failure_on_call: int | None = None) -> None:
        self.failure_on_call = failure_on_call
        self.calls: list[tuple[Path, bytes]] = []

    def write(self, path: Path, audio: bytes) -> None:
        self.calls.append((path, audio))
        if self.failure_on_call == len(self.calls):
            raise RuntimeError("write failed")
        path.write_bytes(audio)


def test_convert_markdown_stops_on_synthesis_failure_and_keeps_successful_output(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.")
    request = request_for(input_path, tmp_path)
    synthesizer = FakeSynthesizer(failure_on_call=2)
    writer = FakeWavWriter()

    with pytest.raises(RuntimeError, match="synthesis failed"):
        convert_markdown(request, synthesizer=synthesizer, writer=writer)

    assert (tmp_path / "output" / "book_000001.wav").read_bytes() == b"audio-1"
    assert not (tmp_path / "output" / "book_000002.wav").exists()
    state = load_state(tmp_path / "output" / "book.state.json")
    assert state.last_successful_chunk == 1
    assert state.total_chunks == 2
    assert not state.completed


def test_convert_markdown_stops_on_write_failure_and_keeps_successful_output(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.")
    request = request_for(input_path, tmp_path)
    synthesizer = FakeSynthesizer()
    writer = FakeWavWriter(failure_on_call=2)

    with pytest.raises(RuntimeError, match="write failed"):
        convert_markdown(request, synthesizer=synthesizer, writer=writer)

    assert (tmp_path / "output" / "book_000001.wav").read_bytes() == b"audio-1"
    assert not (tmp_path / "output" / "book_000002.wav").exists()
    state = load_state(tmp_path / "output" / "book.state.json")
    assert state.last_successful_chunk == 1
    assert state.total_chunks == 2
    assert not state.completed


def test_convert_markdown_resumes_by_skipping_successful_chunks(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "book_000001.wav").write_bytes(b"existing audio")
    save_state(
        output_dir / "book.state.json",
        build_conversion_state(
            input_path=input_path,
            input_sha256=hash_file(input_path),
            chunk_target_chars=20,
            voice="alba",
            last_successful_chunk=1,
            total_chunks=2,
            completed=False,
        ),
    )
    synthesizer = FakeSynthesizer()
    writer = FakeWavWriter()

    result = convert_markdown(request_for(input_path, tmp_path), synthesizer, writer)

    assert result.resumed
    assert result.skipped_chunks == 1
    assert result.written_chunks == 1
    assert synthesizer.calls == [("Second sentence.", "alba")]
    assert (output_dir / "book_000001.wav").read_bytes() == b"existing audio"
    assert (output_dir / "book_000002.wav").read_bytes() == b"audio-1"
    state = load_state(output_dir / "book.state.json")
    assert state.last_successful_chunk == 2
    assert state.completed


def test_convert_markdown_logs_fresh_overwrite_behavior(caplog, tmp_path):
    input_path = write_input(tmp_path, "First sentence.")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "book_000001.wav").write_bytes(b"old audio")

    with caplog.at_level(logging.INFO):
        result = convert_markdown(
            request_for(input_path, tmp_path),
            synthesizer=FakeSynthesizer(),
            writer=FakeWavWriter(),
        )

    assert not result.resumed
    assert (output_dir / "book_000001.wav").read_bytes() == b"audio-1"
    assert "Fresh conversion will overwrite generated WAV files" in caplog.text


def write_input(tmp_path: Path, text: str) -> Path:
    input_path = tmp_path / "book.md"
    input_path.write_text(text, encoding="utf-8")
    return input_path


def request_for(input_path: Path, tmp_path: Path) -> ConversionRequest:
    return ConversionRequest(
        input_path=input_path,
        chunk_target_chars=20,
        voice="alba",
        output_dir=tmp_path / "output",
    )
