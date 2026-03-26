from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

import httpx
import prance
import yaml
import yaml.nodes

from happi.log import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

CACHE_DIR = Path.home() / ".happi" / "cache"
FRESHNESS_SECONDS = 86400

_log = get_logger("spec.loader")


class SpecLoadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class _YamlLoaderProtocol(Protocol):
    def add_constructor(
        self,
        tag: str,
        constructor: Callable[[object, object], object],
    ) -> None: ...

    def get_single_data(self) -> object: ...

    def dispose(self) -> None: ...


def load_spec(
    source: str,
    *,
    force_refresh: bool = False,
) -> tuple[dict[str, Any], str]:
    """Load an OpenAPI spec, resolve $refs, and cache the parsed result by content hash."""
    _log.info("Loading spec from %s", source)
    raw = _fetch_raw(source, force_refresh=force_refresh)
    content_hash = hashlib.sha256(raw.encode()).hexdigest()
    _log.debug("Content hash: %s", content_hash[:16])

    cached = _read_cache(content_hash)
    if cached is not None:
        _log.info("Using cached parsed model for hash %s", content_hash[:16])
        return cached, content_hash

    _log.info("Parsing and resolving $refs...")
    parsed = _parse_and_resolve(raw, source)
    _write_cache(content_hash, parsed)
    _log.info("Cached parsed model as %s", content_hash[:16])
    return parsed, content_hash


def _fetch_raw(source: str, *, force_refresh: bool = False) -> str:
    if source.startswith(("http://", "https://")):
        return _fetch_url(source, force_refresh=force_refresh)
    return _read_file(source)


def _fetch_url(url: str, *, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached_raw = _read_raw_cache(url)
        if cached_raw is not None:
            _log.debug("Using cached raw spec for URL %s", url)
            return cached_raw

    _log.info("Fetching spec from %s", url)
    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
    except httpx.ConnectError as e:
        raise SpecLoadError("CONNECTION_ERROR", f"Could not connect to {url}: {e}") from e
    except httpx.HTTPStatusError as e:
        raise SpecLoadError(
            "HTTP_ERROR", f"Failed to fetch spec from {url}: {e.response.status_code}"
        ) from e
    except httpx.TimeoutException as e:
        raise SpecLoadError("TIMEOUT", f"Timed out fetching spec from {url}") from e

    _write_raw_cache(url, response.text)
    return response.text


def _read_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise SpecLoadError("FILE_NOT_FOUND", f"File not found: {path_str}")
    return path.read_text()


def _parse_and_resolve(raw: str, source: str) -> dict[str, Any]:
    parsed = _parse_raw(raw, source)
    return _resolve_refs(parsed, source)


def _parse_raw(raw: str, source: str) -> dict[str, Any]:
    try:
        if source.endswith(".json") or raw.lstrip().startswith("{"):
            result: dict[str, Any] = json.loads(raw)
            return result
        yaml_result: object = _load_yaml_permissive(raw)
        if not isinstance(yaml_result, dict):
            raise SpecLoadError("INVALID_SPEC", f"Not a valid OpenAPI spec: {source}")
        return cast("dict[str, Any]", yaml_result)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise SpecLoadError("INVALID_SPEC", f"Failed to parse spec from {source}: {e}") from e


def _load_yaml_permissive(raw: str) -> object:
    """Handle non-standard YAML tags (like bare '=' in Cloudflare spec)."""
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        _log.debug("safe_load failed, retrying with permissive loader")
        loader = cast("_YamlLoaderProtocol", yaml.SafeLoader(raw))
        loader.add_constructor(
            "tag:yaml.org,2002:value",
            _construct_yaml_value,
        )
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()


def _construct_yaml_value(loader: object, node: object) -> object:
    typed_loader = cast("yaml.SafeLoader", loader)
    typed_node = cast("yaml.nodes.ScalarNode", node)
    return typed_loader.construct_scalar(typed_node)


def _resolve_refs(spec: dict[str, Any], _source: str) -> dict[str, Any]:
    try:
        resolver = prance.ResolvingParser(
            spec_string=json.dumps(spec), backend="openapi-spec-validator"
        )
        raw_spec: object = getattr(resolver, "specification", None)
        if isinstance(raw_spec, dict):
            return cast("dict[str, Any]", raw_spec)
        return spec
    except (ValueError, OSError, KeyError):
        return spec
    except Exception:
        return spec


def _cache_key_for_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _read_raw_cache(url: str) -> str | None:
    cache_dir = CACHE_DIR / "raw"
    key = _cache_key_for_url(url)
    meta_path = cache_dir / f"{key}.meta.json"
    raw_path = cache_dir / f"{key}.raw"

    if not meta_path.exists() or not raw_path.exists():
        return None

    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text())
        fetched_at = float(cast("str", meta.get("fetched_at", "0")))
        if time.time() - fetched_at > FRESHNESS_SECONDS:
            return None
        return raw_path.read_text()
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def _write_raw_cache(url: str, content: str) -> None:
    cache_dir = CACHE_DIR / "raw"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _cache_key_for_url(url)

    meta = {"url": url, "fetched_at": str(time.time())}
    (cache_dir / f"{key}.meta.json").write_text(json.dumps(meta))
    (cache_dir / f"{key}.raw").write_text(content)


def _read_cache(content_hash: str) -> dict[str, Any] | None:
    cache_path = CACHE_DIR / f"{content_hash}.json"
    if not cache_path.exists():
        return None
    try:
        result: dict[str, Any] = json.loads(cache_path.read_text())
        return result
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(content_hash: str, parsed: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{content_hash}.json"
    cache_path.write_text(json.dumps(parsed, default=str))
