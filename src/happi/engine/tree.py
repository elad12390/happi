from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import typer

from happi.config.config import list_profiles
from happi.display.basic import render_error, render_explore
from happi.display.history import render_history
from happi.docs.markdown import generate_markdown
from happi.docs.mermaid import generate_mermaid
from happi.engine.executor import execute_operation
from happi.engine.history import get_history
from happi.engine.stack import get_stack
from happi.log import get_logger
from happi.spec.loader import load_spec
from happi.spec.relations import infer_relations
from happi.spec.resources import extract_resources

if TYPE_CHECKING:
    from happi.spec.model import Operation, Resource

_ALL_ARGS = typer.Argument(None)

_registered = False
_log = get_logger("engine.tree")


def register_profile_apps(root_app: typer.Typer) -> None:
    global _registered
    if _registered:
        return
    profiles = list_profiles()
    for api_name, raw_profile in profiles.items():
        if isinstance(raw_profile, dict):
            api_app = _build_api_app(api_name, cast("dict[str, Any]", raw_profile))
            root_app.add_typer(api_app, name=api_name)
            _log.info("Registered API command group: %s", api_name)
    _registered = True


def _build_api_app(api_name: str, profile: dict[str, Any]) -> typer.Typer:
    spec_info = cast("dict[str, Any]", profile.get("spec", {}))
    spec_url = cast("str | None", spec_info.get("url"))
    if not spec_url:
        return typer.Typer(help=f"{api_name} (missing spec configuration)", no_args_is_help=True)

    spec, _ = load_spec(spec_url)
    resources = extract_resources(spec)
    relations = infer_relations(spec, resources)
    api_app = typer.Typer(
        help=_api_help_text(api_name, resources), no_args_is_help=True, rich_markup_mode="rich"
    )

    def explore_command() -> None:
        rows = [(resource.name, _sorted_verbs(resource.operations)) for resource in resources]
        render_explore(api_name, rows)

    api_app.command(name="explore", help="Browse resources and actions for this API.")(
        explore_command
    )

    def find_command(query: str = typer.Argument(help="Search query")) -> None:
        _render_find(api_name, resources, query)

    api_app.command(name="find", help="Search resources and actions by name or description.")(
        find_command
    )

    def docs_command(
        map_only: bool = typer.Option(False, "--map-only", help="Output just the Mermaid diagram"),
        resource_filter: str | None = typer.Option(
            None, "--resource", help="Generate docs for one resource only"
        ),
    ) -> None:
        if map_only:
            typer.echo(generate_mermaid(resources, relations))
            return
        if resource_filter:
            filtered = [r for r in resources if r.name == resource_filter]
            if not filtered:
                render_error(f"No resource named '{resource_filter}'")
                return
            typer.echo(generate_markdown(api_name, filtered, relations=relations))
            return
        typer.echo(generate_markdown(api_name, resources, relations=relations))

    api_app.command(name="docs", help="Generate Markdown docs for this API.")(docs_command)

    def history_command(
        limit: int = typer.Option(20, help="Maximum number of rows to show"),
    ) -> None:
        rows = get_history(api_name=api_name, limit=limit)
        render_history(rows)

    api_app.command(name="history", help="Show command history for this API.")(history_command)

    def stack_command() -> None:
        entries = get_stack(api_name)
        if not entries:
            typer.echo("Stack is empty for this session.")
            return
        from rich.table import Table as RichTable

        table = RichTable(show_header=True, header_style="bold")
        table.add_column("Ref", style="dim")
        table.add_column("ID", style="cyan")
        table.add_column("Source")
        for idx, entry in enumerate(entries):
            ref = "_" if idx == 0 else f"_{idx}"
            primary_id = str(entry.get("primary_id", "—"))
            source = f"{entry.get('resource', '')}.{entry.get('verb', '')}"
            table.add_row(ref, primary_id, source)
        from rich.console import Console as RichConsole

        RichConsole().print(table)

    api_app.command(name="stack", help="Show the response stack for this session.")(stack_command)

    for resource in resources:
        resource_app = _build_resource_app(api_name, profile, resource)
        api_app.add_typer(resource_app, name=resource.name)

    return api_app


def _build_resource_app(api_name: str, profile: dict[str, Any], resource: Resource) -> typer.Typer:
    resource_app = typer.Typer(
        help=_resource_help_text(api_name, resource), no_args_is_help=True, rich_markup_mode="rich"
    )
    for operation in resource.operations:
        _register_operation_command(resource_app, api_name, profile, resource, operation)
    return resource_app


def _register_operation_command(
    resource_app: typer.Typer,
    api_name: str,
    profile: dict[str, Any],
    resource: Resource,
    operation: Operation,
) -> None:
    help_text = _operation_help_text(api_name, resource, operation)

    def run_operation_command(ctx: typer.Context, args: list[str] = _ALL_ARGS) -> None:
        if ctx.resilient_parsing:
            return
        base_url = cast("str", profile.get("base_url", ""))
        if not base_url:
            render_error(f"No base URL configured for {api_name}")
            raise typer.Exit(1)
        raw_tokens = args or []
        cleaned_tokens, preserved_flags = _strip_global_flags(raw_tokens)
        path_arg_count = len(operation.args)
        positional = cleaned_tokens[:path_arg_count]
        extras = cleaned_tokens[path_arg_count:] + preserved_flags
        raw_auth = profile.get("auth")
        auth_dict = cast("dict[str, str]", raw_auth) if isinstance(raw_auth, dict) else None
        exit_code = execute_operation(
            api_name=api_name,
            base_url=base_url,
            resource_name=resource.name,
            operation=operation,
            positional=positional,
            extras=extras,
            command_text=(
                f"happi {api_name} {resource.name} {operation.verb} {' '.join(raw_tokens)}"
            ).strip(),
            auth=auth_dict,
        )
        if exit_code != 0:
            raise typer.Exit(exit_code)

    resource_app.command(
        name=operation.verb,
        help=help_text,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )(run_operation_command)


def _api_help_text(api_name: str, resources: list[Resource]) -> str:
    sample = "\n".join(f"  happi {api_name} {resource.name} --help" for resource in resources[:3])
    return (
        f"Choose a resource for {api_name}.\n\n"
        f"Examples:\n{sample}\n\n"
        f"Next:\n  happi {api_name} explore"
    )


def _resource_help_text(api_name: str, resource: Resource) -> str:
    examples = "\n".join(
        f"  happi {api_name} {resource.name} {op.verb}" + (" <id>" if op.args else "")
        for op in resource.operations[:4]
    )
    return (
        f"Commands for working with {resource.name}.\n\n"
        f"Examples:\n{examples}\n\n"
        f"Next:\n  happi {api_name} {resource.name} <action> --help"
    )


def _operation_help_text(api_name: str, resource: Resource, operation: Operation) -> str:
    arg_names = " ".join(f"<{arg.name}>" for arg in operation.args)
    usage = f"happi {api_name} {resource.name} {operation.verb} {arg_names}".rstrip()
    flag_preview = "\n".join(
        f"  --{flag.name}    {flag.description}" for flag in operation.flags[:6]
    )
    example = usage
    if operation.flags:
        first_flag = operation.flags[0]
        example = f"{usage} --{first_flag.name} <{first_flag.name}>".strip()
    summary = (
        operation.summary or operation.description or f"{operation.verb.title()} {resource.name}"
    )
    return (
        f"{summary}\n\n"
        f"Usage:\n  {usage}\n\n"
        + (f"Options:\n{flag_preview}\n\n" if flag_preview else "")
        + f"Example:\n  {example}\n\n"
        + f"Next:\n  happi {api_name} {resource.name} {operation.verb}"
    )


def _sorted_verbs(operations: list[Operation]) -> list[str]:
    return sorted({operation.verb for operation in operations})


def _render_find(api_name: str, resources: list[Resource], query: str) -> None:
    lowered = query.lower()
    matches: list[str] = []
    for resource in resources:
        if lowered in resource.name.lower():
            matches.append(f"happi {api_name} {resource.name} --help")
        for operation in resource.operations:
            haystacks = [resource.name, operation.verb, operation.summary, operation.description]
            if any(lowered in value.lower() for value in haystacks if value):
                suffix = " <id>" if operation.args else ""
                matches.append(f"happi {api_name} {resource.name} {operation.verb}{suffix}")
    seen: set[str] = set()
    unique_matches: list[str] = []
    for match in matches:
        if match not in seen:
            unique_matches.append(match)
            seen.add(match)
    if not unique_matches:
        render_error(f"No matches for '{query}'")
        return
    typer.echo("Matches:")
    for match in unique_matches[:20]:
        typer.echo(f"  {match}")


_GLOBAL_FLAGS_WITH_VALUE = frozenset({"--output", "-o", "--body"})
_GLOBAL_FLAGS_STANDALONE = frozenset({"--json", "--yaml", "--quiet", "-q", "--yes", "-y"})


def _strip_global_flags(tokens: list[str]) -> tuple[list[str], list[str]]:
    cleaned: list[str] = []
    preserved: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _GLOBAL_FLAGS_STANDALONE:
            preserved.append(tok)
        elif tok in _GLOBAL_FLAGS_WITH_VALUE and i + 1 < len(tokens):
            preserved.append(tok)
            preserved.append(tokens[i + 1])
            i += 1
        else:
            cleaned.append(tok)
        i += 1
    return cleaned, preserved
