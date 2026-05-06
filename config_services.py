from __future__ import annotations

from typing import Any

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString

from command_builder import build_command, format_command_for_yaml, update_form_from_mapping
from models import AdvancedSection, GlobalSettingsForm, ModelForm, ModelListItem
from yaml_store import YamlConfigStore, YamlStoreError


ADVANCED_SECTION_KEYS = ["macros", "matrix", "groups", "hooks", "peers"]


class ModelConfigService:
    def model_items(self, data: Any) -> list[tuple[str, CommentedMap]]:
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, dict):
            return []
        return [(str(model_id), model_data) for model_id, model_data in models.items() if isinstance(model_data, dict)]

    def list_items(self, data: Any) -> list[ModelListItem]:
        items: list[ModelListItem] = []
        for model_id, model_data in self.model_items(data):
            form = self.model_form_from_mapping(model_id, model_data)
            items.append(
                ModelListItem(
                    model_id=model_id,
                    subtitle=form.name or ", ".join(form.aliases) or "-",
                    model_path=form.model_path or "(model path unknown)",
                    ttl=form.ttl or "-",
                )
            )
        return items

    def model_form_from_mapping(self, model_id: str, mapping: dict) -> ModelForm:
        return update_form_from_mapping(model_id, mapping)

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
        model["cmd"] = LiteralScalarString(format_command_for_yaml(build_command(form)))
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

    def delete_model(self, data: Any, model_id: str) -> bool:
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, CommentedMap):
            raise YamlStoreError("models must be a mapping")
        if model_id not in models:
            return False
        del models[model_id]
        return True

    def preview_command(self, form: ModelForm) -> str:
        return build_command(form)


class GlobalSettingsService:
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


class AdvancedConfigService:
    def __init__(self, store: YamlConfigStore) -> None:
        self.store = store

    def sections(self, data: Any) -> list[AdvancedSection]:
        if not isinstance(data, dict):
            return []
        return [
            AdvancedSection(key=key, yaml_fragment=self.store.dump_to_string(data[key]))
            for key in ADVANCED_SECTION_KEYS
            if key in data
        ]

    def has_matrix_groups_conflict(self, data: Any) -> bool:
        return isinstance(data, dict) and "matrix" in data and "groups" in data


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
