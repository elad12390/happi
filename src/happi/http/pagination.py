from __future__ import annotations

import re
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from happi.log import get_logger

_log = get_logger("http.pagination")

_PAGE_PARAMS = frozenset({"page", "page_number", "pageNumber"})
_OFFSET_PARAMS = frozenset({"offset", "skip"})
_CURSOR_PARAMS = frozenset({"cursor", "starting_after", "after", "next_cursor", "continuation"})
_LIMIT_PARAMS = frozenset({"limit", "per_page", "perPage", "page_size", "pageSize", "count"})

_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def detect_pagination_info(
    query_param_names: set[str],
    response_headers: dict[str, str],
    response_body: object,
) -> dict[str, Any]:
    info: dict[str, Any] = {"has_more": False, "style": None, "next": None}

    next_link = _parse_link_header(response_headers)
    if next_link:
        info["has_more"] = True
        info["style"] = "link-header"
        info["next"] = next_link
        return info

    if isinstance(response_body, dict):
        body = cast("dict[str, Any]", response_body)
        next_url = body.get("next") or body.get("next_url") or body.get("next_page_url")
        if isinstance(next_url, str) and next_url:
            info["has_more"] = True
            info["style"] = "next-url"
            info["next"] = next_url
            return info

        next_cursor = body.get("next_cursor") or body.get("cursor")
        has_more = body.get("has_more") or body.get("hasMore")
        if has_more and next_cursor:
            info["has_more"] = True
            info["style"] = "cursor"
            info["next"] = str(next_cursor)
            return info

    if query_param_names & _PAGE_PARAMS:
        info["style"] = "page"
    elif query_param_names & _OFFSET_PARAMS:
        info["style"] = "offset"
    elif query_param_names & _CURSOR_PARAMS:
        info["style"] = "cursor"

    return info


def build_next_query(
    current_query: dict[str, Any],
    pagination_info: dict[str, Any],
    query_param_names: set[str],
) -> dict[str, Any] | None:
    style = pagination_info.get("style")
    if not style or not pagination_info.get("has_more"):
        return None

    next_query = dict(current_query)

    if style == "link-header":
        next_url = str(pagination_info.get("next", ""))
        if next_url:
            parsed = urlparse(next_url)
            qs = parse_qs(parsed.query)
            return {k: v[0] if len(v) == 1 else v for k, v in qs.items()}
        return None

    if style == "next-url":
        next_url = str(pagination_info.get("next", ""))
        if next_url:
            parsed = urlparse(next_url)
            qs = parse_qs(parsed.query)
            return {k: v[0] if len(v) == 1 else v for k, v in qs.items()}
        return None

    if style == "page":
        page_key = next((k for k in query_param_names if k in _PAGE_PARAMS), "page")
        current_page = int(current_query.get(page_key, 1))
        next_query[page_key] = str(current_page + 1)
        return next_query

    if style == "offset":
        offset_key = next((k for k in query_param_names if k in _OFFSET_PARAMS), "offset")
        limit_key = next((k for k in query_param_names if k in _LIMIT_PARAMS), "limit")
        current_offset = int(current_query.get(offset_key, 0))
        limit = int(current_query.get(limit_key, 20))
        next_query[offset_key] = str(current_offset + limit)
        return next_query

    if style == "cursor":
        cursor_key = next((k for k in query_param_names if k in _CURSOR_PARAMS), "cursor")
        next_cursor = pagination_info.get("next")
        if next_cursor:
            next_query[cursor_key] = str(next_cursor)
            return next_query

    return None


def _parse_link_header(headers: dict[str, str]) -> str | None:
    link_header = headers.get("link") or headers.get("Link")
    if not link_header:
        return None
    match = _LINK_RE.search(link_header)
    if match:
        return match.group(1)
    return None
