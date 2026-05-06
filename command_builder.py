from __future__ import annotations

import re
import shlex
from dataclasses import asdict
from typing import Iterable

from models import ModelForm

KNOWN_CACHE_QUANT_TYPES = (
    "f32",
    "f16",
    "bf16",
    "q8_0",
    "q4_0",
    "q4_1",
    "iq4_nl",
    "q5_0",
    "q5_1",
)

SPEC_TYPE_OPTIONS = (
    "none",
    "ngram-cache",
    "ngram-simple",
    "ngram-map-k",
    "ngram-map-k4v",
    "ngram-mod",
)

CACHE_TYPE_OPTIONS = {
    "--cache-type-k": "k_cache_quant_type",
    "--cache-type-v": "v_cache_quant_type",
}

VALUE_OPTIONS = {
    "--model": "model_path",
    "-m": "model_path",
    "--mmproj": "mmproj_path",
    "-mm": "mmproj_path",
    "--ctx-size": "context_length",
    "-c": "context_length",
    "--n-gpu-layers": "gpu_offload_layers",
    "-ngl": "gpu_offload_layers",
    "--threads": "cpu_threads",
    "-t": "cpu_threads",
    "--batch-size": "eval_batch_size",
    "-b": "eval_batch_size",
    "--ubatch-size": "ubatch_size",
    "-ub": "ubatch_size",
    "--seed": "seed",
    "--spec-ngram-size-n": "spec_ngram_size_n",
    "--draft": "draft_max",
    "--draft-n": "draft_max",
    "--draft-min": "draft_min",
    "--draft-n-min": "draft_min",
    "--draft-max": "draft_max",
}

IGNORED_VALUE_OPTIONS = {"--port"}
EXPERT_USED_COUNT_SUFFIX = ".expert_used_count"


def quote_arg(value: str) -> str:
    if value == "":
        return '""'
    if value == "${PORT}":
        return value
    if re.search(r"[\s\"']", value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def split_command(command: str) -> list[str]:
    lexer = shlex.shlex(command.replace("\r\n", "\n"), posix=False)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _clean_token(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def build_command(form: ModelForm) -> str:
    args = [
        quote_arg(form.llama_server_path.strip() or "llama-server"),
        "--model",
        quote_arg(form.model_path.strip()),
        "--port",
        "${PORT}",
    ]
    option_map = [
        ("--mmproj", form.mmproj_path),
        ("--ctx-size", form.context_length),
        ("--n-gpu-layers", form.gpu_offload_layers),
        ("--threads", form.cpu_threads),
        ("--batch-size", form.eval_batch_size),
        ("--ubatch-size", form.ubatch_size),
        ("--seed", form.seed),
        ("--cache-type-k", form.k_cache_quant_type),
        ("--cache-type-v", form.v_cache_quant_type),
    ]
    # KV cache GPU offload command emission is intentionally deferred until the exact llama.cpp flag policy is chosen.
    for option, value in option_map:
        text = str(value).strip()
        if text:
            args.extend([option, quote_arg(text)])
    override_kv = _override_kv_value(form)
    if override_kv:
        args.extend(["--override-kv", quote_arg(override_kv)])
    spec_type = form.spec_type.strip()
    if spec_type:
        args.extend(["--spec-type", quote_arg(spec_type)])
    spec_map = [
        ("--spec-ngram-size-n", form.spec_ngram_size_n),
        ("--draft-min", form.draft_min),
        ("--draft-max", form.draft_max),
    ]
    for option, value in spec_map:
        text = str(value).strip()
        if text:
            args.extend([option, quote_arg(text)])
    custom = form.custom_args.strip()
    if custom:
        args.append(custom)
    return " ".join(args)


def format_command_for_yaml(command: str) -> str:
    tokens = split_command(command)
    if not tokens:
        return ""

    lines = [tokens[0]]
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if _is_option_token(token) and i + 1 < len(tokens) and not _is_option_token(tokens[i + 1]):
            lines.append(f"{token} {tokens[i + 1]}")
            i += 2
            continue
        lines.append(token)
        i += 1
    return "\n".join(lines)


def parse_command(model_id: str, command: str) -> ModelForm:
    tokens = [_clean_token(token) for token in split_command(command)]
    form = ModelForm(model_id=model_id)
    if tokens:
        form.llama_server_path = tokens[0]

    custom: list[str] = []
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in CACHE_TYPE_OPTIONS and i + 1 < len(tokens):
            value = tokens[i + 1]
            if value in KNOWN_CACHE_QUANT_TYPES:
                setattr(form, CACHE_TYPE_OPTIONS[token], value)
            else:
                custom.extend([token, quote_arg(value) if re.search(r"\s", value) else value])
            i += 2
            continue
        if token in VALUE_OPTIONS and i + 1 < len(tokens):
            setattr(form, VALUE_OPTIONS[token], tokens[i + 1])
            i += 2
            continue
        if token == "--override-kv" and i + 1 < len(tokens):
            _apply_override_kv(form, tokens[i + 1])
            i += 2
            continue
        if token == "--spec-type" and i + 1 < len(tokens):
            value = tokens[i + 1]
            if value in SPEC_TYPE_OPTIONS:
                form.spec_type = value
                i += 2
                continue
            custom.extend([token, quote_arg(value) if re.search(r"\s", value) else value])
            i += 2
            continue
        if token in IGNORED_VALUE_OPTIONS and i + 1 < len(tokens):
            i += 2
            continue
        custom.append(quote_arg(token) if re.search(r"\s", token) else token)
        i += 1
    form.custom_args = " ".join(custom)
    return form


def _is_option_token(token: str) -> bool:
    return token.startswith("-")


def _override_kv_value(form: ModelForm) -> str:
    entries = [entry for entry in _split_override_kv_entries(form.override_kv) if not _is_expert_used_count_override(entry)]
    expert_key = form.expert_used_count_key.strip()
    expert_count = form.expert_used_count.strip()
    if expert_key and expert_count:
        entries.append(f"{expert_key}=int:{expert_count}")
    return ",".join(entries)


def _apply_override_kv(form: ModelForm, value: str) -> None:
    passthrough_entries: list[str] = []
    for entry in _split_override_kv_entries(value):
        key, type_name, typed_value = _split_override_kv_entry(entry)
        if key.endswith(EXPERT_USED_COUNT_SUFFIX) and type_name == "int":
            form.expert_used_count_key = key
            form.expert_used_count = typed_value
            continue
        passthrough_entries.append(entry)
    form.override_kv = ",".join([*(_split_override_kv_entries(form.override_kv)), *passthrough_entries])


def _split_override_kv_entries(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _split_override_kv_entry(entry: str) -> tuple[str, str, str]:
    key, separator, typed_value = entry.partition("=")
    if not separator:
        return key, "", ""
    type_name, type_separator, value = typed_value.partition(":")
    if not type_separator:
        return key, "", typed_value
    return key, type_name, value


def _is_expert_used_count_override(entry: str) -> bool:
    key, type_name, _value = _split_override_kv_entry(entry)
    return key.endswith(EXPERT_USED_COUNT_SUFFIX) and type_name == "int"


def update_form_from_mapping(model_id: str, mapping: dict) -> ModelForm:
    form = parse_command(model_id, str(mapping.get("cmd", "") or ""))
    form.ttl = "" if mapping.get("ttl") is None else str(mapping.get("ttl"))
    aliases = mapping.get("aliases") or []
    if isinstance(aliases, str):
        form.aliases = [aliases]
    elif isinstance(aliases, Iterable):
        form.aliases = [str(item) for item in aliases]
    form.name = str(mapping.get("name", "") or "")
    return form


def form_to_plain_dict(form: ModelForm) -> dict:
    return asdict(form)
