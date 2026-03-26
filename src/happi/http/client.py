from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import httpx

from happi.config.config import happi_home
from happi.log import get_logger

_log = get_logger("http.client")

_BINARY_PREFIXES = ("audio/", "image/", "video/", "application/octet-stream", "application/pdf")


class APIError(Exception):
    def __init__(self, status_code: int, body: object) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"API returned status {status_code}")


@dataclass
class BinaryFile:
    path: Path
    content_type: str
    size: int


def send_request(
    *,
    base_url: str,
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    body: object | None = None,
    auth: dict[str, str] | None = None,
    timeout: int = 30,
) -> object:
    url = _join_url(base_url, path)
    headers = _build_auth_headers(auth)
    auth_query = _build_auth_query(auth)

    merged_query: dict[str, Any] | None = None
    if query or auth_query:
        merged_query = dict(query or {})
        merged_query.update(auth_query)

    _log.info("HTTP %s %s", method, url)
    response = httpx.request(
        method=method,
        url=url,
        params=merged_query,
        json=body,
        headers=headers if headers else None,
        timeout=timeout,
        follow_redirects=True,
    )
    _log.debug("Response status: %s", response.status_code)

    if response.is_error:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            error_body: object = response.json()
        else:
            error_body = response.text
        raise APIError(response.status_code, error_body)

    content_type = response.headers.get("content-type", "")
    if _is_binary(content_type):
        return _save_binary(response.content, content_type)

    if "application/json" in content_type:
        payload: object = response.json()
        return payload

    return response.text


def _is_binary(content_type: str) -> bool:
    return any(content_type.startswith(prefix) for prefix in _BINARY_PREFIXES)


def _save_binary(data: bytes, content_type: str) -> BinaryFile:
    ext = _extension_for(content_type)
    downloads = happi_home() / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    filename = f"happi_{int(time.time())}{ext}"
    filepath = downloads / filename
    filepath.write_bytes(data)
    _log.info("Saved binary response (%d bytes) to %s", len(data), filepath)
    return BinaryFile(path=filepath, content_type=content_type, size=len(data))


def _extension_for(content_type: str) -> str:
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/ogg": ".ogg",
        "audio/flac": ".flac",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "video/mp4": ".mp4",
        "application/pdf": ".pdf",
        "application/octet-stream": ".bin",
    }
    for prefix, ext in mapping.items():
        if content_type.startswith(prefix):
            return ext
    return ".bin"


def _build_auth_headers(auth: dict[str, str] | None) -> dict[str, str]:
    if auth is None:
        return {}
    auth_type = auth.get("type", "")
    if auth_type == "bearer":
        tok = auth.get("token", "")
        if tok:
            return {"Authorization": f"Bearer {tok}"}
    if auth_type == "api-key":
        header_name = auth.get("header")
        value = auth.get("value", "")
        if header_name and value:
            return {header_name: value}
    return {}


def _build_auth_query(auth: dict[str, str] | None) -> dict[str, str]:
    if auth is None:
        return {}
    auth_type = auth.get("type", "")
    if auth_type == "api-key":
        query_name = auth.get("query")
        value = auth.get("value", "")
        if query_name and value:
            return {query_name: value}
    return {}


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
