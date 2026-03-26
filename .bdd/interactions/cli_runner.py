from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def _empty_str_list() -> list[str]:
    return []


@dataclass
class CLIResult:
    exit_code: int
    stdout: str
    stderr: str
    command: list[str] = field(default_factory=_empty_str_list)


def run_happi(*args: str, timeout: int = 60, env: Mapping[str, str] | None = None) -> CLIResult:
    cmd = [sys.executable, "-m", "happi", *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=dict(env) if env is not None else None,
    )
    return CLIResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        command=cmd,
    )
