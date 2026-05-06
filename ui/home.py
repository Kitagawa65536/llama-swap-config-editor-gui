from __future__ import annotations

import flet as ft


def build_home(app) -> ft.Control:
    recent = [
        ft.ListTile(title=ft.Text(path), on_click=lambda e, p=path: app.open_config(p))
        for path in app.settings.recent_configs
    ]
    if not recent:
        recent = [ft.Text(app.t("home.no_recent_configs"))]

    return ft.Column(
        expand=True,
        spacing=16,
        controls=[
            ft.Text(app.t("home.title"), size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                wrap=True,
                controls=[
                    ft.Button(app.t("home.new_config"), on_click=app.create_new_config),
                    ft.Button(app.t("home.open_config"), on_click=app.pick_config),
                    # Bundled demo schema support is deferred; users currently select an external config-schema.json.
                    ft.OutlinedButton(app.t("home.select_schema"), on_click=app.pick_schema),
                    ft.Button(
                        app.t("home.add_gguf"),
                        height=56,
                        on_click=app.pick_gguf,
                    ),
                ],
            ),
            ft.Text(app.t("home.config_path", path=app.state.path or "-")),
            ft.Text(app.t("home.schema_path", path=app.state.schema_path or "-")),
            ft.Divider(),
            ft.Text(app.t("home.recent_configs"), weight=ft.FontWeight.BOLD),
            ft.Column(controls=recent, scroll=ft.ScrollMode.AUTO, expand=True),
        ],
    )
