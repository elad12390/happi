from __future__ import annotations

import re
from typing import Any, cast

import inflect

from happi.log import get_logger
from happi.spec.model import Operation, Param, Resource

_inflect_engine = inflect.engine()
_log = get_logger("spec.resources")

_VERSION_SEGMENTS = frozenset({"v1", "v2", "v3", "v4", "api"})


def extract_resources(spec: dict[str, Any]) -> list[Resource]:
    """Extract resources from OpenAPI spec paths. Path segments take priority over tags."""
    paths: dict[str, Any] = spec.get("paths", {})

    all_paths = set(paths.keys())
    resource_roots = _identify_resource_roots(all_paths)
    _log.debug("Identified resource roots: %s", sorted(resource_roots))
    _log.info("Processing %d paths", len(all_paths))

    resource_map: dict[str, Resource] = {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        typed_path_item = cast("dict[str, Any]", path_item)
        for method, raw_op in typed_path_item.items():
            if method in ("parameters", "summary", "description", "servers"):
                continue
            if not isinstance(raw_op, dict):
                continue
            operation = cast("dict[str, Any]", raw_op)

            resource_name, verb, parent_param, is_action = _classify_operation(
                method, path, operation, resource_roots
            )
            action_label = " (action)" if is_action else ""
            _log.debug("%s %s → %s %s%s", method.upper(), path, resource_name, verb, action_label)

            if resource_name not in resource_map:
                resource_map[resource_name] = Resource(
                    name=resource_name,
                    description=_get_resource_description(operation, resource_name),
                )

            resource = resource_map[resource_name]

            args = _extract_path_args(path, operation)
            flags = _extract_query_flags(operation)

            summary: str = cast("str", operation.get("summary", ""))
            description: str = cast("str", operation.get("description", ""))
            op = Operation(
                verb=verb,
                http_method=method.upper(),
                path=path,
                summary=summary,
                description=description,
                args=args,
                flags=flags,
                is_action=is_action,
            )

            resource.operations.append(op)

            if parent_param and not resource.parent_param:
                resource.parent_param = parent_param

    result = list(resource_map.values())
    for resource in result:
        _deduplicate_verbs(resource)
    _log.info(
        "Extracted %d resources: %s",
        len(result),
        ", ".join(r.name for r in result),
    )
    return result


def _identify_resource_roots(all_paths: set[str]) -> set[str]:
    """Find segments that are true resources (have a corresponding item endpoint with {id})."""
    roots: set[str] = set()
    all_segments_list = [_meaningful_segments(p) for p in all_paths]

    for segments in all_segments_list:
        if not segments:
            continue
        roots.add(segments[0])

    sub_candidates: set[str] = set()
    for segments in all_segments_list:
        for i, seg in enumerate(segments):
            if not _is_param(seg) and i > 0 and not _is_param(segments[i - 1]):
                sub_candidates.add(seg)
            if not _is_param(seg) and i > 0 and _is_param(segments[i - 1]):
                sub_candidates.add(seg)

    for candidate in sub_candidates:
        for segments in all_segments_list:
            if candidate in segments:
                idx = segments.index(candidate)
                if idx + 1 < len(segments) and _is_param(segments[idx + 1]):
                    roots.add(candidate)
                    break

    return roots


_ClassifyResult = tuple[str, str, Param | None, bool]


def _classify_operation(
    method: str,
    path: str,
    operation: dict[str, Any],
    resource_roots: set[str],
) -> _ClassifyResult:
    segments = _meaningful_segments(path)
    method = method.lower()

    if not segments:
        return "root", method, None, False

    root = segments[0]
    resource_name = _normalize_resource_name(root)

    if len(segments) == 1:
        return resource_name, _method_to_verb(method, has_id=False), None, False

    if len(segments) == 2:
        return _classify_two_segments(method, segments, resource_name, resource_roots)

    if _is_param(segments[1]):
        return _classify_nested_with_id(method, segments, resource_name, root, resource_roots)

    return _classify_nested_without_id(method, segments, resource_name, resource_roots)


def _classify_two_segments(
    method: str,
    segments: list[str],
    resource_name: str,
    resource_roots: set[str],
) -> _ClassifyResult:
    tail = segments[1]
    if _is_param(tail):
        return resource_name, _method_to_verb(method, has_id=True), None, False

    if tail in resource_roots:
        parent_param = Param(
            name=_to_flag_name(segments[0]),
            location="path",
            param_type="string",
            required=True,
        )
        return (
            _normalize_resource_name(tail),
            _method_to_verb(method, has_id=False),
            parent_param,
            False,
        )

    return resource_name, _to_kebab(tail), None, True


def _classify_nested_with_id(
    method: str,
    segments: list[str],
    resource_name: str,
    root: str,
    resource_roots: set[str],
) -> _ClassifyResult:
    tail_non_params = [s for s in segments[2:] if not _is_param(s)]
    if not tail_non_params:
        return resource_name, _method_to_verb(method, has_id=True), None, False

    last_tail = tail_non_params[-1]
    if last_tail in resource_roots:
        tail_idx = segments.index(last_tail)
        has_sub_id = any(_is_param(s) for s in segments[tail_idx + 1 :])
        parent_param = Param(
            name=_to_flag_name(root),
            location="path",
            param_type="string",
            required=True,
        )
        return (
            _normalize_resource_name(last_tail),
            _method_to_verb(method, has_id=has_sub_id),
            parent_param,
            False,
        )

    return resource_name, _to_kebab(last_tail), None, True


def _classify_nested_without_id(
    method: str,
    segments: list[str],
    resource_name: str,
    resource_roots: set[str],
) -> _ClassifyResult:
    sub = segments[1]
    if sub not in resource_roots:
        return resource_name, _to_kebab(sub), None, True

    sub_resource_name = _normalize_resource_name(sub)
    has_sub_id = _is_param(segments[2]) if len(segments) >= 3 else False
    if has_sub_id and len(segments) >= 4:
        tail_after = [s for s in segments[3:] if not _is_param(s)]
        if tail_after:
            return sub_resource_name, _to_kebab(tail_after[-1]), None, True
    return sub_resource_name, _method_to_verb(method, has_id=has_sub_id), None, False


def _meaningful_segments(path: str) -> list[str]:
    segments = _path_segments(path)
    return [s for s in segments if s.lower() not in _VERSION_SEGMENTS]


def _method_to_verb(method: str, *, has_id: bool) -> str:
    mapping_with_id: dict[str, str] = {
        "get": "show",
        "put": "update",
        "patch": "update",
        "delete": "delete",
        "post": "create",
    }
    mapping_collection: dict[str, str] = {
        "get": "list",
        "post": "create",
        "put": "update",
        "patch": "update",
        "delete": "delete",
    }
    if has_id:
        return mapping_with_id.get(method, method)
    return mapping_collection.get(method, method)


def _path_segments(path: str) -> list[str]:
    return [s for s in path.split("/") if s]


def _is_param(segment: str) -> bool:
    return segment.startswith("{") and segment.endswith("}")


def _to_kebab(name: str) -> str:
    name = re.sub(r"[_\s]+", "-", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name)
    return name.lower()


def _to_flag_name(name: str) -> str:
    kebab = _to_kebab(name)
    singular = _inflect_engine.singular_noun(cast("inflect.Word", kebab))
    if singular:
        return str(singular)
    return kebab


def _normalize_resource_name(segment: str) -> str:
    kebab = _to_kebab(segment)
    word = cast("inflect.Word", kebab)
    singular = _inflect_engine.singular_noun(word)
    if singular and singular != kebab:
        return str(_inflect_engine.plural_noun(cast("inflect.Word", singular)))
    if not _inflect_engine.singular_noun(word):
        return str(_inflect_engine.plural_noun(word))
    return kebab


def _deduplicate_verbs(resource: Resource) -> None:
    seen: dict[str, int] = {}
    for op in resource.operations:
        if op.verb in seen:
            seen[op.verb] += 1
            suffix = _derive_suffix(op)
            op.verb = f"{op.verb}-{suffix}" if suffix else f"{op.verb}-{seen[op.verb]}"
        else:
            seen[op.verb] = 1


def _derive_suffix(op: Operation) -> str:
    segments = [s for s in op.path.split("/") if s and not s.startswith("{")]
    if segments:
        candidate = _to_kebab(segments[-1])
        if candidate != op.verb:
            return candidate
    if op.summary:
        words = op.summary.lower().split()
        if len(words) >= 2:
            return _to_kebab(words[-1])
    return ""


def _get_resource_description(operation: dict[str, Any], fallback: str) -> str:
    tags: list[str] = operation.get("tags", [])
    if tags:
        return tags[0]
    return fallback


def _extract_path_args(path: str, operation: dict[str, Any]) -> list[Param]:
    raw_params: object = operation.get("parameters", [])
    params: list[dict[str, Any]] = (
        cast("list[dict[str, Any]]", raw_params) if isinstance(raw_params, list) else []
    )
    return [
        Param(
            name=cast("str", param.get("name", "")),
            location="path",
            param_type=_schema_type(param.get("schema", {})),
            required=True,
            description=cast("str", param.get("description", "")),
        )
        for param in params
        if param.get("in") == "path"
    ]


def _extract_query_flags(operation: dict[str, Any]) -> list[Param]:
    flags: list[Param] = []
    raw_params: object = operation.get("parameters", [])
    params: list[dict[str, Any]] = (
        cast("list[dict[str, Any]]", raw_params) if isinstance(raw_params, list) else []
    )
    for param in params:
        if param.get("in") == "query":
            raw_schema: object = param.get("schema", {})
            typed_schema: dict[str, Any] = (
                cast("dict[str, Any]", raw_schema) if isinstance(raw_schema, dict) else {}
            )
            enum_values: list[str] = cast("list[str]", typed_schema.get("enum", []))
            flags.append(
                Param(
                    name=cast("str", param.get("name", "")),
                    location="query",
                    param_type=_schema_type(typed_schema),
                    required=cast("bool", param.get("required", False)),
                    description=cast("str", param.get("description", "")),
                    enum_values=enum_values,
                )
            )
    return flags


def _schema_type(schema: object) -> str:
    if isinstance(schema, dict):
        typed_schema = cast("dict[str, Any]", schema)
        return str(typed_schema.get("type", "string"))
    return "string"
