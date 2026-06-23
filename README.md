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
BTA_TTS_WORKERS=4  # 4 gives the best result on 8 core CPU
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

Add inline pause tags to insert silence into generated audio:

```markdown
Hello. [1s] This starts after one second of silence.
```

Supported pause syntax is `[1s]`, `[1.5s]`, or `[0.25s]`. Pause tags are not
spoken, and unsupported syntax is treated as ordinary text.

## Flow

Think of the pipeline as three passes: extract the book into plain Markdown,
shape the text for clean narration, then render and stitch the audio.

### 1. Extract the Source Book

Start by turning the original EPUB or PDF into a Markdown file under `input/`.
Use the tool that fits the source format:

```
lit parse book.pdf --no-ocr -o input/book.md  # https://github.com/run-llama/liteparse
pandoc book.epub -t markdown_strict -o input/book.md  # https://pandoc.org/
```

### 2. Prepare the Text for Speech

Clean the extracted Markdown before synthesis. For long books, split the text
into chapter-sized files first, then remove visual-only ebook artifacts such as
image references, table-of-contents links, anchors, worksheet blanks, and bare
URLs.

Useful Codex skills:

* `split-ebook-into-chapters` for cleanup and chaptering
* `merge-chapters-into-md` for merging back
* `add-pause-tags` for adding silence

The goal is not to make pretty Markdown. The goal is clean narration: text that
sounds intentional when read aloud.

### 3. Render WAV Chunks

Run `bta` on the prepared Markdown file:

```bash
bta convert input/book.md
```

`bta` writes ordered WAV chunks to `output/` and saves conversion state so an
interrupted matching run can resume.

### 4. Merge the Audiobook

When the WAV chunks are ready, merge them into a single MP3:

```bash
bash scripts/merge_wavs.sh ./output
```

## References

* For EPUB to text conversion: https://pandoc.org/
* For PDF to text conversion: https://github.com/run-llama/liteparse
* TTS: https://github.com/kyutai-labs/pocket-tts
* Voices: alba, bill_boerst, charles, eponine, jean, peter_yearsley, stuart_bell 
