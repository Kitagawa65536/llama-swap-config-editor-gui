from __future__ import annotations

from pathlib import Path

import flet as ft
from ruamel.yaml.comments import CommentedMap

from app_settings import AppSettingsRepository
from config_services import AdvancedConfigService, GlobalSettingsService, ModelConfigService
from gguf_importer import import_gguf, import_many
from models import AdvancedSection, ConfigState, GlobalSettingsForm, ModelForm, ModelListItem
from schema_validator import ConfigSchemaValidator
from ui.advanced import build_advanced
from ui.global_settings import build_global_settings
from ui.home import build_home
from ui.models_view import build_models
from ui.raw_yaml import build_raw_yaml
from yaml_store import YamlConfigStore


ROUTES = {
    "/": "Home",
    "/models": "Models",
    "/global": "Global Settings",
    "/advanced": "Advanced",
    "/raw": "Raw YAML",
}


class LlamaSwapConfigEditor:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "llama-swap Config Editor"
        self.page.window_width = 1180
        self.page.window_height = 760

        self.store = YamlConfigStore()
        self.model_service = ModelConfigService()
        self.global_settings_service = GlobalSettingsService()
        self.advanced_service = AdvancedConfigService(self.store)
        self.settings_repo = AppSettingsRepository()
        self.settings = self.settings_repo.load()
        self.state = ConfigState()
        self.validator = ConfigSchemaValidator()
        self.selected_model_id: str | None = None
        self.current_model_form: ModelForm | None = None
        self.gguf_context_limits: dict[str, int] = {}
        self.global_form = GlobalSettingsForm()
        self.raw_editor: ft.TextField | None = None

        self.config_picker = ft.FilePicker()
        self.schema_picker = ft.FilePicker()
        self.gguf_picker = ft.FilePicker()
        self.page.services.extend([self.config_picker, self.schema_picker, self.gguf_picker])

        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.route_change()

    def route_change(self, _event: ft.RouteChangeEvent | None = None) -> None:
        route = self.page.route or "/"
        if route not in ROUTES:
            route = "/"
            self.page.route = route
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                route=route,
                controls=[self.shell()],
                padding=0,
            )
        )
        self.page.update()

    def view_pop(self, _event: ft.ViewPopEvent) -> None:
        if self.page.views:
            self.page.views.pop()
        self.page.route = self.page.views[-1].route if self.page.views else "/"
        self.route_change()

    def shell(self) -> ft.Control:
        rail = ft.NavigationRail(
            selected_index=self.route_index(self.page.route),
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=96,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationRailDestination(icon=ft.Icons.LIST, label="Models"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Global"),
                ft.NavigationRailDestination(icon=ft.Icons.TUNE, label="Advanced"),
                ft.NavigationRailDestination(icon=ft.Icons.CODE, label="Raw YAML"),
            ],
            on_change=self.on_nav,
        )
        content = ft.Container(expand=True, padding=18, content=self.build_route_content())
        status = ft.Container(
            padding=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("変更あり / Dirty" if self.state.dirty else "変更なし / Clean"),
                    ft.Text(self.state.validation_message, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(self.state.last_message, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Button("検証 / Validate", on_click=self.validate_config),
                    ft.Button("保存 / Save", on_click=self.save_config),
                ],
            ),
        )
        return ft.Column(expand=True, controls=[ft.Row(expand=True, controls=[rail, ft.VerticalDivider(width=1), content]), status])

    def build_route_content(self) -> ft.Control:
        route = self.page.route
        if route == "/models":
            return build_models(self)
        if route == "/global":
            return build_global_settings(self)
        if route == "/advanced":
            return build_advanced(self)
        if route == "/raw":
            return build_raw_yaml(self)
        return build_home(self)

    def on_nav(self, event: ft.ControlEvent) -> None:
        routes = list(ROUTES)
        self.navigate(routes[event.control.selected_index])

    def route_index(self, route: str) -> int:
        routes = list(ROUTES)
        return routes.index(route) if route in routes else 0

    def navigate(self, route: str) -> None:
        self.page.run_task(self.page.push_route, route)

    async def pick_config(self, _event=None) -> None:
        files = await self.config_picker.pick_files(allow_multiple=False, allowed_extensions=["yaml", "yml"])
        self.handle_config_files(files)

    async def pick_schema(self, _event=None) -> None:
        files = await self.schema_picker.pick_files(allow_multiple=False, allowed_extensions=["json"])
        self.handle_schema_files(files)

    async def pick_gguf(self, _event=None) -> None:
        files = await self.gguf_picker.pick_files(allow_multiple=True, allowed_extensions=["gguf"])
        self.handle_gguf_files(files)

    def handle_config_files(self, files: list[ft.FilePickerFile] | None) -> None:
        if files and files[0].path:
            self.open_config(files[0].path)

    def handle_schema_files(self, files: list[ft.FilePickerFile] | None) -> None:
        if not files or not files[0].path:
            return
        try:
            self.state.schema_path = Path(files[0].path)
            self.validator.load(self.state.schema_path)
            self.settings_repo.add_recent_schema(self.settings, str(self.state.schema_path))
            self.state.validation_message = "schema読込OK / Schema loaded"
            self.validate_config()
        except Exception as exc:
            self.state.last_message = f"schema読込失敗 / Schema load failed: {exc}"
            self.refresh()

    def handle_gguf_files(self, files: list[ft.FilePickerFile] | None) -> None:
        if not files:
            return
        suggestions = import_many([file.path for file in files if file.path])
        if not suggestions:
            return
        if self.state.data is None:
            self.state.data = CommentedMap()
            self.state.data["models"] = CommentedMap()
        for suggestion in suggestions:
            model_id = self.unique_model_id(suggestion.model_id)
            form = ModelForm(
                model_id=model_id,
                name=suggestion.name,
                llama_server_path=self.settings.default_llama_server_path,
                model_path=suggestion.model_path,
                context_length=suggestion.context_length,
                context_length_max=suggestion.context_length_max,
                gpu_offload_layers=suggestion.gpu_offload_layers,
            )
            if suggestion.context_length_max is not None:
                self.gguf_context_limits[self.gguf_path_key(suggestion.model_path)] = suggestion.context_length_max
            self.model_service.apply_model_form(self.state.data, None, form)
            self.selected_model_id = model_id
            self.current_model_form = form
        self.mark_dirty(f"{len(suggestions)}件のGGUFを追加しました / GGUF model(s) added")
        self.navigate("/models")

    def open_config(self, path: str) -> None:
        try:
            data, raw = self.store.load(path)
            self.state.path = Path(path)
            self.state.data = data
            self.state.raw_yaml = raw
            self.state.dirty = False
            self.selected_model_id = None
            self.current_model_form = None
            self.global_form = self.global_settings_service.global_settings_form(data)
            self.raw_editor = None
            self.settings_repo.add_recent_config(self.settings, str(path))
            self.state.last_message = "config読込OK / Config loaded"
            self.validate_config()
        except Exception as exc:
            self.state.last_message = f"config読込失敗 / Config load failed: {exc}"
            self.refresh()

    def select_model(self, model_id: str) -> None:
        if self.state.data is None:
            return
        for key, mapping in self.model_service.model_items(self.state.data):
            if key == model_id:
                self.selected_model_id = model_id
                self.current_model_form = self.model_service.model_form_from_mapping(key, mapping)
                context_limit = self.gguf_context_limits.get(self.gguf_path_key(self.current_model_form.model_path))
                if context_limit is not None:
                    self.current_model_form.context_length_max = context_limit
                break
        self.refresh()

    def add_empty_model(self, _event=None) -> None:
        if self.state.data is None:
            self.state.data = CommentedMap()
            self.state.data["models"] = CommentedMap()
        model_id = self.unique_model_id("new-model")
        form = ModelForm(model_id=model_id, llama_server_path=self.settings.default_llama_server_path)
        self.model_service.apply_model_form(self.state.data, None, form)
        self.selected_model_id = model_id
        self.current_model_form = form
        self.mark_dirty("空のモデルを追加しました / Empty model added")

    def apply_current_model(self, _event=None) -> None:
        if self.state.data is None or self.current_model_form is None:
            return
        try:
            original = self.selected_model_id
            self.model_service.apply_model_form(self.state.data, original, self.current_model_form)
            self.selected_model_id = self.current_model_form.model_id
            self.state.raw_yaml = self.store.dump_to_string(self.state.data)
            self.raw_editor = None
            self.mark_dirty("モデルフォームを反映しました / Model form applied")
        except Exception as exc:
            self.state.last_message = f"反映失敗 / Apply failed: {exc}"
            self.refresh()

    def apply_global_settings(self, _event=None) -> None:
        if self.state.data is None:
            self.state.data = CommentedMap()
        self.global_settings_service.apply_global_settings(self.state.data, self.global_form)
        self.state.raw_yaml = self.store.dump_to_string(self.state.data)
        self.raw_editor = None
        self.mark_dirty("Global Settingsを反映しました / Global settings applied")

    def preview_current_cmd(self, _event=None) -> None:
        if self.current_model_form:
            self.state.last_message = self.model_service.preview_command(self.current_model_form)
            self.refresh()

    def load_current_model_gguf_header(self, _event=None) -> None:
        if self.current_model_form is None:
            return
        model_path = self.current_model_form.model_path.strip()
        if not model_path:
            self.state.last_message = "GGUF model pathを入力してください / Enter a GGUF model path first"
            self.refresh()
            return

        suggestion = import_gguf(model_path)
        if suggestion.context_length_max is None:
            error = suggestion.metadata.get("read_error")
            detail = f": {error}" if error else ""
            self.state.last_message = f"Context長の最大値を取得できませんでした / Context max not found{detail}"
            self.refresh()
            return

        context_limit = suggestion.context_length_max
        self.gguf_context_limits[self.gguf_path_key(suggestion.model_path)] = context_limit
        self.current_model_form.context_length_max = context_limit

        current = self.current_model_form.context_length.strip()
        if not current:
            self.current_model_form.context_length = str(context_limit)
            self.state.last_message = f"GGUFヘッダ読込OK。Context長を最大値 {context_limit} にしました / GGUF header loaded"
        else:
            try:
                current_value = int(current)
            except ValueError:
                self.state.last_message = f"GGUFヘッダ読込OK。最大 Context長: {context_limit} / GGUF header loaded"
            else:
                if current_value > context_limit:
                    self.current_model_form.context_length = str(context_limit)
                    self.state.last_message = f"Context長が最大値を超えていたため {context_limit} に丸めました / Clamped to GGUF max"
                else:
                    self.state.last_message = f"GGUFヘッダ読込OK。最大 Context長: {context_limit} / GGUF header loaded"
        self.refresh()

    def on_raw_changed(self, event: ft.ControlEvent) -> None:
        self.state.raw_yaml = event.control.value
        self.state.dirty = True

    def apply_raw_yaml(self, _event=None) -> None:
        try:
            data = self.store.parse_raw(self.state.raw_yaml)
            self.state.data = data
            self.global_form = self.global_settings_service.global_settings_form(data)
            self.selected_model_id = None
            self.current_model_form = None
            self.mark_dirty("Raw YAMLをフォームへ反映しました / Raw YAML applied")
        except Exception as exc:
            self.state.last_message = f"Raw YAML反映失敗。フォーム状態は維持しました / Apply failed: {exc}"
            self.refresh()

    def validate_config(self, _event=None) -> None:
        if self.state.data is None:
            self.state.validation_message = "config未読込 / No config loaded"
        else:
            try:
                ok, message = self.validator.validate(self.state.data)
                self.state.validation_message = ("OK: " if ok else "NG: ") + message
            except Exception as exc:
                self.state.validation_message = f"validation error: {exc}"
        self.refresh()

    def save_config(self, _event=None) -> None:
        if self.state.path is None:
            self.state.last_message = "保存先config.yamlを先に開いてください / Open a config path first"
            self.refresh()
            return
        if self.page.route == "/raw":
            try:
                self.state.data = self.store.parse_raw(self.state.raw_yaml)
            except Exception as exc:
                self.state.last_message = f"YAML構文エラーのため保存不可 / YAML error: {exc}"
                self.refresh()
                return
        try:
            ok, message, _backup = self.store.save(self.state.path, self.state.data, self.validator)
            self.state.last_message = message
            if ok:
                self.state.raw_yaml = self.store.dump_to_string(self.state.data)
                self.state.dirty = False
                self.raw_editor = None
                self.validate_config()
            else:
                self.refresh()
        except Exception as exc:
            self.state.last_message = f"保存失敗 / Save failed: {exc}"
            self.refresh()

    def unique_model_id(self, base: str) -> str:
        existing = set()
        if self.state.data is not None and isinstance(self.state.data.get("models"), dict):
            existing = {str(key) for key in self.state.data["models"].keys()}
        candidate = base
        count = 2
        while candidate in existing:
            candidate = f"{base}-{count}"
            count += 1
        return candidate

    def gguf_path_key(self, path: str) -> str:
        try:
            return str(Path(path).expanduser().resolve())
        except OSError:
            return path

    def model_list_items(self) -> list[ModelListItem]:
        if self.state.data is None:
            return []
        return self.model_service.list_items(self.state.data)

    def advanced_sections(self) -> list[AdvancedSection]:
        return self.advanced_service.sections(self.state.data)

    def has_advanced_conflict(self) -> bool:
        return self.advanced_service.has_matrix_groups_conflict(self.state.data)

    def mark_dirty(self, message: str) -> None:
        self.state.dirty = True
        self.state.last_message = message
        self.refresh()

    def refresh(self) -> None:
        self.route_change()


def main(page: ft.Page) -> None:
    LlamaSwapConfigEditor(page)


if __name__ == "__main__":
    ft.run(main)
