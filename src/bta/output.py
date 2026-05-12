from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

STATE_SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = Path("output")


@dataclass(frozen=True)
class OutputPlan:
    output_dir: Path
    wav_paths: list[Path]
    state_path: Path


@dataclass(frozen=True)
class ConversionState:
    schema_version: int
    input_path: str
    input_sha256: str
    chunk_target_chars: int
    voice: str
    last_successful_chunk: int
    total_chunks: int
    completed: bool


@dataclass(frozen=True)
class ResumeDecision:
    next_chunk_number: int
    last_successful_chunk: int


class ResumeValidationError(ValueError):
    pass


def plan_output_paths(
    input_path: Path,
    total_chunks: int,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> OutputPlan:
    if total_chunks < 1:
        raise ValueError("total_chunks must be a positive integer")

    output_dir.mkdir(parents=True, exist_ok=True)
    wav_paths = [
        output_dir / f"{input_path.stem}_{chunk_number:06d}.wav"
        for chunk_number in range(1, total_chunks + 1)
    ]
    state_path = output_dir / f"{input_path.stem}.state.json"
    return OutputPlan(output_dir=output_dir, wav_paths=wav_paths, state_path=state_path)


def prepare_fresh_output(plan: OutputPlan) -> None:
    for wav_path in plan.wav_paths:
        if wav_path.exists():
            wav_path.unlink()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_conversion_state(
    input_path: Path,
    input_sha256: str,
    chunk_target_chars: int,
    voice: str,
    last_successful_chunk: int,
    total_chunks: int,
    completed: bool,
) -> ConversionState:
    return ConversionState(
        schema_version=STATE_SCHEMA_VERSION,
        input_path=str(input_path.resolve()),
        input_sha256=input_sha256,
        chunk_target_chars=chunk_target_chars,
        voice=voice,
        last_successful_chunk=last_successful_chunk,
        total_chunks=total_chunks,
        completed=completed,
    )


def save_state(state_path: Path, state: ConversionState) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(asdict(state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_state(state_path: Path) -> ConversionState:
    raw_state = json.loads(state_path.read_text(encoding="utf-8"))
    return state_from_json(raw_state)


def state_from_json(raw_state: dict[str, Any]) -> ConversionState:
    return ConversionState(
        schema_version=int(raw_state["schema_version"]),
        input_path=str(raw_state["input_path"]),
        input_sha256=str(raw_state["input_sha256"]),
        chunk_target_chars=int(raw_state["chunk_target_chars"]),
        voice=str(raw_state["voice"]),
        last_successful_chunk=int(raw_state["last_successful_chunk"]),
        total_chunks=int(raw_state["total_chunks"]),
        completed=bool(raw_state["completed"]),
    )


def validate_resume(
    state: ConversionState,
    input_path: Path,
    input_sha256: str,
    chunk_target_chars: int,
    voice: str,
) -> ResumeDecision:
    if resume_mismatch_reasons(state, input_path, input_sha256, chunk_target_chars, voice):
        raise ResumeValidationError("Cannot resume because conversion state does not match")
    if state.completed:
        raise ResumeValidationError("Cannot resume completed conversion state")

    return ResumeDecision(
        next_chunk_number=state.last_successful_chunk + 1,
        last_successful_chunk=state.last_successful_chunk,
    )


def resume_mismatch_reasons(
    state: ConversionState,
    input_path: Path,
    input_sha256: str,
    chunk_target_chars: int,
    voice: str,
) -> list[str]:
    expected_path = str(input_path.resolve())
    return [
        reason
        for reason, mismatched in (
            ("schema_version", state.schema_version != STATE_SCHEMA_VERSION),
            ("input_path", state.input_path != expected_path),
            ("input_sha256", state.input_sha256 != input_sha256),
            ("chunk_target_chars", state.chunk_target_chars != chunk_target_chars),
            ("voice", state.voice != voice),
        )
        if mismatched
    ]
