from __future__ import annotations

import flet as ft


def build_home(app) -> ft.Control:
    recent = [
        ft.ListTile(title=ft.Text(path), on_click=lambda e, p=path: app.open_config(p))
        for path in app.settings.recent_configs
    ]
    if not recent:
        recent = [ft.Text("最近開いたconfigはありません / No recent configs")]

    return ft.Column(
        expand=True,
        spacing=16,
        controls=[
            ft.Text("Home", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                wrap=True,
                controls=[
                    ft.Button("config.yaml を開く / Open config", on_click=app.pick_config),
                    ft.OutlinedButton("config-schema.json を選択 / Select schema", on_click=app.pick_schema),
                    ft.Button(
                        "GGUFからモデルを追加 / Add model from GGUF",
                        height=56,
                        on_click=app.pick_gguf,
                    ),
                ],
            ),
            ft.Text(f"Config: {app.state.path or '-'}"),
            ft.Text(f"Schema: {app.state.schema_path or '-'}"),
            ft.Divider(),
            ft.Text("最近開いたconfig / Recent configs", weight=ft.FontWeight.BOLD),
            ft.Column(controls=recent, scroll=ft.ScrollMode.AUTO, expand=True),
        ],
    )
