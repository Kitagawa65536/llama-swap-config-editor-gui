# llama-swap Config Editor GUI

[English](README.md) | [日本語](README_jp.md)

This is a Flet desktop GUI for safely editing `llama-swap` `config.yaml` files. It does not start, stop, or monitor llama-swap itself, llama.cpp, or llama-server.

## Features

- Read, edit, and save `config.yaml`
- Save-time validation via `config-schema.json`
- Create a `.bak` backup before saving
- Model editing centered on `models.<model_id>.cmd`
- Generate model addition candidates from GGUF metadata (multiple GGUF files at once)
- Model search and filtering by model_id
- Raw YAML editor
- Global settings editing
- Raw views for Macros / Matrix / Groups / Hooks / Peers
- Create new config.yaml
- Recent config/schema history
- UI language switching (Japanese / English)

## Model Editing Features

### Basic Settings

- llama-server path selection (file picker dialog)
- Model path selection (GGUF file picker)
- mmproj path selection (multimodal projector GGUF file picker)
- Context length (slider input, synced with GGUF max value)
- GPU offload layers
- CPU threads
- Batch size / Ubatch size
- Seed

### KV Cache

- KV cache GPU offload toggle
- K/V cache quantization type selection (f32, f16, bf16, q8_0, q4_0, q4_1, iq4_nl, q5_0, q5_1)

### Advanced Settings

- Override KV configuration (manual input field)
- expert_used_count configuration (auto-detected from GGUF or manual input)
- Speculative decoding (n-gram) settings
  - spec-type selection (none, ngram-cache, ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod)
  - spec-ngram-size-n, draft-min, draft-max
- GGUF metadata viewer
- GGUF header auto-load (context length, expert_used_count, etc.)

### Model Management

- Add models (empty model / from GGUF)
- Delete models
- Model search (debounced real-time filter by model_id)
- TTL / Aliases / Name configuration
- Command preview

## Important Notes

- llama-server-specific arguments are not stored as separate fields in the llama-swap schema; they are eventually merged into the `cmd` string.
- Full reverse parsing of an existing `cmd` is not guaranteed. Unrecognized arguments are preserved as `custom args`.
- Custom keys are not saved to `config.yaml`.
- Existing YAML comments, ordering, unknown keys, and unsupported settings are preserved as much as possible with `ruamel.yaml`.
- A `config.yaml.bak` or `config.yaml.<timestamp>.bak` backup is created before saving.
- Values read from GGUF metadata are estimates. Please confirm them before saving.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe main.py
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Command Generation

Base form:

```text
<llama_server_path> --model <model_path> --port ${PORT}
```

The following options are added only when they are present:

- `--mmproj`
- `--ctx-size`
- `--n-gpu-layers`
- `--threads`
- `--batch-size`
- `--ubatch-size`
- `--seed`
- `--cache-type-k`
- `--cache-type-v`

When override KV is set, `--override-kv` is added. The expert_used_count value is integrated into `--override-kv` as `key.expert_used_count=int:N`.

When speculative decoding is enabled, the following are added:

- `--spec-type`
- `--spec-ngram-size-n`
- `--draft-min`
- `--draft-max`

`custom args` are appended at the end. `${PORT}` is always preserved.

## License

MIT License — see LICENSE.txt.
