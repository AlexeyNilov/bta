# bta

Book to Audio converter. `bta` converts local Markdown files into ordered WAV
chunks using Pocket TTS.

## Installation

```bash
git clone https://github.com/AlexeyNilov/bta.git
cd bta
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

For development checks:

```bash
pip install -e .[dev]
```

## Configuration

Configuration is loaded from environment variables and optional `.env` files.

```bash
BTA_CHUNK_TARGET_CHARS=2000
BTA_TTS_WORKERS=1
BTA_VOICE=alba
```

`BTA_CHUNK_TARGET_CHARS` must be a positive integer. `BTA_TTS_WORKERS` controls
how many independent Pocket TTS worker processes synthesize chunks concurrently
and defaults to `1` to preserve sequential conversion behavior. `BTA_VOICE` is
passed to Pocket TTS and defaults to `alba`.

`bta` sets `HF_HUB_OFFLINE=1` by default before loading Pocket TTS so cached
models do not trigger Hugging Face network checks on every run. For the first
model download or a refresh, run with `HF_HUB_OFFLINE=0`.

## Usage

Convert a local Markdown file:

```bash
bta convert input/book.md
```

Generated files are written to `output/` as `book_000001.wav`,
`book_000002.wav`, and so on. Conversion state is saved as
`output/book.state.json` so an interrupted matching conversion can resume.

## Flow

```bash
scripts/flow.sh book
scripts/flow.sh book --no-play
```

See [scripts/flow.sh](scripts/flow.sh) for the full EPUB-to-MP3 workflow.

To merge an existing folder of WAV files into one MP3:

```bash
scripts/merge_wavs.sh ./output
```

The merged file is written inside that folder using the folder name, for example
`output/output.mp3`. The merge inserts 2 seconds of silence after each WAV file
to create pauses between chapters.

## References

* For EPUB to text conversion: https://pandoc.org/
* For PDF to text conversion: https://github.com/run-llama/liteparse
* TTS: https://github.com/kyutai-labs/pocket-tts
* Voices: alba, bill_boerst, charles, eponine, jean, peter_yearsley, stuart_bell 
