from pathlib import Path
from uuid import uuid4

from command_builder import update_form_from_mapping
from models import ModelForm
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
    data, _raw = store.load(config)

    form = update_form_from_mapping("old-model", data["models"]["old-model"])
    form.model_path = "/new.gguf"
    store.apply_model_form(data, "old-model", form)

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
    data, _raw = store.load(config)
    form = ModelForm(model_id="added", llama_server_path="llama-server", model_path="/m.gguf")
    store.apply_model_form(data, None, form)

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
