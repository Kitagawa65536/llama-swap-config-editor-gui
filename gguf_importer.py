from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from models import GgufImportSuggestion


CONTEXT_KEYS = [
    "llama.context_length",
    "qwen35.context_length",
    "qwen2.context_length",
    "gemma3.context_length",
    "general.context_length",
]

NAME_KEYS = [
    "general.name",
    "general.basename",
    "general.finetune",
]


def normalize_model_id(name: str) -> str:
    stem = Path(name).stem.lower()
    normalized = re.sub(r"[^a-z0-9_-]+", "-", stem)
    normalized = re.sub(r"-+", "-", normalized).strip("-_")
    return normalized or "model"


def import_gguf(path: str | Path) -> GgufImportSuggestion:
    gguf_path = Path(path).resolve()
    metadata: dict[str, Any] = {}
    try:
        from gguf import GGUFReader

        reader = GGUFReader(str(gguf_path))
        for field in getattr(reader, "fields", {}).values():
            key = getattr(field, "name", None)
            if not key:
                continue
            metadata[str(key)] = _field_value(field)
    except Exception as exc:
        metadata["read_error"] = str(exc)

    model_name = _first_text(metadata, NAME_KEYS) or gguf_path.stem
    context_length_max = _first_context_length(metadata, CONTEXT_KEYS)
    context_length = str(context_length_max) if context_length_max is not None else ""
    return GgufImportSuggestion(
        model_id=normalize_model_id(gguf_path.stem),
        name=model_name,
        model_path=str(gguf_path),
        context_length=context_length,
        context_length_max=context_length_max,
        gpu_offload_layers="",
        metadata=metadata,
    )


def import_many(paths: list[str | Path]) -> list[GgufImportSuggestion]:
    return [import_gguf(path) for path in paths]


def _field_value(field: Any) -> Any:
    contents = getattr(field, "contents", None)
    if callable(contents):
        try:
            return contents()
        except Exception:
            pass
    parts = getattr(field, "parts", None)
    if parts:
        values = [getattr(part, "tolist", lambda: part)() for part in parts]
        if len(values) == 1:
            return values[0]
        return values
    data = getattr(field, "data", None)
    if hasattr(data, "tolist"):
        return data.tolist()
    return data


def _first_text(metadata: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                continue
        if isinstance(value, list) and value:
            value = value[0]
        return str(value)
    return ""


def _first_context_length(metadata: dict[str, Any], keys: list[str]) -> int | None:
    for key in _context_keys_for_metadata(metadata, keys):
        context_length = normalize_context_length(metadata.get(key))
        if context_length is not None:
            return context_length
    return None


def _context_keys_for_metadata(metadata: dict[str, Any], keys: list[str]) -> list[str]:
    ordered_keys = list(keys)
    architecture = _normalize_text_value(metadata.get("general.architecture"))
    if architecture:
        architecture_key = f"{architecture}.context_length"
        if architecture_key not in ordered_keys:
            ordered_keys.insert(0, architecture_key)
    return ordered_keys


def normalize_context_length(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, list):
        if len(value) != 1:
            return None
        value = value[0]
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    try:
        context_length = int(value)
    except (TypeError, ValueError):
        return None
    return context_length if context_length > 0 else None


def _normalize_text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        value = value[0]
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    return str(value).strip()
