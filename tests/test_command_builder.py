from command_builder import build_command, format_command_for_yaml, parse_command
from models import ModelForm


def test_build_command_keeps_port_and_omits_empty_values():
    form = ModelForm(
        model_id="m",
        llama_server_path="C:/Program Files/llama/llama-server.exe",
        model_path="D:/Models/My Model.gguf",
        context_length="4096",
        custom_args="--verbose",
    )

    cmd = build_command(form)

    assert '"C:/Program Files/llama/llama-server.exe"' in cmd
    assert '"D:/Models/My Model.gguf"' in cmd
    assert "--port ${PORT}" in cmd
    assert "--ctx-size 4096" in cmd
    assert "--threads" not in cmd
    assert cmd.endswith("--verbose")


def test_build_command_includes_mmproj_when_present():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="D:/Models/model.gguf",
        mmproj_path="D:/Models/vision projector.gguf",
    )

    cmd = build_command(form)

    assert '--mmproj "D:/Models/vision projector.gguf"' in cmd


def test_parse_command_extracts_known_args_and_keeps_unknown_custom_args():
    form = parse_command(
        "sample",
        'llama-server --port ${PORT} -lcd cache.bin --model "D:/Models/My Model.gguf" -c 8192 --n-gpu-layers 35 --foo bar',
    )

    assert form.llama_server_path == "llama-server"
    assert form.model_path == "D:/Models/My Model.gguf"
    assert form.context_length == "8192"
    assert form.gpu_offload_layers == "35"
    assert "-lcd cache.bin" in form.custom_args
    assert "--foo bar" in form.custom_args


def test_parse_command_extracts_mmproj_long_option():
    form = parse_command(
        "sample",
        'llama-server --model D:/Models/model.gguf --mmproj "D:/Models/mmproj.gguf"',
    )

    assert form.model_path == "D:/Models/model.gguf"
    assert form.mmproj_path == "D:/Models/mmproj.gguf"


def test_parse_command_extracts_mmproj_short_option():
    form = parse_command(
        "sample",
        'llama-server --model D:/Models/model.gguf -mm "D:/Models/mmproj.gguf"',
    )

    assert form.model_path == "D:/Models/model.gguf"
    assert form.mmproj_path == "D:/Models/mmproj.gguf"


def test_build_command_adds_optional_values_in_order():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="/models/a.gguf",
        mmproj_path="/models/mmproj.gguf",
        context_length="2048",
        gpu_offload_layers="0",
        cpu_threads="8",
        eval_batch_size="512",
        ubatch_size="256",
        seed="42",
        k_cache_quant_type="q8_0",
        v_cache_quant_type="q8_0",
    )

    assert build_command(form) == (
        "llama-server --model /models/a.gguf --port ${PORT} "
        "--mmproj /models/mmproj.gguf "
        "--ctx-size 2048 --n-gpu-layers 0 --threads 8 --batch-size 512 --ubatch-size 256 "
        "--seed 42 --cache-type-k q8_0 --cache-type-v q8_0"
    )


def test_parse_command_extracts_ubatch_size_long_and_short_options():
    long_form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --ubatch-size 256",
    )
    short_form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf -ub 128",
    )

    assert long_form.ubatch_size == "256"
    assert short_form.ubatch_size == "128"


def test_build_command_merges_expert_used_count_with_existing_override_kv():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="/models/a.gguf",
        override_kv="llama.rope.freq_base=float:1000000",
        expert_used_count_key="qwen3moe.expert_used_count",
        expert_used_count="8",
    )

    cmd = build_command(form)

    assert "--override-kv llama.rope.freq_base=float:1000000,qwen3moe.expert_used_count=int:8" in cmd


def test_parse_command_extracts_expert_used_count_and_preserves_other_override_kv():
    form = parse_command(
        "sample",
        (
            "llama-server --model D:/Models/model.gguf "
            "--override-kv llama.rope.freq_base=float:1000000,qwen3moe.expert_used_count=int:6"
        ),
    )

    assert form.override_kv == "llama.rope.freq_base=float:1000000"
    assert form.expert_used_count_key == "qwen3moe.expert_used_count"
    assert form.expert_used_count == "6"


def test_build_command_adds_ngram_speculative_decoding_options():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="/models/a.gguf",
        spec_type="ngram-map-k4v",
        spec_ngram_size_n="24",
        draft_min="48",
        draft_max="64",
    )

    assert build_command(form) == (
        "llama-server --model /models/a.gguf --port ${PORT} "
        "--spec-type ngram-map-k4v --spec-ngram-size-n 24 --draft-min 48 --draft-max 64"
    )


def test_parse_command_extracts_ngram_speculative_decoding_options():
    form = parse_command(
        "sample",
        (
            "llama-server --model D:/Models/model.gguf --spec-type ngram-mod "
            "--spec-ngram-size-n 24 --draft-min 48 --draft-max 64"
        ),
    )

    assert form.spec_type == "ngram-mod"
    assert form.spec_ngram_size_n == "24"
    assert form.draft_min == "48"
    assert form.draft_max == "64"
    assert "--spec-type" not in form.custom_args


def test_build_command_can_emit_spec_type_none():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="/models/a.gguf",
        spec_type="none",
    )

    assert build_command(form) == "llama-server --model /models/a.gguf --port ${PORT} --spec-type none"


def test_parse_command_accepts_draft_option_aliases_from_help():
    form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --draft 64 --draft-n-min 48",
    )

    assert form.draft_max == "64"
    assert form.draft_min == "48"


def test_parse_command_extracts_known_cache_types_without_custom_args():
    form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --cache-type-k q8_0 --cache-type-v f16",
    )

    assert form.k_cache_quant_type == "q8_0"
    assert form.v_cache_quant_type == "f16"
    assert "--cache-type-k" not in form.custom_args
    assert "--cache-type-v" not in form.custom_args


def test_parse_command_keeps_unknown_cache_types_in_custom_args():
    form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --cache-type-k q6_k --cache-type-v q4_2",
    )

    assert form.k_cache_quant_type == ""
    assert form.v_cache_quant_type == ""
    assert "--cache-type-k q6_k" in form.custom_args
    assert "--cache-type-v q4_2" in form.custom_args


def test_parse_command_supports_mixed_known_and_unknown_cache_types():
    form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --cache-type-k q8_0 --cache-type-v q4_2",
    )

    assert form.k_cache_quant_type == "q8_0"
    assert form.v_cache_quant_type == ""
    assert "--cache-type-k" not in form.custom_args
    assert "--cache-type-v q4_2" in form.custom_args


def test_build_command_round_trips_unknown_cache_types_via_custom_args():
    form = parse_command(
        "sample",
        "llama-server --model D:/Models/model.gguf --cache-type-k q6_k --threads 8",
    )

    rebuilt = build_command(form)

    assert "--cache-type-k q6_k" in rebuilt
    assert "--threads 8" in rebuilt
    assert form.k_cache_quant_type == ""


def test_format_command_for_yaml_puts_options_on_separate_lines():
    command = (
        'llama-server --model "D:/Models/My Model.gguf" --port ${PORT} '
        "--ctx-size 4096 -lcd sample_cache.bin --verbose"
    )

    assert format_command_for_yaml(command) == (
        "llama-server\n"
        '--model "D:/Models/My Model.gguf"\n'
        "--port ${PORT}\n"
        "--ctx-size 4096\n"
        "-lcd sample_cache.bin\n"
        "--verbose"
    )
