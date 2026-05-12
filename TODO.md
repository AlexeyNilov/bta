# Backlog

Implementation plan for the first Markdown-to-WAV audiobook workflow.

## Assumptions

* [ ] Treat `doc/requirements.md` as the source of truth for first-version
      behavior.
* [ ] Keep the public CLI minimal: `bta convert <input.md>`, `bta --version`,
      and help.
* [ ] Keep first-version conversion config limited to `BTA_CHUNK_TARGET_CHARS`
      and `BTA_VOICE`.
* [ ] Avoid loading Pocket TTS in unit tests; test the converter through injected
      synthesizer and WAV writer interfaces.

## Phase 1: Configuration and CLI Contract

* [x] Add tests for `BTA_CHUNK_TARGET_CHARS` defaulting to `2000`, accepting a
      positive integer, and rejecting invalid values.
* [x] Add tests for `BTA_VOICE` defaulting to `alba` and accepting non-empty
      configured values.
* [x] Extend `Config` with `chunk_target_chars` and `voice`.
* [x] Replace template CLI help text with `bta convert <input.md>` usage.
* [x] Add CLI tests for help, version, unknown command, missing input, stdin not
      supported, and local file path validation.
* [x] Implement `convert` command parsing without adding tuning flags.

## Phase 2: Text Cleanup and Chunking

* [x] Add tests for removing single-line and multiline embedded HTML tags.
* [x] Add tests for preserving word spacing when HTML occurs between words, such
      as `This <span ...></span>mission` becoming `This mission`.
* [x] Add tests showing non-HTML Markdown content is preserved for now.
* [x] Implement a text cleanup module for HTML removal and whitespace
      normalization.
* [x] Add tests for paragraph-aware chunking with a target character count.
* [x] Add tests proving chunking never splits a sentence.
* [x] Add tests for a single sentence longer than the target becoming one
      oversized chunk.
* [x] Implement sentence-boundary-aware chunking.

## Phase 3: Output Paths and State

* [x] Add tests for default output folder `output/`, create-if-missing, and
      reuse-if-existing behavior.
* [x] Add tests for output names based on input stem and six-digit one-based
      ordering, such as `input_000001.wav`.
* [x] Add tests for fresh conversions overwriting generated files.
* [x] Define a versioned state data model for `<input-stem>.state.json`.
* [x] Add tests for state contents: input path, input SHA-256,
      `BTA_CHUNK_TARGET_CHARS`, `BTA_VOICE`, last successful chunk, total chunks,
      and completion status.
* [x] Add tests for safe resume from a matching incomplete state file.
* [x] Add tests for rejecting resume when input hash or relevant config differs.
* [x] Implement output path planning, input hashing, state load/save, and resume
      validation.

## Phase 4: Conversion Orchestration

* [ ] Define small protocols/interfaces for speech synthesis and WAV writing.
* [ ] Add tests for fail-fast behavior on chunk synthesis or write failure.
* [ ] Add tests that successful WAV files and state remain after failure.
* [ ] Add tests that resume skips successful chunks and continues with the next
      chunk.
* [ ] Implement the conversion service using injected synthesizer and writer
      dependencies.
* [ ] Make overwrite behavior explicit in logs or status output.

## Phase 5: Pocket TTS Integration

* [ ] Add a thin Pocket TTS adapter that loads `TTSModel` once per conversion.
* [ ] Add adapter-level tests with fakes or mocks for `TTSModel.load_model`,
      `get_state_for_audio_prompt`, and `generate_audio`.
* [ ] Add a WAV writer using `scipy.io.wavfile.write` or the writer expected by
      Pocket TTS runtime dependencies.
* [ ] Wire the CLI `convert` command to the conversion service, Pocket TTS
      adapter, and WAV writer.
* [ ] Decide whether `scipy` must be an explicit project dependency after
      confirming Pocket TTS dependency behavior.

## Phase 6: Documentation and Packaging

* [ ] Update `README.md` with installation, `.env`, and `bta convert <input.md>`
      usage.
* [ ] Add or update `.env.example` with only `BTA_CHUNK_TARGET_CHARS` and
      `BTA_VOICE`.
* [ ] Update `pyproject.toml` metadata to remove leftover MCP/template keywords
      and classifiers.
* [ ] Bump `pyproject.toml` version using semantic versioning after behavior is
      implemented.
* [ ] Run `make format`.
* [ ] Run `make lint`.
* [ ] Run `make mypy`.
* [ ] Run `make test`.
