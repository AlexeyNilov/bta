# Backlog

## Parallel Pocket TTS Synthesis

Goal: reduce wall-clock conversion time by running independent TTS chunk
synthesis jobs concurrently.

Current `time bta convert input/test.md` 16 chunks
real    4m20.384s
user    7m25.192s
sys     0m4.862s

Assumptions:

- TTS generation dominates runtime; Markdown cleaning, chunking, hashing, and
  state serialization are not meaningful bottlenecks for book-sized inputs.
- A shared `PocketTtsSynthesizer` should not be used across threads until Pocket
  TTS explicitly documents thread-safe inference.
- Process-based parallelism is safer than thread-based parallelism because each
  worker owns its model instance and voice-state cache.
- The best worker count on an 8-core CPU may be lower than 8 if the TTS backend
  already uses multiple CPU threads internally.
- Resume state currently represents a contiguous successful prefix, not
  arbitrary completed chunks.

Implementation plan:

1. Add `BTA_TTS_WORKERS` config.
   - Default to `1` to preserve current behavior.
   - Validate as a positive integer.
   - Document the setting in `README.md`.

2. Add tests before implementation.
   - Config rejects invalid worker counts.
   - Single-worker conversion keeps current ordering and resume behavior.
   - Multi-worker conversion writes all expected chunks.
   - Multi-worker progress/state updates only advance through the highest
     contiguous completed chunk.
   - Failed synthesis leaves completed WAV files intact and does not mark later
     out-of-order chunks as resumable unless all earlier chunks completed.

3. Introduce a parallel synthesis path.
   - Keep the existing sequential path for `tts_workers == 1`.
   - Use `concurrent.futures.ProcessPoolExecutor` for `tts_workers > 1`.
   - Initialize one `PocketTtsSynthesizer` per process, not per chunk.
   - Have workers synthesize and write WAV output directly.
   - Return completed chunk numbers to the parent process.

4. Preserve safe resume semantics.
   - Track completed chunk numbers in the parent while workers finish
     out-of-order.
   - Save `last_successful_chunk` only when all previous chunks are complete.
   - Accept that a crash may redo already-written out-of-order chunks.
   - Consider a later state-schema change for per-chunk completion if redo cost
     proves significant.

5. Control CPU oversubscription.
   - Benchmark `BTA_TTS_WORKERS=2`, `4`, and `8`.
   - If Pocket TTS uses PyTorch CPU threads, consider setting per-worker torch
     threads explicitly, for example `max(1, cpu_count // workers)`.
   - Do not add this tuning until measured; wrong thread limits can slow down
     some machines.

6. Verification.
   - Run `make format`.
   - Run `make lint`.
   - Run `make mypy`.
   - Run a real conversion benchmark on `input/test.md` with worker counts `1`,
     `2`, `4`, and `8`. 

Open design choice:

- Keep the first version conservative by preserving the current contiguous
  resume state, or bump the state schema and store per-chunk completion to avoid
  redoing chunks after a crash. - Yes, lets be conservative for now
