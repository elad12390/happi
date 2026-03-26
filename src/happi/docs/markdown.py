from __future__ import annotations

from typing import TYPE_CHECKING

from happi.docs.mermaid import generate_mermaid

if TYPE_CHECKING:
    from happi.spec.model import Relation, Resource


def generate_markdown(
    api_name: str,
    resources: list[Resource],
    relations: list[Relation] | None = None,
) -> str:
    lines = [f"# {api_name}", ""]

    if relations:
        lines.append("## Relationship Map")
        lines.append("")
        lines.append(generate_mermaid(resources, relations))
        lines.append("")

        lines.append("## Relations")
        lines.append("")
        lines.append("| From | → | To | Via | Confidence |")
        lines.append("|---|---|---|---|---|")
        lines.extend(
            f"| {rel.from_resource} | {rel.relation_type} | "
            f"{rel.to_resource} | `{rel.via}` | {rel.confidence} |"
            for rel in relations
        )
        lines.append("")

    lines.append("## Resources")
    lines.append("")
    for resource in resources:
        lines.append(f"### {resource.name}")
        lines.append("")
        lines.extend(
            f"- `{op.verb}` — {op.summary or op.description or op.path}"
            for op in sorted(resource.operations, key=lambda o: o.verb)
        )
        lines.append("")

    lines.append("## Quick Reference")
    lines.append("")
    lines.append("| I want to... | Command |")
    lines.append("|---|---|")
    for resource in resources[:5]:
        for op in resource.operations[:2]:
            arg_str = " <id>" if op.args else ""
            lines.append(
                f"| {op.summary or op.verb.title() + ' ' + resource.name} "
                f"| `happi {api_name} {resource.name} {op.verb}{arg_str}` |"
            )
    lines.append("")
    return "\n".join(lines)
