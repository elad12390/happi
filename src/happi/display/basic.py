from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any, cast

import inflect
import yaml
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from happi.http.client import BinaryFile

console = Console()
err_console = Console(stderr=True)
_inflect_engine = inflect.engine()

_DESTRUCTIVE_VERBS = frozenset({"delete", "remove", "purge", "destroy", "revoke", "cancel"})


def render_explore(api_name: str, resource_rows: list[tuple[str, list[str]]]) -> None:
    console.print(f"[bold]{api_name}[/bold] — choose a resource")
    console.print()
    for resource_name, verbs in resource_rows:
        console.print(f"{resource_name:<20} {', '.join(verbs)}")
    console.print()
    console.print("Try:")
    console.print(f"  happi {api_name} <resource> --help")
    console.print(f"  happi {api_name} <resource> <action> --help")


def render_table(
    payload: object,
    *,
    output_format: str = "table",
    quiet: bool = False,
) -> None:
    if output_format == "json":
        _print_json(payload)
        return
    if output_format == "yaml":
        _print_yaml(payload)
        return

    rows = _extract_rows(payload)
    if not rows:
        if not quiet:
            console.print("[dim]No results[/dim]")
        return

    columns = _choose_columns(rows, wide=output_format == "wide")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim")
    for col in columns:
        table.add_column(col)

    for idx, row in enumerate(rows):
        table.add_row(str(idx), *[str(row.get(col, "")) for col in columns])
    console.print(table)
    if not quiet:
        console.print(f"\n  [dim]{len(rows)} items[/dim]")


def render_card(
    payload: object,
    *,
    api_name: str = "",
    resource_name: str = "",
    output_format: str = "table",
    quiet: bool = False,
) -> None:
    if output_format == "json":
        _print_json(payload)
        return
    if output_format == "yaml":
        _print_yaml(payload)
        return

    if not isinstance(payload, dict):
        console.print(payload)
        return
    data = cast("dict[str, Any]", payload)
    title = _card_title(data)
    console.print(f"[bold]{title}[/bold]")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue
        console.print(f"{key:<16} {value}")

    if not quiet and api_name and resource_name:
        _print_hints_after_show(api_name, resource_name)


def render_success(
    resource: str,
    verb: str,
    payload: object,
    *,
    api_name: str = "",
    output_format: str = "table",
    quiet: bool = False,
) -> None:
    if output_format == "json":
        _print_json(payload)
        return
    if output_format == "yaml":
        _print_yaml(payload)
        return

    identifier = extract_primary_id(payload)
    singular = _inflect_engine.singular_noun(cast("inflect.Word", resource))
    resource_label = str(singular) if singular else resource
    console.print(
        f"[green]✓[/green] {_past_tense(verb)} {resource_label} {identifier or ''}".rstrip()
    )
    if isinstance(payload, dict):
        data = cast("dict[str, Any]", payload)
        for key in list(data)[:4]:
            value = data[key]
            if isinstance(value, (dict, list)):
                continue
            console.print(f"{key:<16} {value}")

    if not quiet and api_name and resource:
        _print_hints_after_mutation(api_name, resource, verb)


def render_confirm(
    resource: str,
    verb: str,
    identifier: str,
    *,
    yes: bool = False,
) -> bool:
    singular = _inflect_engine.singular_noun(cast("inflect.Word", resource))
    resource_label = str(singular) if singular else resource

    if yes:
        return True

    if not sys.stdin.isatty():
        err_console.print(f"[red]✗[/red] Use --yes to confirm {verb} in non-interactive mode")
        return False

    console.print(f"[yellow]⚠[/yellow] {verb.title()} {resource_label} [cyan]{identifier}[/cyan]?")
    response = console.input("[dim]Continue? [y/N] [/dim]")
    return response.strip().lower() in {"y", "yes"}


def render_binary(binary_file: BinaryFile) -> None:
    console.print(
        f"[green]✓[/green] Saved to [cyan]{binary_file.path}[/cyan] "
        f"({binary_file.size} bytes, {binary_file.content_type})"
    )


def render_error(
    message: str,
    details: object | None = None,
    *,
    api_name: str = "",
    resource_name: str = "",
    verb: str = "",
    status_code: int = 0,
) -> None:
    err_console.print(f"[red]✗[/red] {message}")

    if isinstance(details, dict):
        typed_details = cast("dict[str, Any]", details)
        errors = typed_details.get("errors") or typed_details.get("error")
        if isinstance(errors, list):
            typed_errors = cast("list[object]", errors)
            for error_item in typed_errors:
                if isinstance(error_item, dict):
                    typed_error = cast("dict[str, Any]", error_item)
                    field = typed_error.get("field", "")
                    msg = typed_error.get("message", typed_error.get("msg", ""))
                    err_console.print(
                        f"  [dim]•[/dim] {field}: {msg}" if field else f"  [dim]•[/dim] {msg}"
                    )
                else:
                    err_console.print(f"  [dim]•[/dim] {error_item}")
        elif isinstance(errors, str):
            err_console.print(f"  {errors}")
        else:
            message_field = typed_details.get("message") or typed_details.get("detail")
            if message_field:
                err_console.print(f"  {message_field}")
    elif details is not None:
        err_console.print(f"  {details}")

    if status_code == 401 and api_name:
        err_console.print()
        err_console.print("Run:")
        err_console.print(f"  happi auth set {api_name} --type bearer --token <TOKEN>")
        err_console.print(f"  happi auth show {api_name}")
    elif status_code == 404 and api_name and resource_name:
        err_console.print()
        err_console.print("Try:")
        err_console.print(f"  happi {api_name} {resource_name} --help")
    elif status_code == 422 and api_name and resource_name and verb:
        err_console.print()
        err_console.print("Check required fields:")
        err_console.print(f"  happi {api_name} {resource_name} {verb} --help")

    err_console.print()
    err_console.print("[dim]Run with --debug for raw HTTP details[/dim]")


def is_destructive(verb: str) -> bool:
    return verb in _DESTRUCTIVE_VERBS


def _print_hints_after_show(api_name: str, resource_name: str) -> None:
    console.print()
    console.print(f"[dim]↳ happi {api_name} {resource_name} update _[/dim]")


def _print_hints_after_mutation(api_name: str, resource_name: str, verb: str) -> None:
    console.print()
    if verb != "delete":
        console.print(f"[dim]↳ happi {api_name} {resource_name} show _[/dim]")


def _print_json(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


def _print_yaml(payload: object) -> None:
    sys.stdout.write(yaml.safe_dump(payload, sort_keys=False, default_flow_style=False))


def _extract_rows(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        typed_payload = cast("list[object]", payload)
        if all(isinstance(item, dict) for item in typed_payload):
            return [cast("dict[str, Any]", item) for item in typed_payload]
    if isinstance(payload, dict):
        data = cast("dict[str, Any]", payload)
        for value in data.values():
            if isinstance(value, list):
                typed_value = cast("list[object]", value)
                if all(isinstance(item, dict) for item in typed_value):
                    return [cast("dict[str, Any]", item) for item in typed_value]
    return []


def _choose_columns(rows: list[dict[str, Any]], *, wide: bool = False) -> list[str]:
    first = rows[0]
    if wide:
        return [k for k in first if not isinstance(first[k], (dict, list))]
    priority = ["id", "identifier", "name", "title", "status"]
    chosen = [col for col in priority if col in first]
    for key in first:
        if key not in chosen and not isinstance(first[key], (dict, list)):
            chosen.append(key)
        if len(chosen) >= 5:
            break
    return chosen


def _card_title(data: dict[str, Any]) -> str:
    identifier = extract_primary_id(data)
    kind = data.get("type") or data.get("resource") or "Resource"
    return f"{kind} {identifier}" if identifier else str(kind)


def extract_primary_id(payload: object) -> str | None:
    if isinstance(payload, dict):
        data = cast("dict[str, Any]", payload)
        for key in ("id", "identifier", "slug"):
            value = data.get(key)
            if value is not None:
                return str(value)
    return None


def _past_tense(verb: str) -> str:
    irregular = {
        "find": "Found",
        "scrape": "Scraped",
        "show": "Showed",
    }
    if verb in irregular:
        return irregular[verb]
    if verb.endswith("e"):
        return f"{verb.title()}d"
    return f"{verb.title()}ed"
