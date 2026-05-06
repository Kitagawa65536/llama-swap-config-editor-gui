from gguf_importer import _first_context_length, expert_used_count_metadata, format_metadata_text, normalize_context_length


def test_normalize_context_length_accepts_common_scalar_values():
    assert normalize_context_length(4096) == 4096
    assert normalize_context_length("8192") == 8192
    assert normalize_context_length(b"16384") == 16384
    assert normalize_context_length([32768]) == 32768


def test_normalize_context_length_rejects_empty_invalid_and_non_positive_values():
    assert normalize_context_length(None) is None
    assert normalize_context_length("") is None
    assert normalize_context_length("not-a-number") is None
    assert normalize_context_length(0) is None
    assert normalize_context_length(-1) is None
    assert normalize_context_length([]) is None
    assert normalize_context_length([4096, 8192]) is None


def test_first_context_length_uses_architecture_specific_key():
    metadata = {
        "general.architecture": "qwen35",
        "qwen35.context_length": 40960,
    }

    assert _first_context_length(metadata, ["llama.context_length", "general.context_length"]) == 40960


def test_expert_used_count_metadata_detects_moe_key():
    metadata = {
        "general.architecture": "qwen3moe",
        "qwen3moe.expert_used_count": 8,
    }

    assert expert_used_count_metadata(metadata) == ("qwen3moe.expert_used_count", "8")


def test_format_metadata_text_sorts_and_renders_values():
    metadata = {
        "z.key": [1, 2],
        "a.key": b"value",
    }

    assert format_metadata_text(metadata) == "a.key: value\nz.key: [1, 2]"
