"""Shared pytest-bdd fixtures for happi BDD tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Available fixture specs (real specs only, no synthetic)
AVAILABLE_FIXTURES: dict[str, str] = {
    "petstore": "petstore.json",
    "github": "github.yaml",
    "stripe": "stripe.yaml",
    "spotify": "spotify.yaml",
    "cloudflare": "cloudflare.yaml",
    "httpbin": "httpbin.json",
}

# Fixtures that are referenced in feature files but not available
MISSING_FIXTURES: frozenset[str] = frozenset(
    {
        "sendgrid",
        "directus",
        "dummyjson",
        "fakestore",
    }
)


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def petstore_spec_path() -> Path:
    """Return the path to the Petstore fixture spec."""
    return FIXTURES_DIR / "petstore.json"


@pytest.fixture
def github_spec_path() -> Path:
    """Return the path to the GitHub fixture spec."""
    return FIXTURES_DIR / "github.yaml"


@pytest.fixture
def stripe_spec_path() -> Path:
    """Return the path to the Stripe fixture spec."""
    return FIXTURES_DIR / "stripe.yaml"


@pytest.fixture
def spotify_spec_path() -> Path:
    """Return the path to the Spotify fixture spec."""
    return FIXTURES_DIR / "spotify.yaml"


@pytest.fixture
def cloudflare_spec_path() -> Path:
    """Return the path to the Cloudflare fixture spec."""
    return FIXTURES_DIR / "cloudflare.yaml"


@pytest.fixture
def httpbin_spec_path() -> Path:
    """Return the path to the httpbin fixture spec."""
    return FIXTURES_DIR / "httpbin.json"
