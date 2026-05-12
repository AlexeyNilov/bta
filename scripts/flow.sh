#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: scripts/flow.sh <book-name> [--no-play]

Runs the full EPUB-to-MP3 flow:
  input/<book-name>.epub -> input/<book-name>.md -> output/<book-name>_*.wav -> output/<book-name>.mp3

Examples:
  scripts/flow.sh book
  scripts/flow.sh book --no-play
USAGE
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        exit 1
    fi
}

concat_escape() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\'/\\\'}
    printf '%s' "$value"
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage >&2
    exit 2
fi

book_name=$1
play_after_conversion=true

if [[ $# -eq 2 ]]; then
    case "$2" in
        --no-play)
            play_after_conversion=false
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $2" >&2
            usage >&2
            exit 2
            ;;
    esac
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_root=$(cd -- "$script_dir/.." && pwd)
cd "$project_root"

input_epub="input/$book_name.epub"
input_md="input/$book_name.md"
output_dir="output"
concat_list="$output_dir/$book_name.txt"
output_mp3="$output_dir/$book_name.mp3"

if [[ ! -f "$input_epub" ]]; then
    echo "Input EPUB not found: $input_epub" >&2
    exit 1
fi

require_command pandoc
require_command bta
require_command ffmpeg
if [[ "$play_after_conversion" == true ]]; then
    require_command ffplay
fi

mkdir -p "$output_dir"

echo "Converting EPUB to Markdown: $input_epub -> $input_md"
pandoc "$input_epub" -t markdown_strict -o "$input_md"

echo "Converting Markdown to WAV chunks: $input_md"
bta convert "$input_md"

shopt -s nullglob
wav_files=("$output_dir/$book_name"_*.wav)
shopt -u nullglob

if [[ ${#wav_files[@]} -eq 0 ]]; then
    echo "No WAV chunks found for $book_name in $output_dir" >&2
    exit 1
fi

printf '' > "$concat_list"
for wav_file in "${wav_files[@]}"; do
    absolute_wav=$(cd -- "$(dirname -- "$wav_file")" && pwd)/$(basename -- "$wav_file")
    printf "file '%s'\n" "$(concat_escape "$absolute_wav")" >> "$concat_list"
done

echo "Combining WAV chunks into MP3: $output_mp3"
ffmpeg -f concat -safe 0 -i "$concat_list" \
    -c:a libmp3lame -q:a 2 \
    "$output_mp3"

if [[ "$play_after_conversion" == true ]]; then
    ffplay "$output_mp3"
fi
