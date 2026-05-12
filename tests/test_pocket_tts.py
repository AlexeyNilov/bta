from pathlib import Path

from bta.pocket_tts import PocketTtsSynthesizer, ScipyWavWriter


class FakeTTSModel:
    load_calls = 0

    def __init__(self) -> None:
        self.sample_rate = 24_000
        self.voice_calls: list[str] = []
        self.audio_calls: list[tuple[dict[str, str], str]] = []

    @classmethod
    def load_model(cls) -> "FakeTTSModel":
        cls.load_calls += 1
        return cls()

    def get_state_for_audio_prompt(self, voice: str) -> dict[str, str]:
        self.voice_calls.append(voice)
        return {"voice": voice}

    def generate_audio(self, model_state: dict[str, str], text_to_generate: str) -> str:
        self.audio_calls.append((model_state, text_to_generate))
        return f"audio for {text_to_generate}"


class FakeAudio:
    def __init__(self) -> None:
        self.numpy_calls = 0

    def numpy(self) -> list[float]:
        self.numpy_calls += 1
        return [0.0, 0.1]


class FakeWavfileModule:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, int, object]] = []

    def write(self, path: Path, sample_rate: int, data: object) -> None:
        self.calls.append((path, sample_rate, data))


def test_pocket_tts_synthesizer_loads_model_once_and_caches_voice_state(monkeypatch):
    FakeTTSModel.load_calls = 0
    monkeypatch.setattr("bta.pocket_tts.TTSModel", FakeTTSModel)

    synthesizer = PocketTtsSynthesizer()
    first_audio = synthesizer.synthesize("First chunk.", "alba")
    second_audio = synthesizer.synthesize("Second chunk.", "alba")

    assert FakeTTSModel.load_calls == 1
    assert synthesizer.sample_rate == 24_000
    assert synthesizer.model.voice_calls == ["alba"]
    assert synthesizer.model.audio_calls == [
        ({"voice": "alba"}, "First chunk."),
        ({"voice": "alba"}, "Second chunk."),
    ]
    assert first_audio == "audio for First chunk."
    assert second_audio == "audio for Second chunk."


def test_pocket_tts_synthesizer_loads_separate_voice_states(monkeypatch):
    FakeTTSModel.load_calls = 0
    monkeypatch.setattr("bta.pocket_tts.TTSModel", FakeTTSModel)

    synthesizer = PocketTtsSynthesizer()
    synthesizer.synthesize("First chunk.", "alba")
    synthesizer.synthesize("Second chunk.", "bruce")

    assert synthesizer.model.voice_calls == ["alba", "bruce"]


def test_scipy_wav_writer_writes_numpy_audio(tmp_path):
    wavfile_module = FakeWavfileModule()
    audio = FakeAudio()
    output_path = tmp_path / "chunk.wav"

    writer = ScipyWavWriter(sample_rate=24_000, wavfile_module=wavfile_module)
    writer.write(output_path, audio)

    assert audio.numpy_calls == 1
    assert wavfile_module.calls == [(output_path, 24_000, [0.0, 0.1])]
