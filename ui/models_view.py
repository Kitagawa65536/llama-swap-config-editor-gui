from __future__ import annotations

import flet as ft

from command_builder import KNOWN_CACHE_QUANT_TYPES


def build_models(app) -> ft.Control:
    cards = build_model_cards(app)
    app.model_list_column = ft.Column(controls=cards, scroll=ft.ScrollMode.AUTO, expand=True)

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
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    tooltip="選択中モデルを削除",
                                    on_click=app.delete_current_model,
                                    disabled=app.selected_model_id is None,
                                ),
                                ft.IconButton(ft.Icons.ADD, tooltip="空のモデルを追加", on_click=app.add_empty_model),
                            ],
                        ),
                    ],
                ),
                ft.TextField(
                    label="model_id で検索 / Search by model_id",
                    value=app.model_search_term,
                    prefix_icon=ft.Icons.SEARCH,
                    hint_text="例: qwen, mistral, vision",
                    dense=True,
                    on_change=app.on_model_search_change,
                ),
                app.model_list_column,
            ],
        ),
    )

    right = _model_form(app) if app.current_model_form else ft.Container(expand=True, padding=16, content=ft.Text("左のモデルを選択してください / Select a model"))
    return ft.Row(expand=True, controls=[left, ft.VerticalDivider(width=1), right])


def build_model_cards(app) -> list[ft.Control]:
    items = app.model_list_items()
    cards = []
    for item in items:
        cards.append(
            ft.Container(
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=6,
                on_click=lambda e, mid=item.model_id: app.select_model(mid),
                bgcolor=ft.Colors.SECONDARY_CONTAINER if app.selected_model_id == item.model_id else None,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(item.model_id, weight=ft.FontWeight.BOLD),
                        ft.Text(item.subtitle, size=12),
                        ft.Text(item.model_path, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"ttl: {item.ttl}", size=11),
                    ],
                ),
            )
        )
    if cards:
        return cards
    if app.model_search_term:
        return [ft.Text("該当するモデルがありません / No matching models")]
    return [ft.Text("モデルがありません / No models")]


def _field(label: str, value: str, on_change, password: bool = False, expand: bool | int | None = None) -> ft.TextField:
    return ft.TextField(label=label, value=value, on_change=on_change, password=password, dense=True, expand=expand)


def _cache_dropdown(label: str, value: str, on_change) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        value=value or "",
        options=[
            ft.dropdown.Option("", "未指定 / Clear"),
            *[ft.dropdown.Option(option, option) for option in KNOWN_CACHE_QUANT_TYPES],
        ],
        on_select=on_change,
        expand=True,
    )


def _model_form(app) -> ft.Control:
    f = app.current_model_form

    def set_attr(name):
        return lambda e: setattr(f, name, e.control.value)

    def set_aliases(e):
        f.aliases = [part.strip() for part in e.control.value.split(",") if part.strip()]

    def set_kv(e):
        value = e.control.value
        f.kv_cache_gpu_offload = True if value == "on" else False if value == "off" else None

    advanced_section = ft.Column(
        visible=False,
        controls=[
            ft.TextField(
                label="advanced dummy input",
                hint_text="本実装時に削除予定 / Placeholder for future advanced settings",
                dense=True,
            )
        ],
    )

    def toggle_advanced(_e):
        advanced_section.visible = not advanced_section.visible
        advanced_section.update()

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
                ft.Row(
                    controls=[
                        _field("llama-server path", f.llama_server_path, set_attr("llama_server_path"), expand=True),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="Browse llama-server",
                            on_click=lambda _e: app.page.run_task(app.pick_llama_server),
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("GGUF model path", f.model_path, set_attr("model_path"), expand=True),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="Browse GGUF",
                            on_click=lambda _e: app.page.run_task(app.pick_model_path),
                        ),
                        ft.OutlinedButton(
                            "GGUFヘッダ読込 / Read GGUF header",
                            icon=ft.Icons.DATA_OBJECT,
                            on_click=app.load_current_model_gguf_header,
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("mmproj path", f.mmproj_path, set_attr("mmproj_path"), expand=True),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="Browse mmproj GGUF",
                            on_click=lambda _e: app.page.run_task(app.pick_mmproj_path),
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _context_length_control(f),
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
                        _field("ubatch size", f.ubatch_size, set_attr("ubatch_size")),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field("seed", f.seed, set_attr("seed")),
                        # KV cache GPU offload is captured in the form but command emission is intentionally deferred.
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
                        _cache_dropdown("K cache type", f.k_cache_quant_type, set_attr("k_cache_quant_type")),
                        _cache_dropdown("V cache type", f.v_cache_quant_type, set_attr("v_cache_quant_type")),
                    ]
                ),
                _field("ttl", f.ttl, set_attr("ttl")),
                _field("aliases (comma separated)", ", ".join(f.aliases), set_aliases),
                ft.TextField(label="custom args", value=f.custom_args, min_lines=3, max_lines=5, on_change=set_attr("custom_args")),
                ft.OutlinedButton("Advanced settings / advance", icon=ft.Icons.TUNE, on_click=toggle_advanced),
                advanced_section,
                ft.Row(
                    controls=[
                        ft.Button("フォームを反映 / Apply form", on_click=app.apply_current_model),
                        ft.OutlinedButton("cmdプレビュー / Preview cmd", on_click=app.preview_current_cmd),
                    ]
                ),
            ],
        ),
    )


def _context_length_control(f) -> ft.Control:
    if not f.context_length_max:
        return _field("context length", f.context_length, lambda e: setattr(f, "context_length", e.control.value))

    limit = f.context_length_max
    slider_value = _slider_context_value(f.context_length, limit)

    def on_text_change(e):
        value = e.control.value.strip()
        if not value:
            f.context_length = ""
            return
        try:
            numeric_value = int(value)
        except ValueError:
            f.context_length = value
            return
        numeric_value = max(1, min(numeric_value, limit))
        f.context_length = str(numeric_value)
        context_field.value = f.context_length
        context_slider.value = numeric_value
        context_field.update()
        context_slider.update()

    def on_slider_change(e):
        numeric_value = int(e.control.value)
        f.context_length = str(numeric_value)
        context_field.value = f.context_length
        context_field.update()

    context_field = ft.TextField(
        label=f"context length (max {limit})",
        value=f.context_length,
        on_change=on_text_change,
        dense=True,
        width=190,
    )
    context_slider = ft.Slider(
        min=1,
        max=limit,
        value=slider_value,
        round=0,
        label="{value}",
        on_change=on_slider_change,
        expand=True,
    )
    return ft.Column(
        expand=True,
        spacing=2,
        controls=[
            context_field,
            context_slider,
        ],
    )


def _slider_context_value(value: str, limit: int) -> int:
    try:
        numeric_value = int(str(value).strip())
    except ValueError:
        return min(1, limit)
    return max(1, min(numeric_value, limit))
