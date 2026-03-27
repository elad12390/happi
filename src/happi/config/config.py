from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any, cast

import yaml


def happi_home() -> Path:
    override = os.environ.get("HAPPI_HOME")
    if override:
        return Path(override)
    return Path.home() / ".happi"


def config_path() -> Path:
    return happi_home() / "config.yaml"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {"apis": {}}
    loaded = yaml.safe_load(path.read_text())
    if isinstance(loaded, dict):
        return cast("dict[str, Any]", loaded)
    return {"apis": {}}


def save_config(config: dict[str, Any]) -> None:
    home = happi_home()
    home.mkdir(parents=True, exist_ok=True)
    path = config_path()
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # chmod 600


def upsert_profile(name: str, profile: dict[str, Any]) -> dict[str, Any]:
    config = load_config()
    apis = config.setdefault("apis", {})
    typed_apis = cast("dict[str, Any]", apis)
    existing = typed_apis.get(name, {})
    merged = dict(existing)
    merged.update(profile)
    typed_apis[name] = merged
    save_config(config)
    return merged


def list_profiles() -> dict[str, Any]:
    config = load_config()
    apis = config.get("apis", {})
    if isinstance(apis, dict):
        return cast("dict[str, Any]", apis)
    return {}


def set_config_value(path_expr: str, value: object) -> None:
    config = load_config()
    current: dict[str, Any] = config
    parts = path_expr.split(".")
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = cast("dict[str, Any]", next_value)
    current[parts[-1]] = value
    save_config(config)


def get_config_value(path_expr: str) -> object:
    current: object = load_config()
    for part in path_expr.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current_dict = cast("dict[str, object]", current)
        current = current_dict[part]
    return current


def unset_config_value(path_expr: str) -> bool:
    config = load_config()
    current: dict[str, Any] = config
    parts = path_expr.split(".")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            return False
        current = cast("dict[str, Any]", next_value)
    removed = current.pop(parts[-1], None)
    save_config(config)
    return removed is not None


def mask_secret(value: object, *, reveal: bool = False) -> str:
    if reveal:
        return str(value)
    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)
    return f"{text[:2]}{'*' * (len(text) - 6)}{text[-4:]}"
