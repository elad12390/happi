from __future__ import annotations

import sqlite3
import time
from typing import TYPE_CHECKING, TypedDict

from happi.config.config import happi_home

if TYPE_CHECKING:
    from pathlib import Path


class HistoryEntry(TypedDict):
    id: int
    api_name: str
    timestamp: float
    command: str
    success: bool
    exit_code: int
    resource: str | None
    verb: str | None
    primary_id: str | None
    summary: str | None


def history_db_path() -> Path:
    return happi_home() / "history.db"


def init_history_db() -> None:
    path = history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                command TEXT NOT NULL,
                success INTEGER NOT NULL,
                exit_code INTEGER NOT NULL,
                resource TEXT,
                verb TEXT,
                primary_id TEXT,
                summary TEXT
            )
            """
        )
        conn.commit()


def add_history_entry(
    *,
    api_name: str,
    command: str,
    success: bool,
    exit_code: int,
    resource: str | None,
    verb: str | None,
    primary_id: str | None,
    summary: str | None,
) -> None:
    init_history_db()
    with sqlite3.connect(history_db_path()) as conn:
        conn.execute(
            """
            INSERT INTO history (
                api_name, timestamp, command, success, exit_code,
                resource, verb, primary_id, summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                api_name,
                time.time(),
                command,
                1 if success else 0,
                exit_code,
                resource,
                verb,
                primary_id,
                summary,
            ),
        )
        conn.commit()


def get_history(*, api_name: str | None = None, limit: int = 20) -> list[HistoryEntry]:
    init_history_db()
    query = (
        "SELECT id, api_name, timestamp, command, success, exit_code, "
        "resource, verb, primary_id, summary FROM history"
    )
    params: list[str | int] = []
    if api_name is not None:
        query += " WHERE api_name = ?"
        params.append(api_name)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(history_db_path()) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_entry(row) for row in rows]


def get_history_entry(entry_id: int) -> HistoryEntry | None:
    init_history_db()
    with sqlite3.connect(history_db_path()) as conn:
        row = conn.execute(
            "SELECT id, api_name, timestamp, command, success, exit_code, "
            "resource, verb, primary_id, summary FROM history WHERE id = ?",
            (entry_id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_entry(row)


def _row_to_entry(row: tuple[object, ...]) -> HistoryEntry:
    return {
        "id": int(str(row[0])),
        "api_name": str(row[1]),
        "timestamp": float(str(row[2])),
        "command": str(row[3]),
        "success": bool(row[4]),
        "exit_code": int(str(row[5])),
        "resource": str(row[6]) if row[6] is not None else None,
        "verb": str(row[7]) if row[7] is not None else None,
        "primary_id": str(row[8]) if row[8] is not None else None,
        "summary": str(row[9]) if row[9] is not None else None,
    }
