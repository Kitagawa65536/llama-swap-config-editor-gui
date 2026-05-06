from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


class SchemaValidationError(Exception):
    pass


class ConfigSchemaValidator:
    def __init__(self, schema_path: str | Path | None = None) -> None:
        self.schema_path = Path(schema_path) if schema_path else None
        self._schema: dict[str, Any] | None = None

    def load(self, schema_path: str | Path | None = None) -> None:
        if schema_path:
            self.schema_path = Path(schema_path)
        if not self.schema_path:
            self._schema = None
            return
        with self.schema_path.open("r", encoding="utf-8") as file:
            self._schema = json.load(file)

    def validate(self, data: Any) -> tuple[bool, str]:
        if self._schema is None:
            if self.schema_path:
                self.load()
            else:
                return True, "Schema not selected; validation skipped"
        try:
            jsonschema.Draft202012Validator.check_schema(self._schema)
            validator = jsonschema.Draft202012Validator(self._schema)
            errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        except jsonschema.SchemaError:
            validator = jsonschema.Draft7Validator(self._schema)
            errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            lines = []
            for error in errors[:8]:
                path = ".".join(str(part) for part in error.path) or "<root>"
                lines.append(f"{path}: {error.message}")
            if len(errors) > 8:
                lines.append(f"... and {len(errors) - 8} more")
            return False, "\n".join(lines)
        return True, "validation OK"
