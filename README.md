# bta

Book to Audio converter. `bta` converts local Markdown files into ordered WAV
chunks using Pocket TTS.

## Installation

```bash
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
BTA_VOICE=alba
```

`BTA_CHUNK_TARGET_CHARS` must be a positive integer. `BTA_VOICE` is passed to
Pocket TTS and defaults to `alba`.

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
book_name=book
pandoc input/$book_name.epub -t markdown_strict -o input/$book_name.md

bta convert input/$book_name.md

for f in output/$book_name_*.wav; do
    echo "file '$PWD/$f'"
done > output/$book_name.txt
ffmpeg -f concat -safe 0 -i output/$book_name.txt \
       -c:a libmp3lame -q:a 2 \
       output/$book_name.mp3

ffplay output/$book_name.mp3
```

## References

* For EPUB to text conversion: https://pandoc.org/
* For PDF to text conversion: https://github.com/run-llama/liteparse
* TTS: https://github.com/kyutai-labs/pocket-tts
