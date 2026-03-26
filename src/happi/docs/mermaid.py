from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from happi.spec.model import Relation, Resource


def generate_mermaid(resources: list[Resource], relations: list[Relation]) -> str:
    lines = ["```mermaid", "graph LR"]
    for resource in resources:
        action_count = len(resource.operations)
        lines.append(f'    {_node_id(resource.name)}["{resource.name}<br/>{action_count} actions"]')
    for relation in relations:
        label = relation.relation_type
        if relation.confidence == "medium":
            label += " ?"
        src = _node_id(relation.from_resource)
        dst = _node_id(relation.to_resource)
        lines.append(f"    {src} -->|{label}| {dst}")
    lines.append("```")
    return "\n".join(lines)


def _node_id(name: str) -> str:
    return name.replace("-", "_")
