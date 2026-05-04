from command_builder import build_command, parse_command
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


def test_build_command_adds_optional_values_in_order():
    form = ModelForm(
        model_id="m",
        llama_server_path="llama-server",
        model_path="/models/a.gguf",
        context_length="2048",
        gpu_offload_layers="0",
        cpu_threads="8",
        eval_batch_size="512",
        seed="42",
        k_cache_quant_type="q8_0",
        v_cache_quant_type="q8_0",
    )

    assert build_command(form) == (
        "llama-server --model /models/a.gguf --port ${PORT} "
        "--ctx-size 2048 --n-gpu-layers 0 --threads 8 --batch-size 512 "
        "--seed 42 --cache-type-k q8_0 --cache-type-v q8_0"
    )
