from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelForm:
    model_id: str
    llama_server_path: str = ""
    model_path: str = ""
    mmproj_path: str = ""
    context_length: str = ""
    context_length_max: int | None = None
    gpu_offload_layers: str = ""
    cpu_threads: str = ""
    eval_batch_size: str = ""
    ubatch_size: str = ""
    kv_cache_gpu_offload: bool | None = None
    seed: str = ""
    k_cache_quant_type: str = ""
    v_cache_quant_type: str = ""
    override_kv: str = ""
    expert_used_count_key: str = ""
    expert_used_count: str = ""
    expert_used_count_source: str = ""
    spec_type: str = ""
    spec_ngram_size_n: str = ""
    draft_min: str = ""
    draft_max: str = ""
    ttl: str = ""
    aliases: list[str] = field(default_factory=list)
    name: str = ""
    custom_args: str = ""
    gguf_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelListItem:
    model_id: str
    subtitle: str
    model_path: str
    ttl: str


@dataclass
class GlobalSettingsForm:
    health_check_timeout: str = ""
    log_level: str = ""
    start_port: str = ""
    global_ttl: str = ""
    send_loading_state: bool | None = None


@dataclass
class AdvancedSection:
    key: str
    yaml_fragment: str


@dataclass
class ConfigState:
    path: Path | None = None
    schema_path: Path | None = None
    data: Any = None
    raw_yaml: str = ""
    dirty: bool = False
    validation_message: str = "未検証 / Not validated"
    last_message: str = ""


@dataclass
class GgufImportSuggestion:
    model_id: str
    name: str
    model_path: str
    context_length: str = ""
    context_length_max: int | None = None
    gpu_offload_layers: str = ""
    cpu_threads: str = ""
    eval_batch_size: str = ""
    ubatch_size: str = ""
    seed: str = ""
    k_cache_quant_type: str = ""
    v_cache_quant_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
