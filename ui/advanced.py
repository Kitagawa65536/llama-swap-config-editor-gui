from __future__ import annotations

import flet as ft


def build_advanced(app) -> ft.Control:
    snippets = []
    # Advanced editing is deferred; this view currently exposes read-only YAML fragments.
    for section in app.advanced_sections():
        snippets.append(ft.Text(f"{section.key}:", weight=ft.FontWeight.BOLD))
        snippets.append(ft.Text(section.yaml_fragment, selectable=True))
    if not snippets:
        snippets.append(ft.Text("Advanced項目はありません / No advanced sections"))

    controls = [ft.Text("Advanced", size=24, weight=ft.FontWeight.BOLD)]
    if app.has_advanced_conflict():
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
