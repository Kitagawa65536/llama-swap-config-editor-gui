from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from platformdirs import user_config_dir


APP_NAME = "llama-swap-config-editor"
APP_AUTHOR = "oss"


@dataclass
class AppSettings:
    recent_configs: list[str] = field(default_factory=list)
    recent_schemas: list[str] = field(default_factory=list)
    default_llama_server_path: str = ""
    default_models_dir: str = ""


class AppSettingsRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(user_config_dir(APP_NAME, APP_AUTHOR)) / "settings.json"

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            defaults = AppSettings()
            values = {key: data.get(key, getattr(defaults, key)) for key in AppSettings.__dataclass_fields__}
            values["recent_configs"] = values["recent_configs"] or []
            values["recent_schemas"] = values["recent_schemas"] or []
            values["default_llama_server_path"] = values["default_llama_server_path"] or ""
            values["default_models_dir"] = values["default_models_dir"] or ""
            return AppSettings(**values)
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2, ensure_ascii=False), encoding="utf-8")

    def add_recent_config(self, settings: AppSettings, path: str) -> None:
        settings.recent_configs = _with_recent(settings.recent_configs, path)
        self.save(settings)

    def add_recent_schema(self, settings: AppSettings, path: str) -> None:
        settings.recent_schemas = _with_recent(settings.recent_schemas, path)
        self.save(settings)


def _with_recent(items: list[str], path: str, limit: int = 10) -> list[str]:
    normalized = str(Path(path))
    return [normalized] + [item for item in items if item != normalized][: limit - 1]
