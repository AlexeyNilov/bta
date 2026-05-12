import json
from pathlib import Path

import pytest

from bta.output import (
    ConversionState,
    ResumeValidationError,
    build_conversion_state,
    hash_file,
    load_state,
    plan_output_paths,
    prepare_fresh_output,
    save_state,
    validate_resume,
)


def test_plan_output_paths_uses_default_output_folder_and_creates_it(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    input_path = Path("book.md")
    input_path.write_text("text", encoding="utf-8")

    plan = plan_output_paths(input_path, total_chunks=1)

    assert plan.output_dir == Path("output")
    assert plan.output_dir.is_dir()


def test_plan_output_paths_reuses_existing_output_folder(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    output_dir = Path("output")
    output_dir.mkdir()
    marker = output_dir / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    input_path = Path("book.md")
    input_path.write_text("text", encoding="utf-8")

    plan = plan_output_paths(input_path, total_chunks=1)

    assert plan.output_dir == output_dir
    assert marker.read_text(encoding="utf-8") == "keep"


def test_plan_output_paths_names_wav_files_from_input_stem_in_order(tmp_path):
    input_path = tmp_path / "input.md"
    input_path.write_text("text", encoding="utf-8")

    plan = plan_output_paths(input_path, total_chunks=2, output_dir=tmp_path / "audio")

    assert plan.wav_paths == [
        tmp_path / "audio" / "input_000001.wav",
        tmp_path / "audio" / "input_000002.wav",
    ]
    assert plan.state_path == tmp_path / "audio" / "input.state.json"


def test_prepare_fresh_output_removes_generated_files_and_keeps_unrelated_files(tmp_path):
    input_path = tmp_path / "book.md"
    input_path.write_text("text", encoding="utf-8")
    plan = plan_output_paths(input_path, total_chunks=2, output_dir=tmp_path / "audio")
    plan.wav_paths[0].write_bytes(b"old audio")
    unrelated = plan.output_dir / "other_000001.wav"
    unrelated.write_bytes(b"keep")

    prepare_fresh_output(plan)

    assert not plan.wav_paths[0].exists()
    assert unrelated.read_bytes() == b"keep"


def test_save_state_writes_versioned_state_contents(tmp_path):
    input_path = tmp_path / "book.md"
    input_path.write_text("hello", encoding="utf-8")
    state_path = tmp_path / "output" / "book.state.json"
    state = build_conversion_state(
        input_path=input_path,
        input_sha256=hash_file(input_path),
        chunk_target_chars=2000,
        voice="alba",
        last_successful_chunk=2,
        total_chunks=3,
        completed=False,
    )

    save_state(state_path, state)

    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved == {
        "schema_version": 1,
        "input_path": str(input_path.resolve()),
        "input_sha256": hash_file(input_path),
        "chunk_target_chars": 2000,
        "voice": "alba",
        "last_successful_chunk": 2,
        "total_chunks": 3,
        "completed": False,
    }


def test_load_state_round_trips_saved_state(tmp_path):
    state_path = tmp_path / "book.state.json"
    state = ConversionState(
        schema_version=1,
        input_path="/tmp/book.md",
        input_sha256="abc123",
        chunk_target_chars=3000,
        voice="bruce",
        last_successful_chunk=1,
        total_chunks=4,
        completed=False,
    )

    save_state(state_path, state)

    assert load_state(state_path) == state


def test_validate_resume_accepts_matching_incomplete_state(tmp_path):
    input_path = tmp_path / "book.md"
    input_path.write_text("hello", encoding="utf-8")
    state = build_conversion_state(
        input_path=input_path,
        input_sha256=hash_file(input_path),
        chunk_target_chars=2000,
        voice="alba",
        last_successful_chunk=2,
        total_chunks=4,
        completed=False,
    )

    decision = validate_resume(
        state,
        input_path=input_path,
        input_sha256=hash_file(input_path),
        chunk_target_chars=2000,
        voice="alba",
    )

    assert decision.next_chunk_number == 3
    assert decision.last_successful_chunk == 2


@pytest.mark.parametrize(
    ("input_sha256", "chunk_target_chars", "voice"),
    [
        ("different", 2000, "alba"),
        ("abc123", 3000, "alba"),
        ("abc123", 2000, "bruce"),
    ],
)
def test_validate_resume_rejects_input_hash_or_config_mismatch(
    tmp_path,
    input_sha256,
    chunk_target_chars,
    voice,
):
    input_path = tmp_path / "book.md"
    input_path.write_text("hello", encoding="utf-8")
    state = build_conversion_state(
        input_path=input_path,
        input_sha256="abc123",
        chunk_target_chars=2000,
        voice="alba",
        last_successful_chunk=1,
        total_chunks=2,
        completed=False,
    )

    with pytest.raises(ResumeValidationError, match="Cannot resume"):
        validate_resume(
            state,
            input_path=input_path,
            input_sha256=input_sha256,
            chunk_target_chars=chunk_target_chars,
            voice=voice,
        )
