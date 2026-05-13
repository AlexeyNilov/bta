import logging

import pytest

from bta.config import load_config


def test_load_config_reads_log_level_from_dotenv_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=debug\n", encoding="utf-8")

    config = load_config()

    assert config.log_level == logging.DEBUG


def test_load_config_prefers_existing_log_level_env_var(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOG_LEVEL", "warning")
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=ERROR\n", encoding="utf-8")

    config = load_config()

    assert config.log_level == logging.WARNING


def test_load_config_rejects_unknown_log_level(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=LOUD\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported LOG_LEVEL"):
        load_config()


def test_load_config_defaults_chunk_target_chars_to_2000(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BTA_CHUNK_TARGET_CHARS", raising=False)

    config = load_config()

    assert config.chunk_target_chars == 2000


def test_load_config_accepts_positive_chunk_target_chars(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BTA_CHUNK_TARGET_CHARS", "3500")

    config = load_config()

    assert config.chunk_target_chars == 3500


@pytest.mark.parametrize("value", ["0", "-1", "abc", "2.5"])
def test_load_config_rejects_invalid_chunk_target_chars(monkeypatch, tmp_path, value):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BTA_CHUNK_TARGET_CHARS", value)

    with pytest.raises(ValueError, match="BTA_CHUNK_TARGET_CHARS"):
        load_config()


def test_load_config_defaults_tts_workers_to_one(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BTA_TTS_WORKERS", raising=False)

    config = load_config()

    assert config.tts_workers == 1


def test_load_config_accepts_positive_tts_workers(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BTA_TTS_WORKERS", "4")

    config = load_config()

    assert config.tts_workers == 4


@pytest.mark.parametrize("value", ["0", "-1", "abc", "2.5"])
def test_load_config_rejects_invalid_tts_workers(monkeypatch, tmp_path, value):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BTA_TTS_WORKERS", value)

    with pytest.raises(ValueError, match="BTA_TTS_WORKERS"):
        load_config()


def test_load_config_defaults_voice_to_alba(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BTA_VOICE", raising=False)

    config = load_config()

    assert config.voice == "alba"


def test_load_config_accepts_non_empty_voice(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BTA_VOICE", "  bruce  ")

    config = load_config()

    assert config.voice == "bruce"
