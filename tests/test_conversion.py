import logging
from pathlib import Path

import pytest

from bta.conversion import ConversionRequest, convert_markdown, synthesize_chunks_parallel
from bta.output import build_conversion_state, hash_file, load_state, plan_output_paths, save_state


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


class RecordingProgressReporter:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def report(self, current_chunk: int, total_chunks: int) -> None:
        self.calls.append((current_chunk, total_chunks))


class FakeFuture:
    def __init__(
        self,
        chunk_number: int,
        output_path: Path,
        exception: Exception | None = None,
    ) -> None:
        self.chunk_number = chunk_number
        self.output_path = output_path
        self.exception = exception
        self.cancel_calls = 0

    def result(self) -> int:
        if self.exception is not None:
            raise self.exception
        self.output_path.write_bytes(f"audio-{self.chunk_number}".encode())
        return self.chunk_number

    def cancel(self) -> None:
        self.cancel_calls += 1


class FakeExecutor:
    def __init__(self, futures_by_chunk: dict[int, FakeFuture]) -> None:
        self.futures_by_chunk = futures_by_chunk
        self.submitted_chunks: list[int] = []

    def __enter__(self) -> "FakeExecutor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def submit(self, worker: object, job: object) -> FakeFuture:
        del worker
        chunk_number = int(getattr(job, "chunk_number"))
        self.submitted_chunks.append(chunk_number)
        return self.futures_by_chunk[chunk_number]


def test_convert_markdown_reports_current_chunk_of_total_chunks(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.")
    progress_reporter = RecordingProgressReporter()

    convert_markdown(
        request_for(input_path, tmp_path),
        synthesizer=FakeSynthesizer(),
        writer=FakeWavWriter(),
        progress_reporter=progress_reporter,
    )

    assert progress_reporter.calls == [(1, 2), (2, 2)]


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


def test_parallel_synthesis_writes_all_expected_chunks_and_marks_complete(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.\n\nThird sentence.")
    request = request_for(input_path, tmp_path, tts_workers=3)
    plan = plan_output_paths(input_path, total_chunks=3, output_dir=request.output_dir)
    futures_by_chunk = {
        chunk_number: FakeFuture(chunk_number, plan.wav_paths[chunk_number - 1])
        for chunk_number in [1, 2, 3]
    }
    executor = FakeExecutor(futures_by_chunk)
    completion_order = [futures_by_chunk[2], futures_by_chunk[1], futures_by_chunk[3]]

    written_chunks = synthesize_chunks_parallel(
        request=request,
        plan=plan,
        chunks=["First sentence.", "Second sentence.", "Third sentence."],
        input_sha256=hash_file(input_path),
        start_chunk_number=1,
        progress_reporter=None,
        executor_factory=lambda max_workers: executor,
        completed_futures=lambda futures: completion_order,
    )

    assert written_chunks == 3
    assert executor.submitted_chunks == [1, 2, 3]
    assert [path.read_bytes() for path in plan.wav_paths] == [b"audio-1", b"audio-2", b"audio-3"]
    state = load_state(plan.state_path)
    assert state.last_successful_chunk == 3
    assert state.completed


def test_parallel_synthesis_reports_only_highest_contiguous_completed_chunk(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.\n\nThird sentence.")
    request = request_for(input_path, tmp_path, tts_workers=3)
    plan = plan_output_paths(input_path, total_chunks=3, output_dir=request.output_dir)
    futures_by_chunk = {
        chunk_number: FakeFuture(chunk_number, plan.wav_paths[chunk_number - 1])
        for chunk_number in [1, 2, 3]
    }
    executor = FakeExecutor(futures_by_chunk)
    completion_order = [futures_by_chunk[2], futures_by_chunk[1], futures_by_chunk[3]]
    progress_reporter = RecordingProgressReporter()

    synthesize_chunks_parallel(
        request=request,
        plan=plan,
        chunks=["First sentence.", "Second sentence.", "Third sentence."],
        input_sha256=hash_file(input_path),
        start_chunk_number=1,
        progress_reporter=progress_reporter,
        executor_factory=lambda max_workers: executor,
        completed_futures=lambda futures: completion_order,
    )

    assert progress_reporter.calls == [(2, 3), (3, 3)]


def test_parallel_synthesis_keeps_out_of_order_success_unresumable_on_later_failure(tmp_path):
    input_path = write_input(tmp_path, "First sentence.\n\nSecond sentence.\n\nThird sentence.")
    request = request_for(input_path, tmp_path, tts_workers=3)
    plan = plan_output_paths(input_path, total_chunks=3, output_dir=request.output_dir)
    futures_by_chunk = {
        1: FakeFuture(1, plan.wav_paths[0]),
        2: FakeFuture(2, plan.wav_paths[1]),
        3: FakeFuture(3, plan.wav_paths[2], exception=RuntimeError("synthesis failed")),
    }
    executor = FakeExecutor(futures_by_chunk)
    completion_order = [futures_by_chunk[2], futures_by_chunk[3], futures_by_chunk[1]]

    with pytest.raises(RuntimeError, match="synthesis failed"):
        synthesize_chunks_parallel(
            request=request,
            plan=plan,
            chunks=["First sentence.", "Second sentence.", "Third sentence."],
            input_sha256=hash_file(input_path),
            start_chunk_number=1,
            progress_reporter=None,
            executor_factory=lambda max_workers: executor,
            completed_futures=lambda futures: completion_order,
        )

    assert not plan.wav_paths[0].exists()
    assert plan.wav_paths[1].read_bytes() == b"audio-2"
    assert not plan.wav_paths[2].exists()
    assert not plan.state_path.exists()


def test_convert_markdown_resume_reports_only_chunks_that_are_processed(tmp_path):
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
    progress_reporter = RecordingProgressReporter()

    convert_markdown(
        request_for(input_path, tmp_path),
        synthesizer=FakeSynthesizer(),
        writer=FakeWavWriter(),
        progress_reporter=progress_reporter,
    )

    assert progress_reporter.calls == [(2, 2)]


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


def request_for(input_path: Path, tmp_path: Path, tts_workers: int = 1) -> ConversionRequest:
    return ConversionRequest(
        input_path=input_path,
        chunk_target_chars=20,
        voice="alba",
        output_dir=tmp_path / "output",
        tts_workers=tts_workers,
    )
