from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

TTSModel: Any = import_module("pocket_tts").TTSModel
SCIPY_WAVFILE: Any = import_module("scipy.io.wavfile")


class PocketTtsSynthesizer:
    def __init__(self) -> None:
        self.model = TTSModel.load_model()
        self.sample_rate = int(self.model.sample_rate)
        self._voice_states: dict[str, Any] = {}

    def synthesize(self, text: str, voice: str) -> Any:
        voice_state = self.get_voice_state(voice)
        return self.model.generate_audio(voice_state, text)

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
