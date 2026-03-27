from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from http.server import HTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interactions.cli_helpers import CLIResult, run_happi_in_env
from interactions.test_server import start_test_server

__all__ = ["CLIResult", "run_happi_in_env"]


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
