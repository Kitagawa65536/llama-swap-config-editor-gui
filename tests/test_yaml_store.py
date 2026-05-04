from pathlib import Path
from uuid import uuid4

from config_services import AdvancedConfigService, GlobalSettingsService, ModelConfigService
from models import GlobalSettingsForm, ModelForm
from schema_validator import ConfigSchemaValidator
from yaml_store import YamlConfigStore


def work_dir() -> Path:
    path = Path("tests") / "_work" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_round_trip_keeps_unknown_keys_and_comments():
    tmp_path = work_dir()
    config = tmp_path / "config.yaml"
    config.write_text(
        """# top comment
unknownRoot: keep
models:
  old-model:
    # cmd comment
    cmd: llama-server --model /old.gguf --port ${PORT} --foo bar
    unknownModelKey: keep
""",
        encoding="utf-8",
    )
    store = YamlConfigStore()
    model_service = ModelConfigService()
    data, _raw = store.load(config)

    form = model_service.model_form_from_mapping("old-model", data["models"]["old-model"])
    form.model_path = "/new.gguf"
    model_service.apply_model_form(data, "old-model", form)

    dumped = store.dump_to_string(data)
    assert "# top comment" in dumped
    assert "unknownRoot: keep" in dumped
    assert "unknownModelKey: keep" in dumped
    assert "/new.gguf" in dumped


def test_save_creates_backup_and_replaces_file():
    tmp_path = work_dir()
    config = tmp_path / "config.yaml"
    config.write_text("models: {}\n", encoding="utf-8")
    store = YamlConfigStore()
    model_service = ModelConfigService()
    data, _raw = store.load(config)
    form = ModelForm(model_id="added", llama_server_path="llama-server", model_path="/m.gguf")
    model_service.apply_model_form(data, None, form)

    ok, message, backup = store.save(config, data)

    assert ok
    assert "Saved" in message
    assert backup is not None and backup.exists()
    assert "added:" in config.read_text(encoding="utf-8")


def test_validation_failure_does_not_modify_file():
    tmp_path = work_dir()
    config = tmp_path / "config.yaml"
    schema = tmp_path / "schema.json"
    config.write_text("models: {}\n", encoding="utf-8")
    schema.write_text(
        '{"type":"object","required":["requiredKey"],"properties":{"requiredKey":{"type":"string"}}}',
        encoding="utf-8",
    )
    store = YamlConfigStore()
    data, _raw = store.load(config)
    validator = ConfigSchemaValidator(schema)

    ok, message, backup = store.save(config, data, validator)

    assert not ok
    assert "requiredKey" in message
    assert backup is None
    assert config.read_text(encoding="utf-8") == "models: {}\n"


def test_parse_raw_rejects_invalid_yaml_without_touching_existing_state():
    store = YamlConfigStore()
    data = store.parse_raw("models: {}\n")

    try:
        store.parse_raw("models:\n  bad: [\n")
    except Exception:
        pass

    assert "models" in data


def test_model_service_builds_list_items_from_existing_models():
    store = YamlConfigStore()
    model_service = ModelConfigService()
    data = store.parse_raw(
        """models:
  sample:
    name: Sample Model
    ttl: 60
    cmd: llama-server --model /models/sample.gguf --port ${PORT}
"""
    )

    items = model_service.list_items(data)

    assert len(items) == 1
    assert items[0].model_id == "sample"
    assert items[0].subtitle == "Sample Model"
    assert items[0].model_path == "/models/sample.gguf"
    assert items[0].ttl == "60"


def test_global_settings_service_applies_and_removes_root_settings():
    store = YamlConfigStore()
    service = GlobalSettingsService()
    data = store.parse_raw("healthCheckTimeout: 30\nlogLevel: info\n")

    service.apply_global_settings(
        data,
        GlobalSettingsForm(
            health_check_timeout="",
            log_level="debug",
            start_port="8080",
            send_loading_state=True,
        ),
    )

    assert "healthCheckTimeout" not in data
    assert data["logLevel"] == "debug"
    assert data["startPort"] == 8080
    assert data["sendLoadingState"] is True


def test_advanced_service_exposes_sections_and_matrix_groups_conflict():
    store = YamlConfigStore()
    service = AdvancedConfigService(store)
    data = store.parse_raw(
        """macros:
  gpu: --n-gpu-layers 99
matrix: {}
groups: {}
"""
    )

    sections = service.sections(data)

    assert [section.key for section in sections] == ["macros", "matrix", "groups"]
    assert "gpu:" in sections[0].yaml_fragment
    assert service.has_matrix_groups_conflict(data)
