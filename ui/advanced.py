from __future__ import annotations

import flet as ft


def build_advanced(app) -> ft.Control:
    data = app.state.data or {}
    has_matrix = "matrix" in data
    has_groups = "groups" in data
    snippets = []
    for key in ["macros", "matrix", "groups", "hooks", "peers"]:
        if key in data:
            snippets.append(ft.Text(f"{key}:", weight=ft.FontWeight.BOLD))
            snippets.append(ft.Text(app.dump_fragment(data[key]), selectable=True))
    if not snippets:
        snippets.append(ft.Text("Advanced項目はありません / No advanced sections"))

    controls = [ft.Text("Advanced", size=24, weight=ft.FontWeight.BOLD)]
    if has_matrix and has_groups:
        controls.append(
            ft.Container(
                padding=10,
                bgcolor=ft.Colors.ERROR_CONTAINER,
                border_radius=6,
                content=ft.Text("警告: matrix と groups は同時利用できません / matrix and groups cannot be used together"),
            )
        )
    controls.extend(snippets)
    return ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10, controls=controls)
