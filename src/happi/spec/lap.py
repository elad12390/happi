from __future__ import annotations

import os
from typing import Any, cast

import httpx

REGISTRY_URL = "https://registry.lap.sh/registry.json"


class LapResolutionError(Exception):
    pass


def resolve_from_lap(name: str) -> dict[str, str]:
    url = os.environ.get("HAPPI_LAP_REGISTRY_URL", REGISTRY_URL)
    headers = {"User-Agent": "happi/0.1.0"}
    offset = 0

    while True:
        response = httpx.get(
            url, params={"offset": offset, "limit": 500}, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        specs = cast("list[dict[str, Any]]", data.get("specs", []))

        match = _find_match(specs, name)
        if match is not None:
            source_url = cast("str", match.get("source_url", ""))
            base_url = cast("str", match.get("base_url", ""))
            lap_name = cast("str", match.get("name", name))
            if not source_url:
                raise LapResolutionError(f"LAP entry for {name} has no source_url")
            return {"name": lap_name, "spec_url": source_url, "base_url": base_url}

        pagination = cast("dict[str, Any]", data.get("pagination", {}))
        has_more = cast("bool", pagination.get("has_more", False))
        if not has_more:
            raise LapResolutionError(f"No LAP registry entry found for {name}")
        offset = cast("int", pagination.get("next_offset", offset + 500))


def _find_match(specs: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    lowered = name.lower()
    normalized = lowered.replace("_", "-")
    for item in specs:
        item_name = cast("str", item.get("name", "")).lower()
        provider = cast("dict[str, Any]", item.get("provider", {}))
        slug = cast("str", provider.get("slug", "")).lower()
        display_name = cast("str", provider.get("display_name", "")).lower()
        if normalized in {item_name, slug, display_name}:
            return item
    return None
