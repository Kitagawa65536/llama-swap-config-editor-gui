# llama-swap Config Editor GUI

[English](README.md) | [日本語](README_jp.md)

This is a minimal Flet desktop GUI for safely editing `llama-swap` `config.yaml` files. It does not start, stop, or monitor llama-swap itself, llama.cpp, or llama-server.

## Features

- Read, edit, and save `config.yaml`
- Save-time validation via `config-schema.json`
- Create a `.bak` backup before saving
- Model editing centered on `models.<model_id>.cmd`
- Generate model addition candidates from GGUF metadata
- Raw YAML editor
- Minimal editing for global settings
- Raw views for Macros / Matrix / Groups / Hooks / Peers

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

- `--ctx-size`
- `--n-gpu-layers`
- `--threads`
- `--batch-size`
- `--seed`
- `--cache-type-k`
- `--cache-type-v`

`custom args` are appended at the end. `${PORT}` is always preserved.

KV cache GPU offload OFF is not emitted automatically into `cmd` in the initial implementation. Add the required llama.cpp options manually in `custom args`.
