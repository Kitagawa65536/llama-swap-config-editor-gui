# llama-swap Config Editor GUI

[English](README.md) | [日本語](README_jp.md)

llama-swap `config.yaml` を安全に編集するための Flet デスクトップGUIです。llama-swap本体、llama.cpp、llama-server の起動・停止・監視は行いません。

## Features

- `config.yaml` の読込、編集、保存
- `config-schema.json` による保存前 validation
- 保存前の `.bak` バックアップ作成
- `models.<model_id>.cmd` 中心のモデル編集
- GGUF metadata からのモデル追加候補作成（複数 GGUF 同時追加対応）
- model_id でのモデル検索・フィルタ
- Raw YAML Editor
- Global Settings の編集
- Macros / Matrix / Groups / Hooks / Peers の Raw 表示
- 新規 config.yaml の作成
- 最近開いた config/schema の履歴管理
- UI 表示言語の切替（日本語 / English）

## モデル編集機能

### 基本設定

- llama-server パスの指定（ファイル選択ダイアログ対応）
- Model path の指定（GGUF ファイル選択対応）
- mmproj path の指定（マルチモーダル投影モデル用 GGUF 選択対応）
- Context length（スライダー入力、GGUF 最大値連携）
- GPU offload layers
- CPU threads
- Batch size / Ubatch size
- Seed

### KV Cache

- KV cache GPU offload の切替
- K/V cache quantization type の選択（f32, f16, bf16, q8_0, q4_0, q4_1, iq4_nl, q5_0, q5_1）

### Advanced Settings

- Override KV 設定（手動入力欄）
- expert_used_count 設定（GGUF から自動検出、または手動入力）
- Speulative decoding（n-gram）設定
  - spec-type の選択（none, ngram-cache, ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod）
  - spec-ngram-size-n, draft-min, draft-max
- GGUF メタデータの表示
- GGUF ヘッダ読込による自動設定（Context 長、expert_used_count など）

### モデル管理

- モデルの追加（空のモデル / GGUF から）
- モデルの削除
- model_id の検索（デバウンス付きリアルタイムフィルタ）
- TTL / Aliases / Name の設定
- cmd のプレビュー

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

- `--mmproj`
- `--ctx-size`
- `--n-gpu-layers`
- `--threads`
- `--batch-size`
- `--ubatch-size`
- `--seed`
- `--cache-type-k`
- `--cache-type-v`

Override KV が入力されている場合は `--override-kv` を追加します。expert_used_count 設定値は `--override-kv` に `key.expert_used_count=int:N` として統合されます。

Speculative decoding が有効な場合は以下を追加します。

- `--spec-type`
- `--spec-ngram-size-n`
- `--draft-min`
- `--draft-max`

`custom args` は最後に追加されます。`${PORT}` は必ず保持します。

## License

MIT License — LICENSE.txt を参照してください。
