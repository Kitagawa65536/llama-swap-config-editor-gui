from __future__ import annotations

import flet as ft

from command_builder import KNOWN_CACHE_QUANT_TYPES, SPEC_TYPE_OPTIONS
from runtime_profiles import RUNTIME_PROFILES, runtime_profile


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
                        ft.Text(app.t("models.title"), size=20, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    tooltip=app.t("models.delete_selected.tooltip"),
                                    on_click=app.delete_current_model,
                                    disabled=app.selected_model_id is None,
                                ),
                                ft.IconButton(ft.Icons.ADD, tooltip=app.t("models.add_empty.tooltip"), on_click=app.add_empty_model),
                            ],
                        ),
                    ],
                ),
                ft.TextField(
                    label=app.t("models.search_label"),
                    value=app.model_search_term,
                    prefix_icon=ft.Icons.SEARCH,
                    hint_text=app.t("models.search_hint"),
                    dense=True,
                    on_change=app.on_model_search_change,
                ),
                app.model_list_column,
            ],
        ),
    )

    right = _model_form(app) if app.current_model_form else ft.Container(expand=True, padding=16, content=ft.Text(app.t("models.select_prompt")))
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
                        ft.Text(f"runtime: {item.runtime_id} / ttl: {item.ttl}", size=11),
                    ],
                ),
            )
        )
    if cards:
        return cards
    if app.model_search_term:
        return [ft.Text(app.t("models.no_matching"))]
    return [ft.Text(app.t("models.no_models"))]


def _field(label: str, value: str, on_change, password: bool = False, expand: bool | int | None = None) -> ft.TextField:
    return ft.TextField(label=label, value=value, on_change=on_change, password=password, dense=True, expand=expand)


def _cache_dropdown(app, label: str, value: str, on_change) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        value=value or "",
        options=[
            ft.dropdown.Option("", app.t("models.clear")),
            *[ft.dropdown.Option(option, option) for option in KNOWN_CACHE_QUANT_TYPES],
        ],
        on_select=on_change,
        expand=True,
    )


def _spec_type_dropdown(app, value: str, on_change) -> ft.Dropdown:
    return ft.Dropdown(
        label="spec type",
        value=value or "",
        options=[
            ft.dropdown.Option("", app.t("models.clear")),
            *[ft.dropdown.Option(option, option) for option in SPEC_TYPE_OPTIONS],
        ],
        on_select=on_change,
        expand=True,
    )


def _model_form(app) -> ft.Control:
    f = app.current_model_form
    profile = runtime_profile(f.runtime_id)

    def set_attr(name):
        return lambda e: setattr(f, name, e.control.value)

    def set_aliases(e):
        f.aliases = [part.strip() for part in e.control.value.split(",") if part.strip()]

    def set_kv(e):
        value = e.control.value
        f.kv_cache_gpu_offload = True if value == "on" else False if value == "off" else None

    def set_runtime(e):
        f.runtime_id = e.control.value

    advanced_section = ft.Column(
        visible=False,
        controls=[
            ft.Text(app.t("models.advanced.title"), weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.OutlinedButton(
                        app.t("models.advanced.show_metadata"),
                        icon=ft.Icons.DATA_OBJECT,
                        on_click=app.show_current_model_metadata,
                        disabled=not bool(f.gguf_metadata),
                    ),
                ]
            ),
            _expert_used_count_control(f, set_attr("expert_used_count"), app),
            ft.Divider(),
            ft.Text("n-gram speculative decoding", weight=ft.FontWeight.BOLD),
            ft.Text(
                app.t("models.advanced.description"),
                size=12,
            ),
            _spec_type_dropdown(app, f.spec_type, set_attr("spec_type")),
            ft.Row(
                controls=[
                    _field("spec ngram size n", f.spec_ngram_size_n, set_attr("spec_ngram_size_n")),
                    _field("draft min", f.draft_min, set_attr("draft_min")),
                    _field("draft max", f.draft_max, set_attr("draft_max")),
                ]
            ),
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
                ft.Text(app.t("models.editor_title"), size=22, weight=ft.FontWeight.BOLD),
                _field("model_id", f.model_id, set_attr("model_id")),
                _field("name", f.name, set_attr("name")),
                ft.Dropdown(
                    label=app.t("models.runtime"),
                    value=f.runtime_id,
                    options=[ft.dropdown.Option(profile.runtime_id, profile.label) for profile in RUNTIME_PROFILES],
                    on_select=set_runtime,
                    dense=True,
                ),
                ft.Row(
                    controls=[
                        _field(app.t(profile.runtime_path_label_key), f.llama_server_path, set_attr("llama_server_path"), expand=True),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip=app.t("models.runtime_path.browse"),
                            on_click=lambda _e: app.page.run_task(app.pick_llama_server),
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _field(app.t(profile.model_path_label_key), f.model_path, set_attr("model_path"), expand=True),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="Browse GGUF",
                            on_click=lambda _e: app.page.run_task(app.pick_model_path),
                        ),
                        ft.OutlinedButton(
                            app.t("models.read_gguf_header"),
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
                                ft.dropdown.Option("unset", app.t("models.unset")),
                                ft.dropdown.Option("on", "ON"),
                                ft.dropdown.Option("off", "OFF"),
                            ],
                            on_select=set_kv,
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        _cache_dropdown(app, "K cache type", f.k_cache_quant_type, set_attr("k_cache_quant_type")),
                        _cache_dropdown(app, "V cache type", f.v_cache_quant_type, set_attr("v_cache_quant_type")),
                    ]
                ),
                _field("ttl", f.ttl, set_attr("ttl")),
                _field("aliases (comma separated)", ", ".join(f.aliases), set_aliases),
                ft.TextField(label="custom args", value=f.custom_args, min_lines=3, max_lines=5, on_change=set_attr("custom_args")),
                ft.OutlinedButton(app.t("models.advanced.toggle"), icon=ft.Icons.TUNE, on_click=toggle_advanced),
                advanced_section,
                ft.Row(
                    controls=[
                        ft.Button(app.t("models.apply_form"), on_click=app.apply_current_model),
                        ft.OutlinedButton(app.t("models.preview_cmd"), on_click=app.preview_current_cmd),
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


def _expert_used_count_control(f, on_change, app=None) -> ft.Control:
    if not f.expert_used_count_key:
        return ft.Text(
            app.t("models.advanced.moe_not_detected") if app else "No MoE expert_used_count detected yet",
            size=12,
        )

    source = f"detected: {f.expert_used_count_source}" if f.expert_used_count_source else "override value"
    return ft.Column(
        spacing=4,
        controls=[
            ft.Text("MoE expert_used_count override", weight=ft.FontWeight.BOLD),
            ft.Text(f"key: {f.expert_used_count_key}", size=12),
            ft.TextField(
                label="expert_used_count",
                value=f.expert_used_count,
                hint_text=source,
                on_change=on_change,
                dense=True,
            ),
            ft.Text(
                app.t("models.advanced.override_description") if app else "Emits --override-kv key.expert_used_count=int:N",
                size=12,
            ),
        ],
    )


def _slider_context_value(value: str, limit: int) -> int:
    try:
        numeric_value = int(str(value).strip())
    except ValueError:
        return min(1, limit)
    return max(1, min(numeric_value, limit))
