from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Any


SUPPORTED_LOCALES = ("ja", "en")
DEFAULT_LOCALE = "ja"
FALLBACK_LOCALE = "en"


class I18n:
    def __init__(
        self,
        current_locale: str,
        fallback_locale: str = FALLBACK_LOCALE,
        locales_dir: Path | None = None,
    ) -> None:
        self.locales_dir = locales_dir or Path(__file__).parent / "locales"
        self.fallback_locale = normalize_locale(fallback_locale)
        self.current_locale = normalize_locale(current_locale)
        self._catalogs: dict[str, dict[str, str]] = {}

    def set_locale(self, locale_name: str) -> None:
        self.current_locale = normalize_locale(locale_name)

    def translate(self, key: str, **kwargs: Any) -> str:
        template = self._lookup(self.current_locale, key)
        if template is None and self.current_locale != self.fallback_locale:
            template = self._lookup(self.fallback_locale, key)
        if template is None:
            template = key
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    def _lookup(self, locale_name: str, key: str) -> str | None:
        return self._catalog(locale_name).get(key)

    def _catalog(self, locale_name: str) -> dict[str, str]:
        if locale_name not in self._catalogs:
            path = self.locales_dir / f"{locale_name}.json"
            try:
                self._catalogs[locale_name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                self._catalogs[locale_name] = {}
        return self._catalogs[locale_name]


def normalize_locale(locale_name: str | None) -> str:
    if not locale_name:
        return DEFAULT_LOCALE
    normalized = locale_name.replace("-", "_").split("_", 1)[0].casefold()
    return normalized if normalized in SUPPORTED_LOCALES else DEFAULT_LOCALE


def detect_system_locale() -> str:
    language, _encoding = locale.getlocale()
    return normalize_locale(language)
