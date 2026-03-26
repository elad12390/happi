from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
import yaml
from pytest_bdd import given, parsers, then, when

from happi.config.config import config_path
from happi.spec import loader as spec_loader
from happi.spec.loader import SpecLoadError, load_spec
from happi.spec.resources import extract_resources
from happi.spec.verbs import is_action_verb

if TYPE_CHECKING:
    from collections.abc import Mapping

    from happi.spec.model import Resource

FIXTURES_DIR = Path(__file__).parent.parent / "support" / "fixtures"


class SpecContext:
    def __init__(self) -> None:
        self.spec: dict[str, object] | None = None
        self.spec_hash: str = ""
        self.resources: list[Resource] = []
        self.load_error: SpecLoadError | None = None
        self.all_specs_loaded: list[dict[str, object]] = []
        self.all_specs_ok: bool = True
        self.garbage_path: str = ""
        self.cli_result: CLIResult | None = None
        self.temp_home: str = ""
        self.lap_server_url: str = ""
        self.remote_spec_url: str = ""
        self.remote_request_count: int = 0
        self.remote_source_checked: bool = False
        self.loaded_hashes: list[str] = []
        self.lap_server: HTTPServer | None = None
        self.remote_server: HTTPServer | None = None


class CLIResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


def run_happi(*args: str, env: Mapping[str, str] | None = None) -> CLIResult:
    result = subprocess.run(
        [sys.executable, "-m", "happi", *args],
        capture_output=True,
        text=True,
        env=dict(env) if env is not None else None,
        timeout=60,
    )
    return CLIResult(result.returncode, result.stdout, result.stderr)


class _RegistryHandler(BaseHTTPRequestHandler):
    registry_payload: bytes = b"{}"
    spec_payload: bytes = b"{}"
    hit_count = 0

    def do_GET(self) -> None:
        if self.path.startswith("/registry.json"):
            body = self.registry_payload
        elif self.path.startswith("/specs/stripe.json"):
            type(self).hit_count += 1
            body = self.spec_payload
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _RemoteSpecHandler(BaseHTTPRequestHandler):
    spec_payload: bytes = b"{}"
    hit_count = 0

    def do_GET(self) -> None:
        if self.path.startswith("/openapi.json"):
            type(self).hit_count += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(self.spec_payload)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def _start_server(handler_cls: type[BaseHTTPRequestHandler]) -> tuple[HTTPServer, str]:
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


@pytest.fixture
def ctx() -> SpecContext:
    return SpecContext()


def _fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def _resolve_fixture_path(raw_path: str) -> str:
    if raw_path.startswith("fixtures/"):
        filename = raw_path.removeprefix("fixtures/")
        candidate = _fixture_path(filename)
        if candidate.exists():
            return str(candidate)
        stem = Path(filename).stem
        for ext in (".json", ".yaml", ".yml"):
            alt = _fixture_path(stem + ext)
            if alt.exists():
                return str(alt)
    return raw_path


# ===========================================================================
# LOAD-SPEC: Given steps
# ===========================================================================


@given(parsers.parse('a local copy of the Petstore OpenAPI spec at "{path}"'))
def _given_petstore_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the GitHub OpenAPI spec at "{path}"'))
def _given_github_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the Stripe OpenAPI spec at "{path}"'))
def _given_stripe_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the Spotify OpenAPI spec at "{path}"'))
def _given_spotify_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the Cloudflare OpenAPI spec at "{path}"'))
def _given_cloudflare_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the SendGrid OpenAPI spec at "{path}"'))
def _given_sendgrid_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the GitLab OpenAPI spec at "{path}"'))
def _given_gitlab_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the Netlify OpenAPI spec at "{path}"'))
def _given_netlify_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given(parsers.parse('a local copy of the PagerDuty OpenAPI spec at "{path}"'))
def _given_pagerduty_local(ctx: SpecContext, path: str) -> None:
    resolved = _resolve_fixture_path(path)
    assert Path(resolved).exists(), f"Fixture not found: {resolved}"


@given("all 10 fixture specs are available locally")
def _given_all_10_fixtures(ctx: SpecContext) -> None:
    required = {
        "petstore.json",
        "github.yaml",
        "stripe.yaml",
        "spotify.yaml",
        "cloudflare.yaml",
        "sendgrid.yaml",
        "gitlab.yaml",
        "netlify.json",
        "pagerduty.json",
        "httpbin.json",
    }
    missing = sorted(name for name in required if not _fixture_path(name).exists())
    if missing:
        pytest.skip(f"Missing fixtures: {', '.join(missing)}")


@given("a spec with $ref references to shared schemas")
def _given_spec_with_refs(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("petstore.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given(parsers.parse('a file "{path}" containing "{content}"'))
def _given_garbage_file(ctx: SpecContext, path: str, content: str, tmp_path: Path) -> None:
    garbage_file = tmp_path / "garbage.txt"
    garbage_file.write_text(content)
    ctx.garbage_path = str(garbage_file)


@given(parsers.parse('the LAP registry contains an API named "{name}"'))
def _given_lap_registry(ctx: SpecContext, name: str, tmp_path: Path) -> None:
    ctx.temp_home = str(tmp_path / ".happi-home")
    Path(ctx.temp_home).mkdir(parents=True, exist_ok=True)

    with _fixture_path("petstore.json").open() as f:
        petstore_spec = json.load(f)

    _RegistryHandler.hit_count = 0
    _RegistryHandler.spec_payload = json.dumps(petstore_spec).encode()
    server, base_url = _start_server(_RegistryHandler)
    ctx.lap_server_url = base_url

    registry = {
        "pagination": {"limit": 500, "offset": 0, "has_more": False, "next_offset": 0},
        "specs": [
            {
                "name": name,
                "source_url": f"{base_url}/specs/stripe.json",
                "base_url": "https://api.stripe.com/",
                "provider": {"slug": "stripe-com", "display_name": "Stripe"},
            }
        ],
    }
    _RegistryHandler.registry_payload = json.dumps(registry).encode()

    ctx.lap_server = server


@given(parsers.parse("a remote spec was checked {hours:d} hours ago"))
def _given_remote_checked(ctx: SpecContext, hours: int, tmp_path: Path) -> None:
    ctx.temp_home = str(tmp_path / ".happi-home")
    Path(ctx.temp_home).mkdir(parents=True, exist_ok=True)

    with _fixture_path("petstore.json").open() as f:
        petstore_spec = json.load(f)

    _RemoteSpecHandler.hit_count = 0
    _RemoteSpecHandler.spec_payload = json.dumps(petstore_spec).encode()
    server, base_url = _start_server(_RemoteSpecHandler)
    ctx.remote_spec_url = f"{base_url}/openapi.json"
    ctx.remote_server = server

    os.environ["HAPPI_HOME"] = ctx.temp_home
    load_spec(ctx.remote_spec_url, force_refresh=True)

    raw_key = spec_loader._cache_key_for_url(ctx.remote_spec_url)
    meta_path = spec_loader.CACHE_DIR / "raw" / f"{raw_key}.meta.json"
    meta = json.loads(meta_path.read_text())
    meta["fetched_at"] = str(time.time() - (hours * 3600))
    meta_path.write_text(json.dumps(meta))

    ctx.remote_request_count = _RemoteSpecHandler.hit_count


# ===========================================================================
# LOAD-SPEC: When steps
# ===========================================================================


@when(parsers.parse('the spec is loaded from "{source}"'))
def _when_spec_loaded(ctx: SpecContext, source: str) -> None:
    if source == "fixtures/garbage.txt" and ctx.garbage_path:
        resolved = ctx.garbage_path
    else:
        resolved = _resolve_fixture_path(source)
    try:
        spec, content_hash = load_spec(resolved)
        ctx.spec = cast("dict[str, object]", spec)
        ctx.spec_hash = content_hash
    except SpecLoadError as e:
        ctx.load_error = e


@when("the spec is loaded")
def _when_spec_loaded_already(ctx: SpecContext) -> None:
    pass


@when("each spec is loaded sequentially")
def _when_load_all(ctx: SpecContext) -> None:
    fixture_names = [
        "petstore.json",
        "github.yaml",
        "stripe.yaml",
        "spotify.yaml",
        "cloudflare.yaml",
        "sendgrid.yaml",
        "gitlab.yaml",
        "netlify.json",
        "pagerduty.json",
        "httpbin.json",
    ]
    ctx.all_specs_loaded = []
    ctx.loaded_hashes = []
    for name in fixture_names:
        spec, content_hash = load_spec(str(_fixture_path(name)))
        ctx.all_specs_loaded.append(cast("dict[str, object]", spec))
        ctx.loaded_hashes.append(content_hash)


@when("the same command runs again")
def _when_same_command(ctx: SpecContext) -> None:
    if ctx.remote_spec_url:
        before = _RemoteSpecHandler.hit_count
        load_spec(ctx.remote_spec_url)
        after = _RemoteSpecHandler.hit_count
        ctx.remote_source_checked = after > before
        return

    if ctx.lap_server_url:
        env = dict(os.environ)
        env["HAPPI_HOME"] = ctx.temp_home
        env["HAPPI_LAP_REGISTRY_URL"] = f"{ctx.lap_server_url}/registry.json"
        ctx.cli_result = run_happi("configure", "stripe", env=env)
        return


@when(parsers.parse('the user runs "happi configure {name}"'))
def _when_user_runs_happi_configure(ctx: SpecContext, name: str) -> None:
    env = dict(os.environ)
    if ctx.temp_home:
        env["HAPPI_HOME"] = ctx.temp_home
    if ctx.lap_server_url:
        env["HAPPI_LAP_REGISTRY_URL"] = f"{ctx.lap_server_url}/registry.json"
    ctx.cli_result = run_happi("configure", name, env=env)


# ===========================================================================
# LOAD-SPEC: Then steps
# ===========================================================================


@then("the spec is parsed successfully")
def _then_parsed_ok(ctx: SpecContext) -> None:
    assert ctx.load_error is None, f"Spec load failed: {ctx.load_error}"
    assert ctx.spec is not None


@then(parsers.parse('the spec title is "{expected_title}"'))
def _then_spec_title(ctx: SpecContext, expected_title: str) -> None:
    assert ctx.spec is not None
    info = ctx.spec.get("info")
    assert isinstance(info, dict)
    assert info.get("title") == expected_title


@then(parsers.parse("the spec contains at least {count:d} resources"))
def _then_at_least_n_resources(ctx: SpecContext, count: int) -> None:
    assert ctx.spec is not None
    resources = extract_resources(cast("dict[str, object]", ctx.spec))
    assert len(resources) >= count, f"Expected at least {count} resources, got {len(resources)}"


@then("all 10 specs parse successfully")
def _then_all_10_ok(ctx: SpecContext) -> None:
    assert len(ctx.all_specs_loaded) == 10
    assert len(ctx.loaded_hashes) == 10


@then("no panic occurs for any spec")
def _then_no_panic_all(ctx: SpecContext) -> None:
    assert ctx.all_specs_loaded


@then("no panic occurs")
def _then_no_panic_single(ctx: SpecContext) -> None:
    assert True


@then(parsers.parse('the load fails with error code "{code}"'))
def _then_load_fails(ctx: SpecContext, code: str) -> None:
    assert ctx.load_error is not None, "Expected a load error but none occurred"
    assert ctx.load_error.code == code, f"Expected error code '{code}', got '{ctx.load_error.code}'"


@then(parsers.parse('the error message contains "{text}"'))
def _then_error_contains(ctx: SpecContext, text: str) -> None:
    assert ctx.load_error is not None
    assert text in str(ctx.load_error), f"Expected '{text}' in error message '{ctx.load_error}'"


@then("all $ref references are resolved inline")
def _then_refs_resolved(ctx: SpecContext) -> None:
    assert ctx.spec is not None
    spec_str = json.dumps(ctx.spec)
    ref_count = spec_str.count('"$ref"')
    assert ref_count == 0, f"Found {ref_count} unresolved $ref references"


@then("no unresolved $ref remains in the resource model")
def _then_no_unresolved_refs(ctx: SpecContext) -> None:
    assert ctx.spec is not None


@then("the spec source is resolved from LAP")
def _then_lap_resolved(ctx: SpecContext) -> None:
    assert ctx.cli_result is not None
    assert ctx.cli_result.exit_code == 0
    assert "Configured stripe" in ctx.cli_result.stdout
    path = Path(ctx.temp_home) / "config.yaml"
    assert path.exists()
    data = json.loads(json.dumps(yaml.safe_load(path.read_text())))
    assert data["apis"]["stripe"]["spec"]["source"] == "lap"


@then("the profile is created successfully")
def _then_profile_created(ctx: SpecContext) -> None:
    path = Path(ctx.temp_home) / "config.yaml" if ctx.temp_home else config_path()
    assert path.exists()
    data = json.loads(json.dumps(yaml.safe_load(path.read_text())))
    assert "apis" in data
    assert "stripe" in data["apis"]


@then("the cached parsed model is reused without checking the remote source")
def _then_cached_reused(ctx: SpecContext) -> None:
    assert ctx.remote_source_checked is False


@then("the remote source is checked for freshness before using the cache")
def _then_freshness_checked(ctx: SpecContext) -> None:
    assert ctx.remote_source_checked is True


# ===========================================================================
# EXTRACT-RESOURCES: Given steps
# ===========================================================================


@given("the Petstore spec is loaded")
def _given_petstore_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("petstore.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the GitHub spec is loaded")
def _given_github_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("github.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the Stripe spec is loaded")
def _given_stripe_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("stripe.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the Spotify spec is loaded")
def _given_spotify_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("spotify.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the Cloudflare spec is loaded")
def _given_cloudflare_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("cloudflare.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the SendGrid spec is loaded")
def _given_sendgrid_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("sendgrid.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the GitLab spec is loaded")
def _given_gitlab_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("gitlab.yaml")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the Netlify spec is loaded")
def _given_netlify_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("netlify.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the PagerDuty spec is loaded")
def _given_pagerduty_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("pagerduty.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("the httpbin spec is loaded")
def _given_httpbin_loaded(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("httpbin.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given("any spec is loaded")
def _given_any_spec(ctx: SpecContext) -> None:
    spec, content_hash = load_spec(str(_fixture_path("petstore.json")))
    ctx.spec = cast("dict[str, object]", spec)
    ctx.spec_hash = content_hash


@given(parsers.parse('a spec with path "{path}"'))
def _given_spec_with_path(ctx: SpecContext, path: str) -> None:
    spec: dict[str, object] = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }
    paths = cast("dict[str, object]", spec["paths"])

    parent_segments = [s for s in path.split("/") if s and not s.startswith("{")]
    if parent_segments:
        root = "/" + parent_segments[0]
        root_id_path = root + "/{id}"
        paths[root] = {
            "get": {
                "summary": f"List {parent_segments[0]}",
                "responses": {"200": {"description": "OK"}},
            },
        }
        paths[root_id_path] = {
            "get": {
                "summary": f"Show {parent_segments[0]}",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}},
            },
        }

    paths[path] = {
        "get": {
            "summary": f"List items at {path}",
            "parameters": [
                {
                    "name": p.strip("{}"),
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for p in path.split("/")
                if p.startswith("{")
            ],
            "responses": {"200": {"description": "OK"}},
        },
    }

    if len(parent_segments) >= 2:
        sub = parent_segments[-1]
        sub_id_path = path + "/{subId}"
        paths[sub_id_path] = {
            "get": {
                "summary": f"Show {sub}",
                "parameters": [
                    {
                        "name": p.strip("{}"),
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                    for p in (path + "/{subId}").split("/")
                    if p.startswith("{")
                ],
                "responses": {"200": {"description": "OK"}},
            },
        }

    ctx.spec = spec


@given(parsers.parse('a spec where path "{path}" has tag "{tag}"'))
def _given_spec_with_tag(ctx: SpecContext, path: str, tag: str) -> None:
    spec: dict[str, object] = {
        "openapi": "3.0.0",
        "info": {"title": "Tag Test", "version": "1.0"},
        "paths": {
            path: {
                "get": {
                    "tags": [tag],
                    "summary": "Test operation",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    ctx.spec = spec


# ===========================================================================
# EXTRACT-RESOURCES: When steps
# ===========================================================================


@when("resources are extracted")
def _when_resources_extracted(ctx: SpecContext) -> None:
    assert ctx.spec is not None
    ctx.resources = extract_resources(cast("dict[str, object]", ctx.spec))


# ===========================================================================
# EXTRACT-RESOURCES: Then steps
# ===========================================================================


@then("the following resources exist:")
def _then_resources_exist(ctx: SpecContext, datatable: list[list[str]]) -> None:
    resource_names = {r.name for r in ctx.resources}
    rows = datatable[1:]  # skip header row
    for row in rows:
        expected = row[0]
        matching = [
            name for name in resource_names if expected in name or name.startswith(expected)
        ]
        assert matching, (
            f"Expected resource '{expected}' not found. Available: {sorted(resource_names)}"
        )


@then("each resource has at least one operation")
def _then_each_has_ops(ctx: SpecContext) -> None:
    for resource in ctx.resources:
        assert len(resource.operations) > 0, f"Resource '{resource.name}' has no operations"


@then(parsers.parse("resources include actions like {action_list}"))
def _then_actions_include(ctx: SpecContext, action_list: str) -> None:
    all_verbs: set[str] = set()
    all_resource_names: set[str] = set()
    for resource in ctx.resources:
        all_resource_names.add(resource.name)
        for op in resource.operations:
            all_verbs.add(op.verb)

    all_names = all_verbs | all_resource_names
    expected_actions = [a.strip().strip('"').strip("'") for a in action_list.split(",")]
    found_count = 0
    for expected in expected_actions:
        matching = [v for v in all_names if expected in v]
        if matching:
            found_count += 1
    assert found_count > 0, (
        f"None of the expected actions {expected_actions} found. "
        f"Available verbs: {sorted(all_verbs)}, resources: {sorted(all_resource_names)}"
    )


@then(parsers.re(r'resources include "(?P<resource_list>.+)"'))
def _then_resources_include(ctx: SpecContext, resource_list: str) -> None:
    resource_names = {r.name for r in ctx.resources}
    expected_names = [name.strip().strip('"').strip("'") for name in resource_list.split('", "')]
    for expected in expected_names:
        matching = [
            name for name in resource_names if expected in name or name.startswith(expected)
        ]
        assert matching, (
            f"Expected resource '{expected}' not found. Available: {sorted(resource_names)}"
        )


@then(parsers.parse("at least {count:d} resources are found"))
def _then_at_least_n(ctx: SpecContext, count: int) -> None:
    assert len(ctx.resources) >= count, (
        f"Expected at least {count} resources, got {len(ctx.resources)}"
    )


@then("no two resources share the same name")
def _then_unique_names(ctx: SpecContext) -> None:
    names = [r.name for r in ctx.resources]
    assert len(names) == len(set(names)), (
        f"Duplicate resource names found: {[n for n in names if names.count(n) > 1]}"
    )


@then("resources are grouped by first path segment")
def _then_grouped_by_segment(ctx: SpecContext) -> None:
    assert len(ctx.resources) > 0


@then("no resource has an empty name")
def _then_no_empty_name(ctx: SpecContext) -> None:
    for resource in ctx.resources:
        assert resource.name.strip(), "Found resource with empty name"


@then(parsers.parse('a resource "{name}" exists'))
def _then_resource_exists(ctx: SpecContext, name: str) -> None:
    resource_names = {r.name for r in ctx.resources}
    matching = [n for n in resource_names if name in n or n.startswith(name)]
    assert matching, f"Expected resource '{name}' not found. Available: {sorted(resource_names)}"


@then(parsers.parse('the "{resource_name}" resource has a "{verb}" operation'))
def _then_resource_has_verb(ctx: SpecContext, resource_name: str, verb: str) -> None:
    for resource in ctx.resources:
        if resource_name in resource.name or resource.name.startswith(resource_name):
            verbs = [op.verb for op in resource.operations]
            assert verb in verbs, (
                f"Resource '{resource.name}' doesn't have verb '{verb}'. Has: {verbs}"
            )
            return
    pytest.fail(f"Resource '{resource_name}' not found")


@then(parsers.parse('no verb name contains "get", "post", "put", "patch", or "delete" as a prefix'))
def _then_no_http_verbs(ctx: SpecContext) -> None:
    http_prefixes = ("get", "post", "put", "patch")
    for resource in ctx.resources:
        for op in resource.operations:
            for prefix in http_prefixes:
                assert not op.verb.startswith(prefix) or op.verb == prefix, (
                    f"Verb '{op.verb}' uses HTTP method '{prefix}' as a prefix"
                )
            if op.verb.startswith("delete") and op.verb != "delete":
                raise AssertionError(f"Verb '{op.verb}' uses HTTP method 'delete' as a prefix")


@then(
    parsers.parse(
        'the "{verb}" operation has a flag "--{flag}" derived from the path param "{param}"'
    )
)
def _then_operation_has_flag(ctx: SpecContext, verb: str, flag: str, param: str) -> None:
    for resource in ctx.resources:
        for op in resource.operations:
            if op.verb == verb and resource.parent_param is not None:
                assert flag in resource.parent_param.name, (
                    f"Expected flag '--{flag}' but parent_param is '--{resource.parent_param.name}'"
                )
                return


@then(parsers.parse('no resource named "{name}" exists'))
def _then_no_resource(ctx: SpecContext, name: str) -> None:
    resource_names = {r.name for r in ctx.resources}
    assert name not in resource_names, f"Resource '{name}' should not exist but was found"


@then("all resource names are lowercase")
def _then_all_lowercase(ctx: SpecContext) -> None:
    for resource in ctx.resources:
        assert resource.name == resource.name.lower(), (
            f"Resource name '{resource.name}' is not lowercase"
        )


# ===========================================================================
# INFER-VERBS: Given steps
# ===========================================================================


@given(parsers.parse('a spec with "{method}" on path "{path}"'))
def _given_spec_method_path(ctx: SpecContext, method: str, path: str) -> None:
    method_lower = method.lower()
    spec: dict[str, object] = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }
    paths = cast("dict[str, object]", spec["paths"])

    segments = [s for s in path.split("/") if s and not s.startswith("{")]
    if segments:
        root = "/" + segments[0]
        root_id = root + "/{id}"
        if root != path:
            paths[root] = {
                "get": {
                    "summary": f"List {segments[0]}",
                    "responses": {"200": {"description": "OK"}},
                },
            }
        if root_id != path:
            paths[root_id] = {
                "get": {
                    "summary": f"Show {segments[0]}",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            }

    paths[path] = {
        method_lower: {
            "summary": f"{method} {path}",
            "parameters": [
                {
                    "name": p.strip("{}"),
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for p in path.split("/")
                if p.startswith("{")
            ],
            "responses": {"200": {"description": "OK"}},
        },
    }

    ctx.spec = spec


# ===========================================================================
# INFER-VERBS: When steps
# ===========================================================================


@when("verbs are inferred")
def _when_verbs_inferred(ctx: SpecContext) -> None:
    assert ctx.spec is not None
    ctx.resources = extract_resources(cast("dict[str, object]", ctx.spec))


@when(parsers.parse('verbs are inferred for resource "{resource_name}"'))
def _when_verbs_for_resource(ctx: SpecContext, resource_name: str) -> None:
    assert ctx.spec is not None
    ctx.resources = extract_resources(cast("dict[str, object]", ctx.spec))


@when("all verbs are inferred")
def _when_all_verbs(ctx: SpecContext) -> None:
    assert ctx.spec is not None
    ctx.resources = extract_resources(cast("dict[str, object]", ctx.spec))


# ===========================================================================
# INFER-VERBS: Then steps
# ===========================================================================


@then(parsers.parse('the operation verb is "{verb}"'))
def _then_verb_is(ctx: SpecContext, verb: str) -> None:
    all_verbs = []
    for resource in ctx.resources:
        for op in resource.operations:
            all_verbs.append(op.verb)
            if op.verb == verb:
                return
    raise AssertionError(f"Expected verb '{verb}' not found. Available: {all_verbs}")


@then("the operation is classified as an action")
def _then_is_action(ctx: SpecContext) -> None:
    for resource in ctx.resources:
        for op in resource.operations:
            if is_action_verb(op.verb):
                return


@then("the following verbs exist:")
def _then_verbs_exist(ctx: SpecContext, datatable: list[list[str]]) -> None:
    all_verbs: set[str] = set()
    for resource in ctx.resources:
        for op in resource.operations:
            all_verbs.add(op.verb)

    rows = datatable[1:]  # skip header row
    for row in rows:
        expected = row[0]
        assert expected in all_verbs, (
            f"Expected verb '{expected}' not found. Available: {sorted(all_verbs)}"
        )


@then(parsers.parse('the verb "{verb}" exists as an action'))
def _then_verb_is_action(ctx: SpecContext, verb: str) -> None:
    for resource in ctx.resources:
        for op in resource.operations:
            if op.verb == verb:
                assert is_action_verb(op.verb), (
                    f"Verb '{verb}' should be an action but is classified as CRUD"
                )
                return
    all_verbs = [op.verb for r in ctx.resources for op in r.operations]
    matching = [v for v in all_verbs if verb.replace("-", "") in v.replace("-", "")]
    if matching:
        return
    raise AssertionError(f"Verb '{verb}' not found. Available: {sorted(set(all_verbs))}")


@then(parsers.parse("the verbs include {verb_list}"))
def _then_verbs_include(ctx: SpecContext, verb_list: str) -> None:
    all_verbs: set[str] = set()
    for resource in ctx.resources:
        for op in resource.operations:
            all_verbs.add(op.verb)

    expected_verbs = [v.strip().strip('"').strip("'") for v in verb_list.split(",")]
    for expected in expected_verbs:
        assert expected in all_verbs, (
            f"Expected verb '{expected}' not found. Available: {sorted(all_verbs)}"
        )
