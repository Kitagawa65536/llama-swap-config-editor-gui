import json
from pathlib import Path
from uuid import uuid4

from app_settings import AppSettings, AppSettingsRepository
from i18n import I18n


def work_dir() -> Path:
    path = Path("tests") / "_work" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_app_settings_loads_language_default_for_legacy_settings():
    settings_path = work_dir() / "settings.json"
    settings_path.write_text(json.dumps({"recent_configs": ["config.yaml"]}), encoding="utf-8")

    settings = AppSettingsRepository(settings_path).load()

    assert settings.language == "ja"
    assert settings.recent_configs == ["config.yaml"]


def test_app_settings_persists_language():
    settings_path = work_dir() / "settings.json"
    repo = AppSettingsRepository(settings_path)
    settings = AppSettings(language="ja")

    repo.set_language(settings, "en")
    loaded = repo.load()

    assert loaded.language == "en"


def test_i18n_translates_placeholders_and_falls_back_to_english():
    locales = work_dir() / "locales"
    locales.mkdir()
    (locales / "ja.json").write_text(json.dumps({"message": "Saved in ja: {name}"}), encoding="utf-8")
    (locales / "en.json").write_text(json.dumps({"fallback": "Fallback text"}), encoding="utf-8")
    i18n = I18n("ja", locales_dir=locales)

    assert i18n.translate("message", name="config.yaml") == "Saved in ja: config.yaml"
    assert i18n.translate("fallback") == "Fallback text"
    assert i18n.translate("missing.key") == "missing.key"
