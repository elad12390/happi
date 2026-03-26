from __future__ import annotations

import sys
from typing import Any, cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from happi.config.config import (
    get_config_value,
    list_profiles,
    mask_secret,
    set_config_value,
    unset_config_value,
    upsert_profile,
)
from happi.display.history import render_history
from happi.engine.history import get_history, get_history_entry
from happi.engine.tree import register_profile_apps
from happi.log import configure_logging
from happi.spec.lap import LapResolutionError, resolve_from_lap
from happi.spec.loader import load_spec

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="happi",
    help="Turn any OpenAPI spec into a human-friendly CLI.",
    epilog=(
        "\b\n"
        "Use an API name, then a resource, then an action:\n"
        "  happi <api> <resource> <action>\n\n"
        "Start here:\n"
        "  happi configure <name>\n\n"
        "Examples:\n"
        "  happi configure petstore\n"
        "  happi configure billing --spec ./openapi.yaml\n"
        "  happi petstore pet list\n\n"
        "Next:\n"
        "  happi configure petstore"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)
config_app = typer.Typer(help="Inspect and modify happi configuration.", no_args_is_help=True)
auth_app = typer.Typer(help="Manage API authentication.", no_args_is_help=True)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show info-level logs while loading specs and building commands",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show debug logs and raw HTTP/spec resolution details",
    ),
) -> None:
    configure_logging(verbose=verbose, debug=debug)


@app.command(
    epilog=(
        "\b\n"
        "Examples:\n"
        "  happi configure petstore\n"
        "  happi configure billing --spec ./openapi.yaml\n"
        "  happi configure billing --spec https://example.com/openapi.json --server https://api.example.com\n\n"
        "Next:\n"
        "  happi NAME explore"
    )
)
def configure(
    name: str = typer.Argument(
        help="Short local name you will use in commands, e.g. petstore or stripe-live"
    ),
    spec: str | None = typer.Option(
        None,
        "--spec",
        help="API description file or URL. If omitted, happi will try LAP first.",
    ),
    server: str | None = typer.Option(
        None,
        "--server",
        help="Base URL to use instead of the server picked from the spec",
    ),
) -> None:
    """Add an API and give it a short local name.

    If --spec is omitted, happi tries the LAP registry first.
    Authentication can be added later.
    """
    from happi.log import get_logger

    log = get_logger("config")
    log.info("Configuring API profile: %s", name)

    resolved_spec = spec
    base_url = server
    source_kind = "manual"

    if resolved_spec is None:
        try:
            lap_entry = resolve_from_lap(name)
            resolved_spec = lap_entry["spec_url"]
            if base_url is None:
                base_url = lap_entry.get("base_url") or None
            source_kind = "lap"
            log.info("Resolved spec from LAP: %s", resolved_spec)
        except LapResolutionError:
            err_console.print(f"[red]✗[/red] Couldn't find an API spec for [cyan]{name}[/cyan]")
            err_console.print()
            err_console.print("Try one of:")
            err_console.print(f"  happi configure {name} --spec ./openapi.yaml")
            err_console.print(f"  happi configure {name} --spec https://example.com/openapi.json")
            raise typer.Exit(1) from None

    assert resolved_spec is not None
    loaded_spec, content_hash = load_spec(resolved_spec)

    if base_url is None:
        base_url = _pick_base_url(loaded_spec, resolved_spec)

    profile = {
        "name": name,
        "base_url": base_url or "",
        "spec": {
            "source": source_kind,
            "url": resolved_spec,
            "current_hash": content_hash,
        },
    }
    upsert_profile(name, profile)

    log.info("Spec source: %s", resolved_spec)
    if base_url:
        log.info("Base URL: %s", base_url)

    console.print(f"[green]✓[/green] Configured [cyan]{name}[/cyan]")
    console.print(f"  Spec: {resolved_spec}")
    if base_url:
        console.print(f"  Base URL: {base_url}")


@app.command()
def history(limit: int = typer.Option(20, help="Maximum number of rows to show")) -> None:
    """Show recent command history across all configured APIs."""
    render_history(get_history(limit=limit))


@app.command()
def redo(
    entry_id: int = typer.Argument(help="History entry ID to re-run"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation for destructive commands"
    ),
) -> None:
    """Re-run a command from history."""
    import shlex
    import subprocess
    import sys as _sys

    entry = get_history_entry(entry_id)
    if entry is None:
        err_console.print(f"[red]✗[/red] No history entry with ID {entry_id}")
        raise typer.Exit(1)

    command_str = str(entry["command"])
    verb = str(entry.get("verb", ""))

    destructive_verbs = {"delete", "remove", "purge", "destroy", "revoke", "cancel"}
    if verb in destructive_verbs and not yes:
        console.print("[yellow]⚠[/yellow] This will re-run:")
        console.print(f"  {command_str}")
        if not _sys.stdin.isatty():
            err_console.print("[red]✗[/red] Use --yes to confirm redo in non-interactive mode")
            raise typer.Exit(1)
        response = console.input("[dim]Continue? [y/N] [/dim]")
        if response.strip().lower() not in {"y", "yes"}:
            raise typer.Exit(0)

    parts = shlex.split(command_str)
    if parts and parts[0] == "happi":
        parts = parts[1:]
    result = subprocess.run(  # noqa: S603
        [_sys.executable, "-m", "happi", *parts],
        check=False,
    )
    raise typer.Exit(result.returncode)


@config_app.command("list")
def config_list() -> None:
    """List configured API profile names."""
    profiles = list_profiles()
    if not profiles:
        console.print("[dim]No configured APIs[/dim]")
        return
    for name in sorted(profiles):
        console.print(name)


@config_app.command("get")
def config_get(
    path: str = typer.Argument(help="Config path, e.g. apis.stripe.base_url"),
    reveal: bool = typer.Option(False, "--reveal", help="Show raw secret values"),
) -> None:
    """Get a config value by dotted path."""
    value = get_config_value(path)
    if value is None:
        err_console.print(f"[red]✗[/red] No config value at {path}")
        raise typer.Exit(1)
    if _looks_secret(path):
        console.print(mask_secret(value, reveal=reveal))
        return
    console.print(value)


@config_app.command("set")
def config_set(
    path: str = typer.Argument(help="Config path, e.g. apis.stripe.base_url"),
    value: str = typer.Argument(help="Value to store"),
) -> None:
    """Set a config value by dotted path."""
    set_config_value(path, value)
    console.print(f"[green]✓[/green] Set {path}")


@config_app.command("unset")
def config_unset(path: str = typer.Argument(help="Config path to remove")) -> None:
    """Remove a config value by dotted path."""
    removed = unset_config_value(path)
    if not removed:
        err_console.print(f"[red]✗[/red] No config value at {path}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] Removed {path}")


@config_app.command("show")
def config_show(
    name: str | None = typer.Argument(None, help="Optional API profile name"),
    reveal: bool = typer.Option(False, "--reveal", help="Show raw secret values"),
) -> None:
    """Show config for one API profile or all profiles."""
    profiles = list_profiles()
    rows = (
        [(name, profiles[name]) for name in sorted(profiles)]
        if name is None
        else [(name, profiles.get(name))]
    )
    for profile_name, profile in rows:
        if not isinstance(profile, dict):
            err_console.print(f"[red]✗[/red] Unknown profile: {profile_name}")
            raise typer.Exit(1)
        console.print(f"[bold]{profile_name}[/bold]")
        typed_profile = cast("dict[str, Any]", profile)
        for key, value in typed_profile.items():
            if key == "auth" and isinstance(value, dict):
                console.print("auth")
                typed_auth = cast("dict[str, Any]", value)
                for auth_key, auth_value in typed_auth.items():
                    rendered = (
                        mask_secret(auth_value, reveal=reveal)
                        if _looks_secret(auth_key)
                        else str(auth_value)
                    )
                    console.print(f"  {auth_key:<14} {rendered}")
                continue
            console.print(f"{key:<16} {value}")
        if len(rows) > 1:
            console.print()


@auth_app.command("show")
def auth_show(
    name: str = typer.Argument(help="API profile name"),
    reveal: bool = typer.Option(False, "--reveal", help="Show raw secret values"),
) -> None:
    """Show auth configuration for one API."""
    raw_profile = list_profiles().get(name)
    if not isinstance(raw_profile, dict):
        err_console.print(f"[red]✗[/red] Unknown profile: {name}")
        raise typer.Exit(1)
    profile = cast("dict[str, Any]", raw_profile)
    auth: object = profile.get("auth")
    if not isinstance(auth, dict):
        console.print("[dim]No auth configured[/dim]")
        return
    console.print(f"[bold]{name}[/bold]")
    for key, value in cast("dict[str, Any]", auth).items():
        rendered = mask_secret(value, reveal=reveal) if _looks_secret(key) else str(value)
        console.print(f"{key:<16} {rendered}")


@auth_app.command("set")
def auth_set(
    name: str = typer.Argument(help="API profile name"),
    auth_type: str = typer.Option(..., "--type", help="Auth type: api-key or bearer"),
    token: str | None = typer.Option(None, "--token", help="Bearer token"),
    key_value: str | None = typer.Option(None, "--value", help="API key value"),
    header: str | None = typer.Option(None, "--header", help="Header name for API key auth"),
    query: str | None = typer.Option(None, "--query", help="Query parameter name for API key auth"),
) -> None:
    """Set auth for one API profile."""
    if auth_type not in {"api-key", "bearer"}:
        err_console.print("[red]✗[/red] --type must be 'api-key' or 'bearer'")
        raise typer.Exit(1)

    auth: dict[str, Any] = {"type": auth_type}
    if auth_type == "bearer":
        if token is None:
            err_console.print("[red]✗[/red] --token is required for bearer auth")
            raise typer.Exit(1)
        auth["token"] = token
    else:
        if key_value is None:
            err_console.print("[red]✗[/red] --value is required for api-key auth")
            raise typer.Exit(1)
        if header is None and query is None:
            err_console.print("[red]✗[/red] api-key auth requires either --header or --query")
            raise typer.Exit(1)
        auth["value"] = key_value
        if header is not None:
            auth["header"] = header
        if query is not None:
            auth["query"] = query

    set_config_value(f"apis.{name}.auth", auth)
    console.print(f"[green]✓[/green] Set auth for [cyan]{name}[/cyan]")


@auth_app.command("unset")
def auth_unset(name: str = typer.Argument(help="API profile name")) -> None:
    """Remove auth from one API profile."""
    removed = unset_config_value(f"apis.{name}.auth")
    if not removed:
        err_console.print(f"[red]✗[/red] No auth configured for {name}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] Removed auth for [cyan]{name}[/cyan]")


@auth_app.command("login")
def auth_login(
    name: str = typer.Argument(help="API profile name"),
    authorize_url: str = typer.Option(..., "--authorize-url", help="OAuth2 authorize endpoint"),
    token_url: str = typer.Option(..., "--token-url", help="OAuth2 token endpoint"),
    client_id: str = typer.Option(..., "--client-id", help="OAuth2 client ID"),
    scopes: str = typer.Option("", "--scopes", help="Space-separated OAuth2 scopes"),
    manual: bool = typer.Option(
        False, "--manual", help="Manual copy-paste mode instead of browser"
    ),
) -> None:
    """Login via OAuth2 (browser-first, with manual fallback)."""
    from happi.config.auth import oauth_login

    success = oauth_login(
        name,
        authorize_url=authorize_url,
        token_url=token_url,
        client_id=client_id,
        scopes=scopes,
        manual=manual,
    )
    if not success:
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show happi version."""
    from happi import __version__

    console.print(f"happi [cyan]{__version__}[/cyan]")


app.add_typer(config_app, name="config")
app.add_typer(auth_app, name="auth")


def _print_root_help() -> None:
    console.print("[bold]happi[/bold] — turn an API into commands you can read")
    console.print()
    console.print("[bold]Command shape[/bold]")
    console.print("  happi <api> <resource> <action>")
    console.print()
    console.print(
        Panel.fit(
            "[bold]Start here[/bold]\nhappi configure <name>",
            border_style="cyan",
        )
    )
    console.print()

    examples = Table(show_header=True, header_style="bold")
    examples.add_column("Examples")
    examples.add_row("happi configure petstore")
    examples.add_row("happi configure billing --spec ./openapi.yaml")
    examples.add_row("happi petstore pet list")
    console.print(examples)
    console.print()

    commands = Table(show_header=True, header_style="bold")
    commands.add_column("Command")
    commands.add_column("What it does")
    commands.add_row("configure", "Add an API and give it a short local name")
    commands.add_row("version", "Show happi version")
    console.print(commands)
    console.print()

    options = Table(show_header=True, header_style="bold")
    options.add_column("Option")
    options.add_column("What it does")
    options.add_row(
        "-v, --verbose", "Show info-level logs while loading specs and building commands"
    )
    options.add_row("--debug", "Show debug logs and raw HTTP/spec resolution details")
    console.print(options)
    console.print()
    console.print("[bold]Next[/bold]")
    console.print("  happi configure petstore")


def _print_configure_help() -> None:
    console.print("[bold]happi configure[/bold] — add an API and give it a short local name")
    console.print()
    console.print("Use the profile name later in commands like:")
    console.print("  happi <name> <resource> <action>")
    console.print()
    console.print("If [bold]--spec[/bold] is omitted, happi tries the LAP registry first.")
    console.print("Authentication can be added later.")
    console.print()

    args = Table(show_header=True, header_style="bold")
    args.add_column("Argument")
    args.add_column("What it means")
    args.add_row("NAME", "Short local name, e.g. petstore or stripe-live")
    console.print(args)
    console.print()

    options = Table(show_header=True, header_style="bold")
    options.add_column("Option")
    options.add_column("What it does")
    options.add_row("--spec TEXT", "API description file or URL")
    options.add_row("--server TEXT", "Base URL to use instead of the server picked from the spec")
    console.print(options)
    console.print()

    examples = Table(show_header=True, header_style="bold")
    examples.add_column("Examples")
    examples.add_row("happi configure petstore")
    examples.add_row("happi configure billing --spec ./openapi.yaml")
    examples.add_row(
        "happi configure billing --spec https://example.com/openapi.json --server https://api.example.com"
    )
    console.print(examples)
    console.print()
    console.print("[bold]Next[/bold]")
    console.print("  happi NAME explore")


def app_entry() -> None:
    argv = sys.argv[1:]
    if argv == ["--help"]:
        _print_root_help()
        return
    if len(argv) == 2 and argv[0] == "configure" and argv[1] == "--help":
        _print_configure_help()
        return
    register_profile_apps(app)
    app()


def _looks_secret(path: str) -> bool:
    lowered = path.lower()
    return any(word in lowered for word in ("token", "secret", "password", "key"))


def _pick_base_url(spec: dict[str, Any], spec_source: str) -> str | None:
    from urllib.parse import urlparse

    servers = spec.get("servers", [])
    if not isinstance(servers, list):
        return None

    raw_servers = cast("list[object]", servers)
    candidates: list[str] = []
    for raw_item in raw_servers:
        if isinstance(raw_item, dict):
            url = cast("dict[str, Any]", raw_item).get("url")
            if isinstance(url, str):
                candidates.append(url)

    if not candidates:
        return None

    resolved: list[str] = []
    for candidate in candidates:
        if candidate.startswith(("http://", "https://")):
            resolved.append(candidate)
        elif spec_source.startswith(("http://", "https://")):
            parsed = urlparse(spec_source)
            resolved.append(f"{parsed.scheme}://{parsed.netloc}{candidate}")
        else:
            resolved.append(candidate)

    for url in resolved:
        lowered = url.lower()
        if url.startswith("https://") and all(
            x not in lowered for x in ("staging", "sandbox", "localhost", "127.0.0.1", "dev")
        ):
            return url

    for url in resolved:
        if url.startswith("https://"):
            return url

    return resolved[0] if resolved else None
