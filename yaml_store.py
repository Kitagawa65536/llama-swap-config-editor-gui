from __future__ import annotations

import os
import shutil
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from command_builder import build_command
from models import GlobalSettingsForm, ModelForm
from schema_validator import ConfigSchemaValidator


class YamlStoreError(Exception):
    pass


def make_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


class YamlConfigStore:
    def __init__(self) -> None:
        self.yaml = make_yaml()

    def load(self, path: str | Path) -> tuple[Any, str]:
        config_path = Path(path)
        text = config_path.read_text(encoding="utf-8")
        data = self.yaml.load(text) or CommentedMap()
        if not isinstance(data, CommentedMap):
            raise YamlStoreError("config.yaml root must be a mapping")
        return data, text

    def parse_raw(self, text: str) -> Any:
        data = self.yaml.load(text) or CommentedMap()
        if not isinstance(data, CommentedMap):
            raise YamlStoreError("YAML root must be a mapping")
        return data

    def dump_to_string(self, data: Any) -> str:
        stream = StringIO()
        self.yaml.dump(data, stream)
        return stream.getvalue()

    def model_items(self, data: Any) -> list[tuple[str, CommentedMap]]:
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, dict):
            return []
        return [(str(model_id), model_data) for model_id, model_data in models.items() if isinstance(model_data, dict)]

    def apply_model_form(self, data: Any, original_model_id: str | None, form: ModelForm) -> None:
        models = data.setdefault("models", CommentedMap())
        if not isinstance(models, CommentedMap):
            raise YamlStoreError("models must be a mapping")
        model_id = form.model_id.strip()
        if not model_id:
            raise YamlStoreError("model_id is required")
        if original_model_id and original_model_id != model_id:
            if model_id in models:
                raise YamlStoreError(f"model_id already exists: {model_id}")
            existing = models.pop(original_model_id, None)
            models[model_id] = existing if isinstance(existing, CommentedMap) else CommentedMap()
        elif model_id not in models:
            models[model_id] = CommentedMap()

        model = models[model_id]
        if not isinstance(model, CommentedMap):
            model = CommentedMap(model)
            models[model_id] = model
        model["cmd"] = build_command(form)
        if form.ttl.strip():
            model["ttl"] = _coerce_scalar(form.ttl)
        elif "ttl" in model:
            del model["ttl"]
        if form.aliases:
            seq = CommentedSeq(form.aliases)
            model["aliases"] = seq
        elif "aliases" in model:
            del model["aliases"]
        if form.name.strip():
            model["name"] = form.name.strip()
        elif "name" in model:
            del model["name"]

    def apply_global_settings(self, data: Any, form: GlobalSettingsForm) -> None:
        pairs = {
            "healthCheckTimeout": form.health_check_timeout,
            "logLevel": form.log_level,
            "startPort": form.start_port,
            "globalTTL": form.global_ttl,
        }
        for key, value in pairs.items():
            text = str(value).strip()
            if text:
                data[key] = _coerce_scalar(text)
            elif key in data:
                del data[key]
        if form.send_loading_state is not None:
            data["sendLoadingState"] = bool(form.send_loading_state)

    def global_settings_form(self, data: Any) -> GlobalSettingsForm:
        return GlobalSettingsForm(
            health_check_timeout=_string_or_empty(data.get("healthCheckTimeout")),
            log_level=_string_or_empty(data.get("logLevel")),
            start_port=_string_or_empty(data.get("startPort")),
            global_ttl=_string_or_empty(data.get("globalTTL")),
            send_loading_state=data.get("sendLoadingState") if isinstance(data.get("sendLoadingState"), bool) else None,
        )

    def save(
        self,
        path: str | Path,
        data: Any,
        validator: ConfigSchemaValidator | None = None,
    ) -> tuple[bool, str, Path | None]:
        valid, message = validator.validate(data) if validator else (True, "validation skipped")
        if not valid:
            return False, message, None

        config_path = Path(path)
        backup_path = self._backup_path(config_path)
        tmp_path = config_path.with_name(config_path.name + ".tmp")
        try:
            if config_path.exists():
                shutil.copy2(config_path, backup_path)
            with tmp_path.open("w", encoding="utf-8", newline="\n") as file:
                self.yaml.dump(data, file)
            os.replace(tmp_path, config_path)
            return True, f"保存しました / Saved. Backup: {backup_path.name}", backup_path
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _backup_path(self, config_path: Path) -> Path:
        simple = config_path.with_suffix(config_path.suffix + ".bak")
        if not simple.exists():
            return simple
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return config_path.with_name(f"{config_path.name}.{timestamp}.bak")


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def _coerce_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped.lower() in {"true", "false"}:
        return stripped.lower() == "true"
    try:
        return int(stripped)
    except ValueError:
        return stripped
