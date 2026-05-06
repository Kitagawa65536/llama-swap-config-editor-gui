from __future__ import annotations

from dataclasses import dataclass


DEFAULT_RUNTIME_ID = "llama.cpp"


@dataclass(frozen=True)
class RuntimeProfile:
    runtime_id: str
    label: str
    default_command: str
    runtime_path_label_key: str
    model_path_label_key: str


RUNTIME_PROFILES = (
    RuntimeProfile(
        runtime_id=DEFAULT_RUNTIME_ID,
        label="llama.cpp",
        default_command="llama-server",
        runtime_path_label_key="models.runtime_path.llama_cpp",
        model_path_label_key="models.model_path.gguf",
    ),
)

RUNTIME_PROFILE_BY_ID = {profile.runtime_id: profile for profile in RUNTIME_PROFILES}


def normalize_runtime_id(value: str | None) -> str:
    runtime_id = str(value or "").strip()
    return runtime_id if runtime_id in RUNTIME_PROFILE_BY_ID else DEFAULT_RUNTIME_ID


def runtime_profile(value: str | None) -> RuntimeProfile:
    return RUNTIME_PROFILE_BY_ID[normalize_runtime_id(value)]
