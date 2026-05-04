from __future__ import annotations

import re
import shlex
from dataclasses import asdict
from typing import Iterable

from models import ModelForm


VALUE_OPTIONS = {
    "--model": "model_path",
    "-m": "model_path",
    "--ctx-size": "context_length",
    "-c": "context_length",
    "--n-gpu-layers": "gpu_offload_layers",
    "-ngl": "gpu_offload_layers",
    "--threads": "cpu_threads",
    "-t": "cpu_threads",
    "--batch-size": "eval_batch_size",
    "-b": "eval_batch_size",
    "--seed": "seed",
    "--cache-type-k": "k_cache_quant_type",
    "--cache-type-v": "v_cache_quant_type",
}

IGNORED_VALUE_OPTIONS = {"--port"}


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
        ("--ctx-size", form.context_length),
        ("--n-gpu-layers", form.gpu_offload_layers),
        ("--threads", form.cpu_threads),
        ("--batch-size", form.eval_batch_size),
        ("--seed", form.seed),
        ("--cache-type-k", form.k_cache_quant_type),
        ("--cache-type-v", form.v_cache_quant_type),
    ]
    # KV cache GPU offload command emission is intentionally deferred until the exact llama.cpp flag policy is chosen.
    for option, value in option_map:
        text = str(value).strip()
        if text:
            args.extend([option, quote_arg(text)])
    custom = form.custom_args.strip()
    if custom:
        args.append(custom)
    return " ".join(args)


def parse_command(model_id: str, command: str) -> ModelForm:
    tokens = [_clean_token(token) for token in split_command(command)]
    form = ModelForm(model_id=model_id)
    if tokens:
        form.llama_server_path = tokens[0]

    custom: list[str] = []
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in VALUE_OPTIONS and i + 1 < len(tokens):
            setattr(form, VALUE_OPTIONS[token], tokens[i + 1])
            i += 2
            continue
        if token in IGNORED_VALUE_OPTIONS and i + 1 < len(tokens):
            i += 2
            continue
        custom.append(quote_arg(token) if re.search(r"\s", token) else token)
        i += 1
    form.custom_args = " ".join(custom)
    return form


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
