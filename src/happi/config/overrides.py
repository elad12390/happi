from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from happi.log import get_logger

_log = get_logger("config.overrides")

OVERRIDE_FILE = ".happi.yaml"


def load_overrides() -> dict[str, Any]:
    path = Path.cwd() / OVERRIDE_FILE
    if not path.exists():
        return {}
    _log.info("Loading overrides from %s", path)
    loaded = yaml.safe_load(path.read_text())
    if isinstance(loaded, dict):
        return cast("dict[str, Any]", loaded)
    return {}


def get_relation_overrides() -> dict[str, str | None]:
    overrides = load_overrides()
    raw = overrides.get("relations", {})
    if not isinstance(raw, dict):
        return {}
    return cast("dict[str, str | None]", raw)


def get_name_overrides() -> dict[str, dict[str, str]]:
    overrides = load_overrides()
    names = overrides.get("names", {})
    if not isinstance(names, dict):
        return {}
    return cast("dict[str, dict[str, str]]", names)


def get_display_overrides() -> dict[str, Any]:
    overrides = load_overrides()
    display = overrides.get("display", {})
    if not isinstance(display, dict):
        return {}
    return cast("dict[str, Any]", display)
