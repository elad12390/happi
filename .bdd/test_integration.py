from __future__ import annotations

from typing import TYPE_CHECKING

from interactions.cli_helpers import run_happi_in_env

if TYPE_CHECKING:
    from pathlib import Path


def test_explore_lists_resources(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "explore")
    assert r.exit_code == 0
    assert "pets" in r.stdout
    assert "choose a resource" in r.stdout


def test_api_help_lists_commands(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "--help")
    assert r.exit_code == 0
    assert "explore" in r.stdout
    assert "pets" in r.stdout
    assert "docs" in r.stdout
    assert "history" in r.stdout
    assert "find" in r.stdout


def test_resource_help_lists_verbs(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "--help")
    assert r.exit_code == 0
    assert "list" in r.stdout or "show" in r.stdout
    assert "create" in r.stdout


def test_list_returns_table(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "list")
    assert r.exit_code == 0
    assert "Buddy" in r.stdout or "items" in r.stdout


def test_show_returns_card(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--output", "table")
    assert r.exit_code == 0
    assert "Buddy" in r.stdout


def test_show_json_output(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--json")
    assert r.exit_code == 0
    import json

    data = json.loads(r.stdout)
    assert data["name"] == "Buddy"


def test_show_yaml_output(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--yaml")
    assert r.exit_code == 0
    assert "name: Buddy" in r.stdout


def test_create_returns_success(configured_petstore: str) -> None:
    r = run_happi_in_env(
        configured_petstore,
        "testapi",
        "pets",
        "create",
        "--name",
        "Milo",
        "--status",
        "available",
        "--output",
        "table",
    )
    assert r.exit_code == 0
    assert "Created" in r.stdout or "✓" in r.stdout


def test_update_returns_success(configured_petstore: str) -> None:
    r = run_happi_in_env(
        configured_petstore,
        "testapi",
        "pets",
        "update",
        "1",
        "--status",
        "sold",
        "--output",
        "table",
    )
    assert r.exit_code == 0
    assert "Updated" in r.stdout or "✓" in r.stdout


def test_delete_requires_yes_in_noninteractive(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "delete", "1")
    assert r.exit_code != 0
    assert "Use --yes" in r.stderr


def test_delete_with_yes_succeeds(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "delete", "2", "--yes")
    assert r.exit_code == 0


def test_action_activate(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "activate", "1")
    assert r.exit_code == 0


def test_show_not_found_shows_error(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "99999")
    assert r.exit_code != 0
    assert "404" in r.stderr or "not found" in r.stderr.lower()


def test_find_command(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "find", "activate")
    assert r.exit_code == 0
    assert "activate" in r.stdout


def test_docs_generates_markdown(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "docs")
    assert r.exit_code == 0
    assert "# testapi" in r.stdout
    assert "## Resources" in r.stdout
    assert "pets" in r.stdout


def test_docs_map_only(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "docs", "--map-only")
    assert r.exit_code == 0
    assert "```mermaid" in r.stdout


def test_docs_single_resource(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "docs", "--resource", "pets")
    assert r.exit_code == 0
    assert "pets" in r.stdout


def test_history_shows_commands(configured_petstore: str) -> None:
    run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--json")
    r = run_happi_in_env(configured_petstore, "testapi", "history")
    assert r.exit_code == 0
    assert "testapi" in r.stdout


def test_global_history(configured_petstore: str) -> None:
    run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--json")
    r = run_happi_in_env(configured_petstore, "history")
    assert r.exit_code == 0
    assert "testapi" in r.stdout


def test_config_list(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "config", "list")
    assert r.exit_code == 0
    assert "testapi" in r.stdout


def test_config_get(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "config", "get", "apis.testapi.name")
    assert r.exit_code == 0
    assert "testapi" in r.stdout


def test_config_set_and_get(configured_petstore: str) -> None:
    run_happi_in_env(configured_petstore, "config", "set", "apis.testapi.note", "test-note")
    r = run_happi_in_env(configured_petstore, "config", "get", "apis.testapi.note")
    assert r.exit_code == 0
    assert "test-note" in r.stdout


def test_config_unset(configured_petstore: str) -> None:
    run_happi_in_env(configured_petstore, "config", "set", "apis.testapi.temp", "value")
    r = run_happi_in_env(configured_petstore, "config", "unset", "apis.testapi.temp")
    assert r.exit_code == 0


def test_config_show(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "config", "show", "testapi")
    assert r.exit_code == 0
    assert "testapi" in r.stdout


def test_auth_set_bearer(configured_petstore: str) -> None:
    r = run_happi_in_env(
        configured_petstore,
        "auth",
        "set",
        "testapi",
        "--type",
        "bearer",
        "--token",
        "test-token-123",
    )
    assert r.exit_code == 0
    assert "Set auth" in r.stdout


def test_auth_show_masked(configured_petstore: str) -> None:
    run_happi_in_env(
        configured_petstore,
        "auth",
        "set",
        "testapi",
        "--type",
        "bearer",
        "--token",
        "sk_live_abcdef1234567890",
    )
    r = run_happi_in_env(configured_petstore, "auth", "show", "testapi")
    assert r.exit_code == 0
    assert "sk" in r.stdout
    assert "abcdef1234567890" not in r.stdout


def test_auth_show_reveal(configured_petstore: str) -> None:
    run_happi_in_env(
        configured_petstore,
        "auth",
        "set",
        "testapi",
        "--type",
        "bearer",
        "--token",
        "sk_live_abcdef1234567890",
    )
    r = run_happi_in_env(configured_petstore, "auth", "show", "testapi", "--reveal")
    assert r.exit_code == 0
    assert "sk_live_abcdef1234567890" in r.stdout


def test_auth_unset(configured_petstore: str) -> None:
    run_happi_in_env(
        configured_petstore, "auth", "set", "testapi", "--type", "bearer", "--token", "test-token"
    )
    r = run_happi_in_env(configured_petstore, "auth", "unset", "testapi")
    assert r.exit_code == 0
    assert "Removed auth" in r.stdout


def test_auth_set_apikey(configured_petstore: str) -> None:
    r = run_happi_in_env(
        configured_petstore,
        "auth",
        "set",
        "testapi",
        "--type",
        "api-key",
        "--value",
        "mykey",
        "--header",
        "X-API-Key",
    )
    assert r.exit_code == 0
    assert "Set auth" in r.stdout


def test_hints_after_show(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--output", "table")
    assert r.exit_code == 0
    assert "↳" in r.stdout or "update" in r.stdout


def test_quiet_suppresses_hints(configured_petstore: str) -> None:
    r = run_happi_in_env(
        configured_petstore, "testapi", "pets", "show", "1", "--output", "table", "--quiet"
    )
    assert r.exit_code == 0
    assert "↳" not in r.stdout


def test_unknown_command_error(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "nonexistent")
    assert r.exit_code != 0


def test_json_flag_not_eaten_as_positional(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--json")
    assert r.exit_code == 0
    import json

    data = json.loads(r.stdout)
    assert data["id"] == 1


def test_output_flag_not_eaten_as_positional(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "1", "--output", "table")
    assert r.exit_code == 0
    assert "Buddy" in r.stdout


def test_yes_flag_not_eaten_as_positional(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "delete", "3", "--yes")
    assert r.exit_code == 0


def test_quiet_flag_not_eaten_as_positional(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "list", "--quiet")
    assert r.exit_code == 0


def test_flags_before_positional_not_eaten(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "--json", "1")
    assert r.exit_code == 0
    import json

    data = json.loads(r.stdout)
    assert data["id"] == 1


def test_output_flag_between_verb_and_id_not_eaten(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "show", "--output", "table", "1")
    assert r.exit_code == 0
    assert "Buddy" in r.stdout


def test_get_with_id_maps_to_show_not_list(tmp_path: Path) -> None:
    from happi.spec.resources import extract_resources

    spec: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/v1/convai/phone-numbers": {
                "get": {
                    "summary": "List Phone Numbers",
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "summary": "Create Phone Number",
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/v1/convai/phone-numbers/{phone_number_id}": {
                "get": {
                    "summary": "Get Phone Number",
                    "parameters": [
                        {
                            "name": "phone_number_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
                "patch": {
                    "summary": "Update Phone Number",
                    "parameters": [
                        {
                            "name": "phone_number_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
                "delete": {
                    "summary": "Delete Phone Number",
                    "parameters": [
                        {
                            "name": "phone_number_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    resources = extract_resources(spec)
    phone_resource = next((r for r in resources if "phone" in r.name), None)
    assert phone_resource is not None

    verbs = [op.verb for op in phone_resource.operations]
    assert "show" in verbs, f"Expected 'show' in {verbs} — GET with {{id}} should be show not list"
    assert "list" in verbs, f"Expected 'list' in {verbs} — GET without {{id}} should be list"

    list_ops = [op for op in phone_resource.operations if op.verb == "list"]
    for op in list_ops:
        assert not op.args, f"list should have no path args, but has {[a.name for a in op.args]}"

    show_ops = [op for op in phone_resource.operations if op.verb == "show"]
    for op in show_ops:
        assert op.args, "show should have path args but has none"


def test_duplicate_verbs_are_disambiguated(tmp_path: Path) -> None:
    from happi.spec.resources import extract_resources

    spec: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/v1/convai/agents": {
                "get": {"summary": "List Agents", "responses": {"200": {"description": "OK"}}},
                "post": {
                    "summary": "Create Agent",
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/v1/convai/agents/{agent_id}": {
                "get": {
                    "summary": "Get Agent",
                    "parameters": [
                        {
                            "name": "agent_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/v1/convai/agents/{agent_id}/branches": {
                "get": {
                    "summary": "List Branches",
                    "parameters": [
                        {
                            "name": "agent_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "summary": "Create Branch",
                    "parameters": [
                        {
                            "name": "agent_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"201": {"description": "Created"}},
                },
            },
        },
    }
    resources = extract_resources(spec)
    agents = next((r for r in resources if "agent" in r.name), None)
    assert agents is not None

    verb_counts: dict[str, int] = {}
    for op in agents.operations:
        verb_counts[op.verb] = verb_counts.get(op.verb, 0) + 1

    for verb_name, count in verb_counts.items():
        assert count == 1, (
            f"Verb '{verb_name}' appears {count} times in "
            f"resource '{agents.name}' — should be unique"
        )


def test_elevenlabs_voice_paths_produce_resources(tmp_path: Path) -> None:
    from happi.spec.resources import extract_resources

    spec: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/v1/voices": {
                "get": {"summary": "List Voices", "responses": {"200": {"description": "OK"}}},
            },
            "/v1/voices/{voice_id}": {
                "get": {
                    "summary": "Get Voice",
                    "parameters": [
                        {
                            "name": "voice_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/v1/text-to-speech/{voice_id}/stream": {
                "post": {
                    "summary": "Text To Speech Stream",
                    "parameters": [
                        {
                            "name": "voice_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    resources = extract_resources(spec)
    resource_names = [r.name for r in resources]
    assert "voices" in resource_names, f"Expected 'voices' in {resource_names}"
    assert any("text-to-speech" in n or "text-to-speeches" in n for n in resource_names), (
        f"Expected text-to-speech resource in {resource_names}"
    )


def test_binary_response_saves_to_file(configured_petstore: str) -> None:
    r = run_happi_in_env(configured_petstore, "testapi", "pets", "photo", "1")
    assert r.exit_code == 0
    assert "saved" in r.stdout.lower() or "wrote" in r.stdout.lower() or ".png" in r.stdout.lower()


def test_body_flag_sends_raw_json(configured_petstore: str) -> None:
    import json

    r = run_happi_in_env(
        configured_petstore,
        "testapi",
        "pets",
        "create",
        "--body",
        '{"name":"BodyPet","status":"available"}',
        "--json",
    )
    assert r.exit_code == 0, f"Failed: {r.stderr}"
    data = json.loads(r.stdout)
    assert data["name"] == "BodyPet"


def test_stdin_pipe_sends_json_body(configured_petstore: str) -> None:
    import json

    r = run_happi_in_env(
        configured_petstore,
        "testapi",
        "pets",
        "create",
        "--json",
        stdin_text='{"name":"StdinPet","status":"pending"}',
    )
    assert r.exit_code == 0, f"Failed: {r.stderr}"
    data = json.loads(r.stdout)
    assert data["name"] == "StdinPet"


def test_body_flag_overrides_other_flags(configured_petstore: str) -> None:
    import json

    r = run_happi_in_env(
        configured_petstore,
        "testapi",
        "pets",
        "create",
        "--name",
        "FlagPet",
        "--body",
        '{"name":"BodyWins","status":"available"}',
        "--json",
    )
    assert r.exit_code == 0, f"Failed: {r.stderr}"
    data = json.loads(r.stdout)
    assert data["name"] == "BodyWins"


def test_inflect_crash_on_unusual_schema_names() -> None:
    from happi.spec.relations import infer_relations
    from happi.spec.resources import extract_resources

    spec: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "EdgeCaseAPI", "version": "1.0"},
        "paths": {
            "/items": {
                "get": {"summary": "List items", "responses": {"200": {"description": "OK"}}},
            },
        },
        "components": {
            "schemas": {
                "": {
                    "type": "object",
                    "properties": {"item_id": {"type": "integer"}},
                },
                " ": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
                "-": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                },
                "NormalSchema": {
                    "type": "object",
                    "properties": {"item_id": {"type": "integer"}},
                },
            }
        },
    }
    resources = extract_resources(spec)
    relations = infer_relations(spec, resources)
    assert isinstance(relations, list)
