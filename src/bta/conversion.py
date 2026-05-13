from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from bta.output import (
    OutputPlan,
    build_conversion_state,
    hash_file,
    load_state,
    plan_output_paths,
    prepare_fresh_output,
    save_state,
    validate_resume,
)
from bta.pocket_tts import PocketTtsSynthesizer, ScipyWavWriter
from bta.text import chunk_text, clean_markdown_text

logger = logging.getLogger(__name__)
_worker_synthesizer: PocketTtsSynthesizer | None = None
_worker_writer: ScipyWavWriter | None = None


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice: str) -> Any:
        pass


class WavWriter(Protocol):
    def write(self, path: Path, audio: Any) -> None:
        pass


class ProgressReporter(Protocol):
    def report(self, current_chunk: int, total_chunks: int) -> None:
        pass


@dataclass(frozen=True)
class ConversionRequest:
    input_path: Path
    chunk_target_chars: int
    voice: str
    output_dir: Path = Path("output")
    tts_workers: int = 1


@dataclass(frozen=True)
class ConversionResult:
    total_chunks: int
    written_chunks: int
    skipped_chunks: int
    resumed: bool
    completed: bool


@dataclass(frozen=True)
class SynthesisJob:
    chunk_number: int
    text: str
    voice: str
    output_path: Path


def convert_markdown(
    request: ConversionRequest,
    synthesizer: SpeechSynthesizer | None = None,
    writer: WavWriter | None = None,
    progress_reporter: ProgressReporter | None = None,
) -> ConversionResult:
    if request.tts_workers < 1:
        raise ValueError("tts_workers must be a positive integer")

    source_text = request.input_path.read_text(encoding="utf-8")
    chunks = chunk_text(clean_markdown_text(source_text), request.chunk_target_chars)
    plan = plan_output_paths(request.input_path, len(chunks), request.output_dir)
    input_sha256 = hash_file(request.input_path)
    start_chunk_number, skipped_chunks, resumed = prepare_conversion(
        request,
        plan,
        input_sha256,
    )

    written_chunks = synthesize_chunks(
        request,
        plan,
        chunks,
        input_sha256,
        start_chunk_number,
        synthesizer,
        writer,
        progress_reporter,
    )
    return ConversionResult(
        total_chunks=len(chunks),
        written_chunks=written_chunks,
        skipped_chunks=skipped_chunks,
        resumed=resumed,
        completed=True,
    )


def prepare_conversion(
    request: ConversionRequest,
    plan: OutputPlan,
    input_sha256: str,
) -> tuple[int, int, bool]:
    if plan.state_path.exists():
        state = load_state(plan.state_path)
        if not state.completed:
            decision = validate_resume(
                state,
                input_path=request.input_path,
                input_sha256=input_sha256,
                chunk_target_chars=request.chunk_target_chars,
                voice=request.voice,
            )
            logger.info("Resuming conversion from chunk %s", decision.next_chunk_number)
            return decision.next_chunk_number, decision.last_successful_chunk, True

    logger.info("Fresh conversion will overwrite generated WAV files")
    prepare_fresh_output(plan)
    return 1, 0, False


def synthesize_chunks(
    request: ConversionRequest,
    plan: OutputPlan,
    chunks: list[str],
    input_sha256: str,
    start_chunk_number: int,
    synthesizer: SpeechSynthesizer | None,
    writer: WavWriter | None,
    progress_reporter: ProgressReporter | None,
) -> int:
    if request.tts_workers > 1:
        return synthesize_chunks_parallel(
            request=request,
            plan=plan,
            chunks=chunks,
            input_sha256=input_sha256,
            start_chunk_number=start_chunk_number,
            progress_reporter=progress_reporter,
        )
    if synthesizer is None or writer is None:
        raise ValueError("synthesizer and writer are required for single-worker conversion")

    written_chunks = 0
    for chunk_number in range(start_chunk_number, len(chunks) + 1):
        chunk_text_value = chunks[chunk_number - 1]
        audio = synthesizer.synthesize(chunk_text_value, request.voice)
        writer.write(plan.wav_paths[chunk_number - 1], audio)
        save_progress(
            request=request,
            plan=plan,
            input_sha256=input_sha256,
            last_successful_chunk=chunk_number,
            total_chunks=len(chunks),
        )
        if progress_reporter is not None:
            progress_reporter.report(chunk_number, len(chunks))
        written_chunks += 1
    return written_chunks


def synthesize_chunks_parallel(
    request: ConversionRequest,
    plan: OutputPlan,
    chunks: list[str],
    input_sha256: str,
    start_chunk_number: int,
    progress_reporter: ProgressReporter | None,
    executor_factory: Callable[[int], Any] | None = None,
    completed_futures: Callable[[list[Any]], Iterable[Any]] = as_completed,
) -> int:
    if executor_factory is None:
        executor_factory = create_process_pool_executor

    written_chunks = 0
    completed_chunk_numbers: set[int] = set()
    last_saved_chunk = start_chunk_number - 1
    futures: list[Any] = []

    with executor_factory(request.tts_workers) as executor:
        for job in synthesis_jobs(request, plan, chunks, start_chunk_number):
            futures.append(executor.submit(synthesize_chunk_with_pocket_tts, job))

        try:
            for future in completed_futures(futures):
                chunk_number = int(future.result())
                completed_chunk_numbers.add(chunk_number)
                written_chunks += 1
                next_saved_chunk = highest_contiguous_chunk(
                    completed_chunk_numbers,
                    last_saved_chunk,
                )
                if next_saved_chunk > last_saved_chunk:
                    save_progress(
                        request=request,
                        plan=plan,
                        input_sha256=input_sha256,
                        last_successful_chunk=next_saved_chunk,
                        total_chunks=len(chunks),
                    )
                    if progress_reporter is not None:
                        progress_reporter.report(next_saved_chunk, len(chunks))
                    last_saved_chunk = next_saved_chunk
        except BaseException:
            for future in futures:
                future.cancel()
            raise

    return written_chunks


def create_process_pool_executor(max_workers: int) -> ProcessPoolExecutor:
    return ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=initialize_pocket_tts_worker,
    )


def synthesis_jobs(
    request: ConversionRequest,
    plan: OutputPlan,
    chunks: list[str],
    start_chunk_number: int,
) -> list[SynthesisJob]:
    return [
        SynthesisJob(
            chunk_number=chunk_number,
            text=chunks[chunk_number - 1],
            voice=request.voice,
            output_path=plan.wav_paths[chunk_number - 1],
        )
        for chunk_number in range(start_chunk_number, len(chunks) + 1)
    ]


def highest_contiguous_chunk(completed_chunk_numbers: set[int], last_saved_chunk: int) -> int:
    next_chunk = last_saved_chunk + 1
    while next_chunk in completed_chunk_numbers:
        last_saved_chunk = next_chunk
        next_chunk += 1
    return last_saved_chunk


def initialize_pocket_tts_worker() -> None:
    global _worker_synthesizer, _worker_writer
    _worker_synthesizer = PocketTtsSynthesizer()
    _worker_writer = ScipyWavWriter(_worker_synthesizer.sample_rate)


def synthesize_chunk_with_pocket_tts(job: SynthesisJob) -> int:
    if _worker_synthesizer is None or _worker_writer is None:
        initialize_pocket_tts_worker()

    if _worker_synthesizer is None or _worker_writer is None:
        raise RuntimeError("Pocket TTS worker was not initialized")

    audio = _worker_synthesizer.synthesize(job.text, job.voice)
    _worker_writer.write(job.output_path, audio)
    return job.chunk_number


def save_progress(
    request: ConversionRequest,
    plan: OutputPlan,
    input_sha256: str,
    last_successful_chunk: int,
    total_chunks: int,
) -> None:
    save_state(
        plan.state_path,
        build_conversion_state(
            input_path=request.input_path,
            input_sha256=input_sha256,
            chunk_target_chars=request.chunk_target_chars,
            voice=request.voice,
            last_successful_chunk=last_successful_chunk,
            total_chunks=total_chunks,
            completed=last_successful_chunk == total_chunks,
        ),
    )
