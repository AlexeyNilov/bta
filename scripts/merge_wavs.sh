#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: scripts/merge_wavs.sh <folder>

Merges all WAV files directly inside <folder> into <folder>/<folder-name>.mp3,
with 3 seconds of silence after each WAV file and a 3 dB volume boost.

Example:
  scripts/merge_wavs.sh ./output
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

if [[ $# -ne 1 ]]; then
    usage >&2
    exit 2
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

audio_dir=${1%/}

if [[ ! -d "$audio_dir" ]]; then
    echo "Folder not found: $audio_dir" >&2
    exit 1
fi

require_command ffmpeg

output_name=$(basename -- "$audio_dir")
concat_list="$audio_dir/$output_name.txt"
output_mp3="$audio_dir/$output_name.mp3"
pause_seconds=3
volume_boost=3dB

shopt -s nullglob
wav_files=("$audio_dir"/*.wav)
shopt -u nullglob

if [[ ${#wav_files[@]} -eq 0 ]]; then
    echo "No WAV files found in $audio_dir" >&2
    exit 1
fi

silence_dir=$(mktemp -d)
trap 'rm -rf "$silence_dir"' EXIT
silence_wav="$silence_dir/silence_3s.wav"

echo "Creating ${pause_seconds}s silence segment"
ffmpeg -y -stream_loop -1 -i "${wav_files[0]}" \
    -t "$pause_seconds" -af volume=0 \
    "$silence_wav"

printf '' > "$concat_list"
for wav_file in "${wav_files[@]}"; do
    absolute_wav=$(cd -- "$(dirname -- "$wav_file")" && pwd)/$(basename -- "$wav_file")
    printf "file '%s'\n" "$(concat_escape "$absolute_wav")" >> "$concat_list"
    printf "file '%s'\n" "$(concat_escape "$silence_wav")" >> "$concat_list"
done

echo "Combining WAV files into MP3 with ${volume_boost} volume boost: $output_mp3"
ffmpeg -y -f concat -safe 0 -i "$concat_list" \
    -af "volume=$volume_boost" \
    -c:a libmp3lame -q:a 2 \
    "$output_mp3"
