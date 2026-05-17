# Backlog

## Pause Tags

Goal: support inline pause tags such as `[1s]`, `[1.5s]`, and `[0.25s]` in
input Markdown. The tag should not be spoken; it should insert silence into the
generated WAV chunk.

Assumptions:

- Pocket TTS is pinned to `2.1.0`.
- `TTSModel.generate_audio(...)` returns a 1-D `torch.Tensor` of samples in this
  pinned version.
- Pause tags affect generated audio inside each WAV chunk, not global gaps
  between separately written chunk files.
- Invalid or unsupported pause syntax should be left as normal text unless the
  implementation explicitly adds validation.

Plan:

1. Add pause tag parsing with a focused event model: text events and pause
   events.
2. Cover parser behavior with tests for plain text, one pause, multiple pauses,
   leading/trailing pauses, decimal durations, and adjacent text.
3. Add a pause-aware synthesis path near `PocketTtsSynthesizer`, where
   `sample_rate`, tensor dtype, and tensor device are available.
4. Insert silence using `torch.zeros(round(seconds * sample_rate))` and
   concatenate pieces with `torch.cat(..., dim=0)`.
5. Ensure tags are removed from text before calling Pocket TTS.
6. Wire the pause-aware synthesis path into both sequential conversion and
   parallel worker conversion.
7. Add conversion tests proving `[1s]` is not spoken, silence is inserted, and
   resume/progress behavior remains unchanged.
8. Document pause tag syntax in `README.md`.
9. Bump the project version with a minor release when the feature is
   implemented.
