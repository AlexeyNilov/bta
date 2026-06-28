# Requirements

## EARS (Easy Approach to Requirements Syntax)

Use the EARS structure for precise requirements:

> **While** `<optional precondition>`, **when** `<optional trigger>`, **the system shall** `<system response>`.

This helps ensure requirements are:

* Context-aware
* Trigger-based
* Action-specific

## Actual requirements

### Functional requirements

#### REQ-001: Convert Markdown to WAV

**When** the user provides a Markdown (`.md`) input document, **the system shall**
convert the document into one or more WAV audio files.

#### REQ-002: Provide a CLI interface

**When** the user installs or runs the project, **the system shall** provide a
command-line interface for starting the Markdown-to-audio conversion workflow.

#### REQ-003: Accept Markdown as source input

**When** the user starts a conversion, **the system shall** accept Markdown text as
the source document format.

#### REQ-004: Read local input files only

**When** the user starts a conversion, **the system shall** read Markdown input
from a local file path and shall not accept stdin as an input source.

#### REQ-005: Produce WAV as target output

**When** a conversion completes successfully, **the system shall** write audio in
WAV format.

#### REQ-006: Remove embedded HTML before speech

**When** preparing Markdown text for speech generation, **the system shall**
remove embedded HTML elements from the text.

#### REQ-007: Normalize whitespace after HTML removal

**When** embedded HTML removal leaves adjacent words separated only by the
removed element or by line breaks, **the system shall** preserve readable word
spacing, for example converting `This <span ...></span>mission` to
`This mission`.

#### REQ-008: Preserve non-HTML Markdown content initially

**When** preparing Markdown text for speech generation, **the system shall** keep
non-HTML Markdown content unchanged unless another requirement defines specific
cleanup behavior.

#### REQ-009: Split input into paragraph chunks

**When** converting a Markdown input document, **the system shall** split the
document into chunks containing several paragraphs each before generating audio.

#### REQ-010: Configure chunk size

**When** the user starts a conversion, **the system shall** allow the target chunk
size to be configured as a target character count through `BTA_CHUNK_TARGET_CHARS`
loaded from environment-based configuration.

#### REQ-011: Preserve sentence boundaries

**When** splitting Markdown input into chunks, **the system shall not** split text
in the middle of a sentence.

#### REQ-012: Use a default chunk target

**When** `BTA_CHUNK_TARGET_CHARS` is not configured, **the system shall** use a
default target chunk size of 2000 characters.

#### REQ-013: Allow oversized sentence chunks

**When** a single sentence exceeds the configured target character count, **the
system shall** keep that sentence in one oversized chunk instead of splitting it.

#### REQ-014: Generate one WAV file per chunk

**When** the system converts a text chunk, **the system shall** write that chunk's
audio to a separate WAV file.

#### REQ-015: Name chunk WAV files from input file stem

**When** the system writes chunk WAV files, **the system shall** name each file
using the input file stem followed by a six-digit one-based chunk number, for
example `output/input_000001.wav`, `output/input_000002.wav`.

#### REQ-016: Preserve chunk order in file names

**When** the system writes chunk WAV files, **the system shall** assign chunk
numbers in source text order.

#### REQ-017: Overwrite existing generated files

**When** a generated WAV file path already exists, **the system shall** overwrite
the existing file.

#### REQ-018: Write conversion output to a folder

**When** the user runs a conversion, **the system shall** write all generated WAV
files into an output folder.

#### REQ-019: Fail immediately on chunk conversion failure

**When** conversion of a chunk fails, **the system shall** stop the conversion
immediately and report the failure to the user.

#### REQ-020: Keep successful outputs after failure

**When** conversion fails after one or more chunks were written successfully,
**the system shall** keep the successfully written WAV files.

#### REQ-021: Write resumable conversion state

**When** a chunk WAV file is written successfully, **the system shall** update a
state file in the output folder using the input file stem and `.state.json`
suffix, for example `output/input.state.json`.

#### REQ-022: Track resume validation data

**When** writing conversion state, **the system shall** include enough data to
validate resume safety, including state schema version, input file path, input
SHA-256 hash, `BTA_CHUNK_TARGET_CHARS`, `BTA_VOICE`, last successful chunk
number, total chunk count, and completion status.

#### REQ-023: Mark completed conversions

**When** all chunks are converted successfully, **the system shall** mark the
state file as complete.

#### REQ-024: Resume incomplete conversions

**When** the user reruns conversion for an input with a matching incomplete state
file, **the system shall** skip chunks already marked successful and resume with
the next chunk.

#### REQ-025: Reject unsafe resume attempts

**When** an incomplete state file exists but its input hash or relevant
configuration does not match the current conversion, **the system shall** fail
with a clear error instead of resuming.

#### REQ-026: Overwrite on fresh conversion only

**When** no matching incomplete state file is being resumed, **the system shall**
treat conversion as fresh and overwrite generated WAV files that use the current
input's output file names.

#### REQ-027: Use the default output folder

**When** the user runs `bta convert <input.md>`, **the system shall** use
`output/` as the default output folder.

#### REQ-028: Create missing output folder

**When** the configured output folder does not exist, **the system shall** create
the folder before writing WAV files.

#### REQ-029: Reuse existing output folder

**When** the configured output folder already exists, **the system shall** reuse
that folder for generated WAV files.

#### REQ-030: Use the convert subcommand

**When** the user starts a conversion from the CLI, **the system shall** support
the command shape `bta convert <input.md>`.

#### REQ-031: Keep conversion CLI minimal

**When** the user starts a conversion from the CLI, **the system shall not**
require chunk-size or other tuning options as CLI arguments.

#### REQ-032: Use environment-based configuration

**When** the user needs to configure conversion behavior, **the system shall**
read configuration from environment variables, including variables loaded from
`.env`.

#### REQ-033: Limit first-version conversion settings

**When** loading first-version conversion settings, **the system shall** support
only `BTA_CHUNK_TARGET_CHARS` and `BTA_VOICE`.

#### REQ-034: Use Pocket TTS for speech generation

**When** generating speech audio, **the system shall** use the `pocket-tts`
Python package.

#### REQ-035: Configure Pocket TTS voice

**When** generating speech audio, **the system shall** allow the Pocket TTS voice
to be configured through `BTA_VOICE` loaded from environment-based configuration.

#### REQ-035a: Support local Pocket TTS voice state files

**When** `BTA_VOICE` points to a local `.safetensors` voice state file, **the
system shall** pass that voice state prompt to Pocket TTS for speech generation.

#### REQ-036: Use alba as the default voice

**When** `BTA_VOICE` is not configured, **the system shall** use `alba` as the
default Pocket TTS voice.

#### REQ-037: Optimize for audiobook creation

**When** prioritizing product behavior and implementation trade-offs, **the
system shall** treat audiobook creation from long-form Markdown text as the main
use case.

### Planning requirements

#### REQ-038: Track requirements in this document

**When** the user provides new project requirements, **the system shall** record
them in `doc/requirements.md`.

#### REQ-039: Track decisions in the decision log

**When** the user and assistant settle an architectural, product, dependency, or
interface choice, **the system shall** record it in `doc/decisions.md`.
