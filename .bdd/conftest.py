from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from http.server import HTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interactions.test_server import start_test_server


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


@pytest.fixture(scope="session")
def test_server() -> tuple[HTTPServer, str]:
    server, base_url = start_test_server()
    return server, base_url


@pytest.fixture()
def happi_home(tmp_path: Path) -> str:
    home = str(tmp_path / ".happi-test")
    Path(home).mkdir(parents=True, exist_ok=True)
    return home


@pytest.fixture()
def configured_petstore(happi_home: str, test_server: tuple[HTTPServer, str]) -> str:
    _, base_url = test_server
    spec_url = f"{base_url}/openapi.json"
    result = run_happi_in_env(happi_home, "configure", "testapi", "--spec", spec_url)
    assert result.exit_code == 0, f"Configure failed: {result.stderr}"
    return happi_home
