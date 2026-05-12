# Decisions

## Why record decisions

Write down key development decisions while the context is fresh. A short note today can save hours later by explaining what was chosen, what was rejected, and why the trade-off made sense at the time.

## Guidance

Use a lightweight Architecture Decision Record (ADR) style:

* Record decisions that affect architecture, data flow, public APIs, dependencies, deployment, security, or long-term maintenance.
* Write the decision when it is made, not after the context has faded.
* Prefer short entries that explain the context, decision, alternatives, and consequences.
* Include enough reasoning for a future maintainer to understand the trade-off.
* Do not document every small implementation detail; focus on choices that would be costly or confusing to rediscover.
* Update or supersede earlier decisions instead of silently rewriting history.

## Entry template

```markdown
### YYYY-MM-DD: Decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What problem, constraint, or trade-off led to this decision?

**Decision:** What was chosen?

**Alternatives considered:** What other options were rejected, and why?

**Consequences:** What becomes easier, harder, riskier, or more constrained?
```

## Actual decisions

### 2026-05-12: Build a Markdown-to-WAV converter

**Status:** Accepted

**Context:** The project is starting from a Python package skeleton named `bta`
with a CLI entry point already declared in `pyproject.toml`.

**Decision:** The tool will convert Markdown (`.md`) text input into WAV audio
output.

**Alternatives considered:** Other source formats such as EPUB and PDF are
useful future inputs, and the README already notes Pandoc as a possible EPUB to
Markdown preprocessing step. They are not the initial primary input format.

**Consequences:** The first design can focus on Markdown parsing, text cleanup,
speech synthesis, WAV generation, and CLI ergonomics. EPUB/PDF support should be
treated as import or preprocessing work unless later requirements expand the
core scope.

### 2026-05-12: Provide a command-line interface

**Status:** Accepted

**Context:** The project already exposes a `bta` console script through
`pyproject.toml`, and the user explicitly requires a CLI interface. The initial
conversion command shape is `bta convert <input.md>`.

**Decision:** The primary product interface will be a CLI command with a
`convert` subcommand.

**Alternatives considered:** A library-only API, GUI, web app, or service API
could be useful later, but they are not required for the initial tool.

**Consequences:** Requirements should specify command syntax, arguments, exit
codes, file behavior, logging, and error messages. Public CLI behavior should be
treated as part of the product contract once implemented.

### 2026-05-12: Accept local Markdown files only

**Status:** Accepted

**Context:** The initial conversion workflow should stay simple and predictable.

**Decision:** `bta convert <input.md>` will accept a local Markdown file path and
will not read Markdown from stdin.

**Alternatives considered:** Supporting stdin would make shell pipelines easier,
but it would complicate naming output files from the input stem and is not needed
for the first audiobook workflow.

**Consequences:** The CLI can require a real input path, derive output chunk
names from that path, and report file-specific validation errors.

### 2026-05-12: Strip embedded HTML and preserve other Markdown initially

**Status:** Accepted

**Context:** Markdown produced from book sources can contain embedded HTML
artifacts such as pagebreak spans. These are not useful narration text and can
appear inside a sentence, for example between `This` and `mission`.

**Decision:** The first text cleanup pass will remove embedded HTML elements and
normalize whitespace so surrounding words remain readable, for example
`This <span ...></span>mission` becomes `This mission`. Other Markdown content
will be preserved for now unless later requirements define additional cleanup.

**Alternatives considered:** Fully parsing and rendering Markdown to plain text
would remove more formatting artifacts, but it may also discard content or make
premature decisions about headings, links, code blocks, and tables. Keeping all
HTML would leak source-format artifacts into generated speech.

**Consequences:** HTML removal needs to be robust enough for multiline tags and
inline tags. Future Markdown-specific cleanup decisions can be added without
changing the initial principle that HTML artifacts should not be spoken.

### 2026-05-12: Generate chunked WAV output

**Status:** Accepted

**Context:** The main use case is audiobook creation, where long Markdown inputs
are more practical to process and consume as smaller audio segments than as one
large file.

**Decision:** The converter will split Markdown input into chunks containing
several paragraphs each and generate a separate WAV file for each chunk. The
generated WAV files will be written into an output folder.

**Alternatives considered:** Generating one WAV file per Markdown input would
produce a simpler interface, but it would be less suitable for long audiobook
workflows and harder to recover from partial failures. Splitting by chapter or
heading may still be useful later, but paragraph chunks are the initial unit.

**Consequences:** The implementation needs deterministic chunking, stable output
file naming, output folder handling, and partial failure behavior.

### 2026-05-12: Use output as the default output folder

**Status:** Accepted

**Context:** The CLI should stay minimal, and generated audiobook chunks need a
predictable destination.

**Decision:** `bta convert <input.md>` will write generated WAV files to
`output/` by default. The converter will create `output/` if it is missing and
reuse it if it already exists.

**Alternatives considered:** Deriving an output folder from the input file name
would reduce collisions between runs but makes the default less predictable.
Requiring an explicit output folder would add CLI surface before it is needed.

**Consequences:** The output location is simple and stable. File naming and
collision behavior are defined separately.

### 2026-05-12: Name chunk WAV files deterministically and overwrite collisions

**Status:** Accepted

**Context:** Chunked audiobook output needs names that preserve playback order
and are predictable across repeated runs.

**Decision:** Generated WAV files will be named from the input file stem plus a
six-digit one-based chunk number, for example `output/input_000001.wav` and
`output/input_000002.wav`. If a generated file already exists, the converter
will overwrite it.

**Alternatives considered:** Appending suffixes would avoid overwrites but would
make repeated runs accumulate stale files. Failing on existing files would be
safer for accidental data preservation but less convenient while tuning settings.
Skipping existing files would imply resumability, which has not been designed
yet.

**Consequences:** Re-running conversion for the same input replaces previous
chunk WAV files with the same names. The implementation should make overwrite
behavior explicit in logs or status output.

### 2026-05-12: Fail fast and support validated resume

**Status:** Accepted

**Context:** Long audiobook conversions can fail after producing useful output.
The user should see failures immediately, but should not have to regenerate
successful chunks when retrying the same conversion.

**Decision:** Conversion will stop immediately on the first failed chunk and keep
already written WAV files. After each successfully written chunk, the converter
will update a state file named from the input stem, for example
`output/input.state.json`. A later run for the same input may resume from the
next chunk when the state is incomplete and matches the current input and
configuration. Resume validation will compare at least the input SHA-256 hash,
`BTA_CHUNK_TARGET_CHARS`, and `BTA_VOICE`. If validation fails, conversion will
fail instead of resuming. Fresh conversions continue to overwrite generated WAV
files using the deterministic output names.

**Alternatives considered:** Storing only the last successful chunk would be
simpler, but it could resume incorrectly after input or configuration changes.
Skipping failed chunks would produce incomplete audiobook output. Retrying
automatically may be useful later, but the first version should surface failures
directly.

**Consequences:** The implementation needs a versioned state schema, input
hashing, atomic or otherwise reliable state updates after each successful chunk,
and clear user-facing messages for resume, complete, and unsafe-resume cases.
Overwrite behavior differs between fresh conversion and resume: fresh conversion
overwrites generated outputs, while resume skips chunks already marked
successful.

### 2026-05-12: Make chunk size configurable without splitting sentences

**Status:** Accepted

**Context:** The optimal chunk size is not known yet and will likely need tuning
against real audiobook inputs and Pocket TTS behavior. Cutting audio generation
text in the middle of a sentence would create unnatural narration.

**Decision:** Chunk size will be configurable as a target character count named
`BTA_CHUNK_TARGET_CHARS`, with an initial default of 2000 characters. The chunker
must preserve sentence boundaries.

**Alternatives considered:** A fixed chunk size would make the first CLI simpler,
but it would lock in an untested value. Splitting strictly by raw character
limits would be easy to implement, but it risks breaking sentences and producing
poor audiobook output.

**Consequences:** The implementation needs a sentence-boundary-aware chunking
algorithm. If the configured target size falls inside a sentence, the chunker
should choose a nearby sentence boundary rather than splitting the sentence. If a
single sentence is longer than the configured target, it should remain one
oversized chunk.

### 2026-05-12: Keep tuning settings in environment configuration

**Status:** Accepted

**Context:** The initial CLI should stay minimal. Chunk sizing and other
conversion tuning values need to be adjustable, but exposing all of them as CLI
options would make the interface noisy before the right set of controls is known.
The existing project already loads environment variables from `.env`.

**Decision:** The first version will keep tunable conversion settings in
environment-based configuration loaded from `.env` instead of exposing them as
CLI arguments. The first-version conversion settings are limited to
`BTA_CHUNK_TARGET_CHARS` and `BTA_VOICE`.

**Alternatives considered:** CLI flags would make individual runs explicit, but
they would expand the public CLI contract before the settings have stabilized.
A separate config file could be useful later, but `.env` already matches the
current project skeleton.

**Consequences:** The CLI can remain close to `bta convert <input.md>`, while
configuration parsing and validation become important product behavior. The
project must document the two supported conversion environment variables and
avoid committing local `.env` files.

### 2026-05-12: Use Pocket TTS as the speech engine

**Status:** Accepted

**Context:** The project already lists `pocket-tts` as a dependency, and
`sample/intro.py` demonstrates its Python API using the `alba` voice. The
upstream project describes Pocket TTS as a CPU-friendly TTS package with a
Python API and CLI: https://github.com/kyutai-labs/pocket-tts

**Decision:** The first implementation will use `pocket-tts` for speech
generation. The Pocket TTS voice will be configurable through `BTA_VOICE`, with
`alba` as the default.

**Alternatives considered:** Other local TTS engines, hosted APIs, or a generic
provider abstraction could be added later. They are unnecessary until the first
Pocket TTS-based audiobook workflow exists.

**Consequences:** The converter should keep the Pocket TTS model and selected
voice state in memory across chunk generation, because the upstream examples note
that model and voice loading are relatively slow. Packaging and runtime checks
must account for Pocket TTS transitive dependencies such as PyTorch and WAV
writing support. Voice configuration must be validated as part of environment
configuration.

### 2026-05-12: Optimize first for audiobook creation

**Status:** Accepted

**Context:** The user identified audiobook creation as the main target use case.

**Decision:** Product and implementation choices should optimize for long-form
Markdown-to-audio conversion suitable for audiobooks.

**Alternatives considered:** Short document narration can still work if it falls
out naturally from the same flow, but it should not drive the first version's
trade-offs.

**Consequences:** Planning should prioritize chunking, ordering, resumability,
consistent voice settings, predictable file names, and error reporting for long
inputs.

### 2026-05-12: Keep requirements and decisions in project documentation

**Status:** Accepted

**Context:** The user wants ongoing planning input to be captured in
`doc/requirements.md` and `doc/decisions.md`.

**Decision:** New requirements will be recorded in `doc/requirements.md`, and
settled architectural, product, dependency, or interface decisions will be
recorded in `doc/decisions.md`.

**Alternatives considered:** Keeping planning only in chat would be faster in
the short term, but it would make the project history harder to review.

**Consequences:** The documentation becomes the source of truth for planning.
Open questions should remain explicit until answered instead of being silently
converted into assumptions.
