# llama-swap Config Editor GUI

llama-swap `config.yaml` を安全に編集するための最小FletデスクトップGUIです。llama-swap本体、llama.cpp、llama-server の起動・停止・監視は行いません。

## Features

- `config.yaml` の読込、編集、保存
- `config-schema.json` による保存前 validation
- 保存前の `.bak` バックアップ作成
- `models.<model_id>.cmd` 中心のモデル編集
- GGUF metadata からのモデル追加候補作成
- Raw YAML Editor
- Global Settings の最小編集
- Macros / Matrix / Groups / Hooks / Peers のRaw表示

## Important Notes

- llama-server の個別引数は llama-swap schema 上の独立フィールドとして保存せず、最終的に `cmd` 文字列へ合成します。
- 既存 `cmd` の完全な逆パースは保証しません。認識できない引数は `custom args` として残します。
- 独自キーは `config.yaml` に保存しません。
- 既存YAMLのコメント、順序、未知キー、未対応設定は `ruamel.yaml` で可能な限り保持します。
- 保存前に `config.yaml.bak` または `config.yaml.<timestamp>.bak` を作成します。
- GGUF metadata から読んだ値は推定です。保存前に必ずユーザーが確認してください。

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

基本形:

```text
<llama_server_path> --model <model_path> --port ${PORT}
```

入力されている場合のみ以下を追加します。

- `--ctx-size`
- `--n-gpu-layers`
- `--threads`
- `--batch-size`
- `--seed`
- `--cache-type-k`
- `--cache-type-v`

`custom args` は最後に追加されます。`${PORT}` は必ず保持します。

KV cache GPU offload OFF は初期実装では `cmd` へ自動出力しません。必要な llama.cpp オプションを `custom args` に手動指定してください。
