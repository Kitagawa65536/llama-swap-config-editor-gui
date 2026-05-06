from pathlib import Path
from types import SimpleNamespace

from config_services import ModelConfigService
from main import LlamaSwapConfigEditor
from models import ConfigState, ModelForm
from yaml_store import YamlConfigStore


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
