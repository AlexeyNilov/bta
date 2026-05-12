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
