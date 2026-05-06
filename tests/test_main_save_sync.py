from pathlib import Path
from types import SimpleNamespace

from app_settings import AppSettings
from config_services import GlobalSettingsService, ModelConfigService
from main import LlamaSwapConfigEditor
from models import ConfigState, ModelForm
from schema_validator import ConfigSchemaValidator
from yaml_store import YamlConfigStore


class FakeSettingsRepository:
    def __init__(self) -> None:
        self.recent: list[str] = []

    def add_recent_config(self, settings: AppSettings, path: str) -> None:
        settings.recent_configs = [path]
        self.recent.append(path)


def test_apply_pending_form_edits_for_save_updates_cmd_context_length():
    store = YamlConfigStore()
    data = store.parse_raw(
        """models:
  sample:
    cmd: llama-server --model /models/sample.gguf --port ${PORT}
"""
    )
    app = LlamaSwapConfigEditor.__new__(LlamaSwapConfigEditor)
    app.page = SimpleNamespace(route="/models")
    app.store = store
    app.model_service = ModelConfigService()
    app.state = ConfigState(path=Path("config.yaml"), data=data, raw_yaml=store.dump_to_string(data))
    app.selected_model_id = "sample"
    app.current_model_form = ModelForm(
        model_id="sample",
        llama_server_path="llama-server",
        model_path="/models/sample.gguf",
        context_length="4096",
        context_length_max=8192,
    )
    app.raw_editor = None

    app.apply_pending_form_edits_for_save()

    cmd = app.state.data["models"]["sample"]["cmd"]
    assert "--ctx-size 4096" in cmd
    assert "context_length_max" not in app.state.raw_yaml
    assert app.state.dirty is True


def test_model_list_items_filters_by_model_id_search_term():
    store = YamlConfigStore()
    data = store.parse_raw(
        """models:
  qwen-14b:
    cmd: llama-server --model /models/qwen.gguf --port ${PORT}
  mistral-7b:
    cmd: llama-server --model /models/mistral.gguf --port ${PORT}
"""
    )
    app = LlamaSwapConfigEditor.__new__(LlamaSwapConfigEditor)
    app.store = store
    app.model_service = ModelConfigService()
    app.state = ConfigState(data=data)
    app.model_search_term = "QWEN"

    items = app.model_list_items()

    assert [item.model_id for item in items] == ["qwen-14b"]


def test_create_config_at_path_initializes_new_config_state():
    tmp_path = Path("tests") / "_work" / "create-config-state"
    tmp_path.mkdir(parents=True, exist_ok=True)
    config = tmp_path / "config.yaml"
    if config.exists():
        config.unlink()
    store = YamlConfigStore()
    app = LlamaSwapConfigEditor.__new__(LlamaSwapConfigEditor)
    app.store = store
    app.global_settings_service = GlobalSettingsService()
    app.settings = AppSettings()
    app.settings_repo = FakeSettingsRepository()
    app.validator = ConfigSchemaValidator()
    app.state = ConfigState(dirty=True)
    app.selected_model_id = "old"
    app.current_model_form = ModelForm(model_id="old")
    app.raw_editor = object()
    app.t = lambda key, **kwargs: key.format(**kwargs)
    app.refresh = lambda: None
    app.validate_config = lambda _event=None: None

    app.create_config_at_path(config)

    assert config.exists()
    assert app.state.path == config
    assert app.state.data["models"] == {}
    assert app.state.dirty is False
    assert app.selected_model_id is None
    assert app.current_model_form is None
    assert app.raw_editor is None
    assert app.settings.recent_configs == [str(config)]


def test_create_config_at_path_does_not_write_when_schema_validation_fails():
    tmp_path = Path("tests") / "_work" / "create-config-validation"
    tmp_path.mkdir(parents=True, exist_ok=True)
    config = tmp_path / "config.yaml"
    schema = tmp_path / "schema.json"
    if config.exists():
        config.unlink()
    schema.write_text(
        '{"type":"object","required":["requiredKey"],"properties":{"requiredKey":{"type":"string"}}}',
        encoding="utf-8",
    )
    app = LlamaSwapConfigEditor.__new__(LlamaSwapConfigEditor)
    app.store = YamlConfigStore()
    app.global_settings_service = GlobalSettingsService()
    app.settings = AppSettings()
    app.settings_repo = FakeSettingsRepository()
    app.validator = ConfigSchemaValidator(schema)
    app.state = ConfigState()
    app.t = lambda key, **kwargs: key.format(**kwargs)
    app.refresh = lambda: None

    app.create_config_at_path(config)

    assert not config.exists()
    assert app.state.path is None
    assert "requiredKey" in app.state.last_message
