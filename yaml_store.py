from __future__ import annotations

import os
import shutil
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

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
