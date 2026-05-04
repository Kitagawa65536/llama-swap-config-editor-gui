from __future__ import annotations

import flet as ft

from command_builder import update_form_from_mapping


def build_models(app) -> ft.Control:
    items = app.store.model_items(app.state.data) if app.state.data is not None else []
    cards = []
    for model_id, model_data in items:
        form = update_form_from_mapping(model_id, model_data)
        subtitle = form.name or ", ".join(form.aliases) or "-"
        model_path = form.model_path or "(model path unknown)"
        cards.append(
            ft.Container(
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=6,
                on_click=lambda e, mid=model_id: app.select_model(mid),
                bgcolor=ft.Colors.SECONDARY_CONTAINER if app.selected_model_id == model_id else None,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(model_id, weight=ft.FontWeight.BOLD),
                        ft.Text(subtitle, size=12),
                        ft.Text(model_path, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"ttl: {form.ttl or '-'}", size=11),
                    ],
                ),
            )
        )

    left = ft.Container(
        width=330,
        padding=10,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Models", size=20, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD, tooltip="空のモデルを追加", on_click=app.add_empty_model),
                    ],
                ),
                ft.Column(controls=cards or [ft.Text("モデルがありません / No models")], scroll=ft.ScrollMode.AUTO, expand=True),
            ],
        ),
    )

    right = _model_form(app) if app.current_model_form else ft.Container(expand=True, padding=16, content=ft.Text("左のモデルを選択してください / Select a model"))
    return ft.Row(expand=True, controls=[left, ft.VerticalDivider(width=1), right])


def _field(label: str, value: str, on_change, password: bool = False) -> ft.TextField:
    return ft.TextField(label=label, value=value, on_change=on_change, password=password, dense=True)


def _model_form(app) -> ft.Control:
    f = app.current_model_form

    def set_attr(name):
        return lambda e: setattr(f, name, e.control.value)

    def set_aliases(e):
        f.aliases = [part.strip() for part in e.control.value.split(",") if part.strip()]

    def set_kv(e):
        value = e.control.value
        f.kv_cache_gpu_offload = True if value == "on" else False if value == "off" else None

    return ft.Container(
        expand=True,
        padding=16,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("モデル編集 / Model editor", size=22, weight=ft.FontWeight.BOLD),
                _field("model_id", f.model_id, set_attr("model_id")),
                _field("name", f.name, set_attr("name")),
                _field("llama-server path", f.llama_server_path, set_attr("llama_server_path")),
                _field("GGUF model path", f.model_path, set_attr("model_path")),
                ft.Row(
                    controls=[
                        _field("context length", f.context_length, set_attr("context_length")),
                        _field("GPU offload layers", f.gpu_offload_layers, set_attr("gpu_offload_layers")),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("CPU threads", f.cpu_threads, set_attr("cpu_threads")),
                        _field("eval batch size", f.eval_batch_size, set_attr("eval_batch_size")),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("seed", f.seed, set_attr("seed")),
                        ft.Dropdown(
                            label="KV cache GPU offload",
                            value="on" if f.kv_cache_gpu_offload is True else "off" if f.kv_cache_gpu_offload is False else "unset",
                            options=[
                                ft.dropdown.Option("unset", "未指定 / Unset"),
                                ft.dropdown.Option("on", "ON"),
                                ft.dropdown.Option("off", "OFF"),
                            ],
                            on_select=set_kv,
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("K cache quantization type", f.k_cache_quant_type, set_attr("k_cache_quant_type")),
                        _field("V cache quantization type", f.v_cache_quant_type, set_attr("v_cache_quant_type")),
                    ]
                ),
                _field("ttl", f.ttl, set_attr("ttl")),
                _field("aliases (comma separated)", ", ".join(f.aliases), set_aliases),
                ft.TextField(label="custom args", value=f.custom_args, min_lines=3, max_lines=5, on_change=set_attr("custom_args")),
                ft.Row(
                    controls=[
                        ft.Button("フォームを反映 / Apply form", on_click=app.apply_current_model),
                        ft.OutlinedButton("cmdプレビュー / Preview cmd", on_click=app.preview_current_cmd),
                    ]
                ),
            ],
        ),
    )
