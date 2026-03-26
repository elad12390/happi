from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def render_history(rows: list[dict[str, Any]]) -> None:
    if not rows:
        console.print("[dim]No history yet[/dim]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim")
    table.add_column("When")
    table.add_column("API")
    table.add_column("Command")
    table.add_column("Result")
    for row in rows:
        when = datetime.fromtimestamp(float(row["timestamp"]), tz=UTC)
        result = (
            f"✓ {row['primary_id']}"
            if row["success"] and row["primary_id"]
            else ("✓" if row["success"] else "✗")
        )
        table.add_row(
            str(row["id"]),
            when.strftime("%Y-%m-%d %H:%M:%S"),
            str(row["api_name"]),
            str(row["command"]),
            result,
        )
    console.print(table)
