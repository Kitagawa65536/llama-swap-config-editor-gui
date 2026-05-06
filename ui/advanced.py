from __future__ import annotations

import flet as ft


def build_advanced(app) -> ft.Control:
    snippets = []
    # Advanced editing is deferred; this view currently exposes read-only YAML fragments.
    for section in app.advanced_sections():
        snippets.append(ft.Text(f"{section.key}:", weight=ft.FontWeight.BOLD))
        snippets.append(ft.Text(section.yaml_fragment, selectable=True))
    if not snippets:
        snippets.append(ft.Text(app.t("advanced.empty")))

    controls = [ft.Text(app.t("advanced.title"), size=24, weight=ft.FontWeight.BOLD)]
    if app.has_advanced_conflict():
        controls.append(
            ft.Container(
                padding=10,
                bgcolor=ft.Colors.ERROR_CONTAINER,
                border_radius=6,
                content=ft.Text(app.t("advanced.conflict")),
            )
        )
    controls.extend(snippets)
    return ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10, controls=controls)
