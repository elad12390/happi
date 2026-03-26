from __future__ import annotations

import re
from typing import Any, cast

import inflect

from happi.spec.model import Relation, Resource

_inflect_engine = inflect.engine()

_ID_SUFFIX = re.compile(r"^(.+?)(?:_id|Id|_ids|Ids)$")
_CONVENTION_FIELDS = {"created_by", "updated_by", "owned_by", "assigned_to", "author"}


def infer_relations(
    spec: dict[str, Any],
    resources: list[Resource],
) -> list[Relation]:
    resource_names = {r.name for r in resources}
    relations: list[Relation] = []

    relations.extend(_from_paths(spec, resource_names))
    relations.extend(_from_schemas(spec, resource_names))

    seen: set[tuple[str, str, str]] = set()
    unique: list[Relation] = []
    for rel in relations:
        key = (rel.from_resource, rel.to_resource, rel.via)
        if key not in seen:
            seen.add(key)
            unique.append(rel)
    return unique


def _from_paths(spec: dict[str, Any], resource_names: set[str]) -> list[Relation]:
    relations: list[Relation] = []
    paths: dict[str, Any] = spec.get("paths", {})
    for path in paths:
        segments = [s for s in path.split("/") if s and not s.startswith("{")]
        params = [s for s in path.split("/") if s and s.startswith("{")]
        if len(segments) >= 2 and len(params) >= 1:
            parent = _match_resource(segments[0], resource_names)
            child = (
                _match_resource(segments[-1], resource_names)
                if segments[-1] != segments[0]
                else None
            )
            if parent and child and parent != child:
                relations.append(
                    Relation(
                        from_resource=parent,
                        to_resource=child,
                        relation_type="has-many",
                        via="path",
                        confidence="certain",
                    )
                )
    return relations


def _from_schemas(spec: dict[str, Any], resource_names: set[str]) -> list[Relation]:
    relations: list[Relation] = []
    schemas = cast("dict[str, Any]", spec.get("components", {}).get("schemas", {}))
    for schema_name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue
        typed_schema = cast("dict[str, Any]", schema)
        properties = typed_schema.get("properties", {})
        if not isinstance(properties, dict):
            continue
        source_resource = _match_resource(schema_name, resource_names)
        if not source_resource:
            continue
        typed_props = cast("dict[str, Any]", properties)
        for field_name in typed_props:
            match = _ID_SUFFIX.match(field_name)
            if match:
                stem = match.group(1)
                target = _match_resource(stem, resource_names)
                if target and target != source_resource:
                    is_array = field_name.endswith(("_ids", "Ids"))
                    relations.append(
                        Relation(
                            from_resource=source_resource,
                            to_resource=target,
                            relation_type="has-many" if is_array else "belongs-to",
                            via=field_name,
                            confidence="high",
                        )
                    )
            elif field_name in _CONVENTION_FIELDS:
                target = _match_resource("user", resource_names)
                if target:
                    relations.append(
                        Relation(
                            from_resource=source_resource,
                            to_resource=target,
                            relation_type="belongs-to",
                            via=field_name,
                            confidence="medium",
                        )
                    )
    return relations


def _match_resource(name: str, resource_names: set[str]) -> str | None:
    lowered = name.lower().replace("_", "-")
    if lowered in resource_names:
        return lowered
    plural = str(_inflect_engine.plural_noun(cast("inflect.Word", lowered)))
    if plural and plural in resource_names:
        return plural
    singular = _inflect_engine.singular_noun(cast("inflect.Word", lowered))
    if singular:
        re_plural = str(_inflect_engine.plural_noun(cast("inflect.Word", str(singular))))
        if re_plural and re_plural in resource_names:
            return re_plural
    return None
