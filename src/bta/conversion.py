from __future__ import annotations

import logging
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
from bta.text import chunk_text, clean_markdown_text

logger = logging.getLogger(__name__)


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice: str) -> Any:
        pass


class WavWriter(Protocol):
    def write(self, path: Path, audio: Any) -> None:
        pass


@dataclass(frozen=True)
class ConversionRequest:
    input_path: Path
    chunk_target_chars: int
    voice: str
    output_dir: Path = Path("output")


@dataclass(frozen=True)
class ConversionResult:
    total_chunks: int
    written_chunks: int
    skipped_chunks: int
    resumed: bool
    completed: bool


def convert_markdown(
    request: ConversionRequest,
    synthesizer: SpeechSynthesizer,
    writer: WavWriter,
) -> ConversionResult:
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
    synthesizer: SpeechSynthesizer,
    writer: WavWriter,
) -> int:
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
        written_chunks += 1
    return written_chunks


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
