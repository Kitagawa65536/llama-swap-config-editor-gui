from __future__ import annotations

import flet as ft


def build_global_settings(app) -> ft.Control:
    f = app.global_form

    def set_attr(name):
        return lambda e: setattr(f, name, e.control.value)

    def set_bool(e):
        f.send_loading_state = e.control.value

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=12,
        controls=[
            ft.Text("Global Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.TextField(label="healthCheckTimeout", value=f.health_check_timeout, on_change=set_attr("health_check_timeout")),
            ft.TextField(label="logLevel", value=f.log_level, on_change=set_attr("log_level")),
            ft.TextField(label="startPort", value=f.start_port, on_change=set_attr("start_port")),
            ft.TextField(label="globalTTL", value=f.global_ttl, on_change=set_attr("global_ttl")),
            ft.Checkbox(label="sendLoadingState", value=bool(f.send_loading_state), on_change=set_bool),
            ft.Button("Global Settingsを反映 / Apply", on_click=app.apply_global_settings),
        ],
    )
