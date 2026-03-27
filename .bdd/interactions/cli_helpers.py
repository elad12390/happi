from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class CLIResult:
    exit_code: int
    stdout: str
    stderr: str


def run_happi_in_env(happi_home: str, *args: str, stdin_text: str | None = None) -> CLIResult:
    env = dict(os.environ)
    env["HAPPI_HOME"] = happi_home
    result = subprocess.run(
        [sys.executable, "-m", "happi", *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        input=stdin_text,
    )
    return CLIResult(result.returncode, result.stdout, result.stderr)
