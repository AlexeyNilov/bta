from __future__ import annotations

import os
from collections.abc import MutableMapping
from importlib import import_module
from pathlib import Path
from typing import Any

import torch

from bta.pause_tags import PauseEvent, TextEvent, parse_pause_tags

TTSModel: Any | None = None
SCIPY_WAVFILE: Any = import_module("scipy.io.wavfile")
HF_HUB_OFFLINE = "HF_HUB_OFFLINE"


class PocketTtsSynthesizer:
    def __init__(self, environ: MutableMapping[str, str] = os.environ) -> None:
        self.environ = environ
        configure_huggingface_offline_mode(self.environ)
        self.model = load_tts_model_class().load_model()
        self.sample_rate = int(self.model.sample_rate)
        self._voice_states: dict[str, Any] = {}

    def synthesize(self, text: str, voice: str) -> Any:
        voice_state = self.get_voice_state(voice)
        return self.model.generate_audio(voice_state, text)

    def synthesize_with_pauses(self, text: str, voice: str) -> Any:
        pieces: list[Any] = []
        first_audio: Any | None = None

        for event in parse_pause_tags(text):
            if isinstance(event, TextEvent):
                chunk = event.text.strip()
                if not chunk:
                    continue
                audio = self.synthesize(chunk, voice)
                if first_audio is None:
                    first_audio = audio
                pieces.append(audio)
            else:
                pieces.append(event)

        if not pieces:
            return torch.zeros(0, dtype=torch.float32)

        return concatenate_audio_pieces(pieces, first_audio, self.sample_rate)

    def get_voice_state(self, voice: str) -> Any:
        if voice not in self._voice_states:
            self._voice_states[voice] = self.model.get_state_for_audio_prompt(voice)
        return self._voice_states[voice]


class ScipyWavWriter:
    def __init__(self, sample_rate: int, wavfile_module: Any = SCIPY_WAVFILE) -> None:
        self.sample_rate = sample_rate
        self.wavfile_module = wavfile_module

    def write(self, path: Path, audio: Any) -> None:
        self.wavfile_module.write(path, self.sample_rate, audio_to_wav_data(audio))


def audio_to_wav_data(audio: Any) -> Any:
    if hasattr(audio, "numpy"):
        return audio.numpy()
    return audio


def concatenate_audio_pieces(
    pieces: list[Any],
    first_audio: Any | None,
    sample_rate: int,
) -> Any:
    dtype = getattr(first_audio, "dtype", torch.float32)
    device = getattr(first_audio, "device", torch.device("cpu"))
    audio_pieces = [
        silence_for_pause(piece, sample_rate, dtype, device)
        if isinstance(piece, PauseEvent)
        else piece
        for piece in pieces
    ]
    return torch.cat(audio_pieces, dim=0)


def silence_for_pause(
    pause: PauseEvent,
    sample_rate: int,
    dtype: Any,
    device: Any,
) -> Any:
    sample_count = max(0, int(round(pause.seconds * sample_rate)))
    return torch.zeros(sample_count, dtype=dtype, device=device)


def configure_huggingface_offline_mode(environ: MutableMapping[str, str]) -> None:
    environ.setdefault(HF_HUB_OFFLINE, "1")


def load_tts_model_class() -> Any:
    global TTSModel
    if TTSModel is None:
        TTSModel = import_module("pocket_tts").TTSModel
    return TTSModel
