from __future__ import annotations

import flet as ft


def build_raw_yaml(app) -> ft.Control:
    if app.raw_editor is None:
        app.raw_editor = ft.TextField(
            value=app.state.raw_yaml,
            multiline=True,
            min_lines=26,
            expand=True,
            on_change=app.on_raw_changed,
            text_size=13,
        )
    app.raw_editor.value = app.state.raw_yaml
    return ft.Column(
        expand=True,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(app.t("raw.title"), size=24, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(app.t("raw.apply"), on_click=app.apply_raw_yaml),
                            ft.Button(app.t("raw.save"), on_click=app.save_config),
                        ]
                    ),
                ],
            ),
            app.raw_editor,
        ],
    )
