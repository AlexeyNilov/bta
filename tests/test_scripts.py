import os
import subprocess
from pathlib import Path


def test_merge_wavs_merges_folder_wavs_in_filename_order(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "merge_wavs.sh"
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "b.wav").write_bytes(b"second")
    (audio_dir / "a.wav").write_bytes(b"first")
    (audio_dir / "notes.txt").write_text("ignore", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ffmpeg_args = tmp_path / "ffmpeg-args.txt"
    fake_ffmpeg = fake_bin / "ffmpeg"
    fake_ffmpeg.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'printf "%s\\n" "$@" > "$FFMPEG_ARGS_FILE"\n'
        'touch "${@: -1}"\n',
        encoding="utf-8",
    )
    fake_ffmpeg.chmod(0o755)
    env = {
        **os.environ,
        "FFMPEG_ARGS_FILE": str(ffmpeg_args),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
    }

    result = subprocess.run(
        ["bash", str(script_path), str(audio_dir)],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (audio_dir / "audio.mp3").exists()
    ffmpeg_call = ffmpeg_args.read_text(encoding="utf-8").splitlines()
    concat_list = Path(ffmpeg_call[ffmpeg_call.index("-i") + 1])
    assert concat_list.read_text(encoding="utf-8").splitlines() == [
        f"file '{audio_dir / 'a.wav'}'",
        f"file '{audio_dir / 'b.wav'}'",
    ]
    assert ffmpeg_call[-1] == str(audio_dir / "audio.mp3")
