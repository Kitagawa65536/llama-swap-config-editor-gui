from gguf_importer import _first_context_length, normalize_context_length


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
