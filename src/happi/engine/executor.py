from __future__ import annotations

import json
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast

from happi.display.basic import (
    is_destructive,
    render_binary,
    render_card,
    render_confirm,
    render_error,
    render_success,
    render_table,
)
from happi.engine.history import add_history_entry
from happi.engine.stack import push, resolve_args
from happi.http.client import APIError, BinaryFile, send_request
from happi.log import get_logger

if TYPE_CHECKING:
    from happi.spec.model import Operation

_log = get_logger("engine.executor")


def execute_operation(
    *,
    api_name: str,
    base_url: str,
    resource_name: str,
    operation: Operation,
    positional: list[str],
    extras: list[str],
    command_text: str,
    auth: dict[str, str] | None = None,
) -> int:
    output_format, quiet, yes, raw_body, filtered_extras = _extract_global_flags(extras)
    is_tty = sys.stdout.isatty()
    effective_format = output_format or ("table" if is_tty else "json")

    resolved_positional = resolve_args(api_name, positional)
    resolved_extras = resolve_args(api_name, filtered_extras)

    if is_destructive(operation.verb):
        identifier = resolved_positional[0] if resolved_positional else "?"
        if not render_confirm(resource_name, operation.verb, identifier, yes=yes):
            return 1

    try:
        _log.info("Executing %s %s %s", api_name, resource_name, operation.verb)
        _log.debug("Positional args: %s", resolved_positional)
        _log.debug("Extra args: %s", resolved_extras)
        path = _resolve_path(operation, resolved_positional)
        query, body = _build_inputs(operation, resolved_extras)

        explicit_body = _resolve_body(raw_body, body)
        _log.debug("Resolved path: %s", path)
        _log.debug("Query: %s", query)
        _log.debug("Body: %s", explicit_body)
        payload = send_request(
            base_url=base_url,
            method=operation.http_method,
            path=path,
            query=query if query else None,
            body=explicit_body,
            auth=auth,
        )
        push(api_name, payload, resource=resource_name, verb=operation.verb)
        _render_payload(
            api_name,
            resource_name,
            operation,
            payload,
            output_format=effective_format,
            quiet=quiet,
        )
        add_history_entry(
            api_name=api_name,
            command=command_text,
            success=True,
            exit_code=0,
            resource=resource_name,
            verb=operation.verb,
            primary_id=_extract_primary_id(payload),
            summary=operation.summary or operation.description or operation.path,
        )
        return 0
    except APIError as e:
        render_error(
            f"{operation.verb.title()} failed ({e.status_code})",
            e.body,
            api_name=api_name,
            resource_name=resource_name,
            verb=operation.verb,
            status_code=e.status_code,
        )
        add_history_entry(
            api_name=api_name,
            command=command_text,
            success=False,
            exit_code=1,
            resource=resource_name,
            verb=operation.verb,
            primary_id=None,
            summary=operation.summary or operation.description or operation.path,
        )
        return 1
    except Exception as e:
        render_error(f"{operation.verb.title()} failed", str(e))
        add_history_entry(
            api_name=api_name,
            command=command_text,
            success=False,
            exit_code=1,
            resource=resource_name,
            verb=operation.verb,
            primary_id=None,
            summary=operation.summary or operation.description or operation.path,
        )
        return 1


def _extract_global_flags(
    extras: list[str],
) -> tuple[str | None, bool, bool, str | None, list[str]]:
    output_format: str | None = None
    quiet = False
    yes = False
    raw_body: str | None = None
    filtered: list[str] = []
    i = 0
    while i < len(extras):
        arg = extras[i]
        if arg == "--json":
            output_format = "json"
        elif arg == "--yaml":
            output_format = "yaml"
        elif arg in ("--quiet", "-q"):
            quiet = True
        elif arg in ("--yes", "-y"):
            yes = True
        elif arg in ("--output", "-o") and i + 1 < len(extras):
            output_format = extras[i + 1]
            i += 1
        elif arg == "--body" and i + 1 < len(extras):
            raw_body = extras[i + 1]
            i += 1
        else:
            filtered.append(arg)
        i += 1
    return output_format, quiet, yes, raw_body, filtered


def _resolve_path(operation: Operation, positional: list[str]) -> str:
    path = operation.path
    path_params = [arg for arg in operation.args if arg.location == "path"]
    if len(positional) < len(path_params):
        missing = ", ".join(param.name for param in path_params[len(positional) :])
        raise ValueError(f"Missing required path arguments: {missing}")
    for param, value in zip(path_params, positional, strict=False):
        path = path.replace(f"{{{param.name}}}", value)
    return path


def _build_inputs(
    operation: Operation,
    extras: list[str],
) -> tuple[dict[str, Any], object | None]:
    parsed = _parse_extra_flags(extras)
    query_param_names = {flag.name for flag in operation.flags if flag.location == "query"}
    if operation.http_method == "GET":
        query = dict(parsed)
    else:
        query = {key: value for key, value in parsed.items() if key in query_param_names}
    body = None
    if operation.http_method in {"POST", "PUT", "PATCH"}:
        body = {key: value for key, value in parsed.items() if key not in query_param_names}
        if not body:
            body = None
    return query, body


def _resolve_body(raw_body: str | None, flag_body: object | None) -> object | None:
    if raw_body is not None:
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body

    if flag_body is not None:
        return flag_body

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                return json.loads(stdin_data)
            except json.JSONDecodeError:
                return stdin_data

    return None


def _parse_extra_flags(extras: list[str]) -> dict[str, Any]:
    parsed_lists: dict[str, list[str]] = defaultdict(list)
    i = 0
    while i < len(extras):
        token = extras[i]
        if token.startswith("--"):
            key = token[2:].replace("-", "_")
            value = "true"
            if i + 1 < len(extras) and not extras[i + 1].startswith("--"):
                value = extras[i + 1]
                i += 1
            parsed_lists[key].append(value)
        i += 1
    result: dict[str, Any] = {}
    for key, values in parsed_lists.items():
        if len(values) == 1:
            single = values[0]
            if "," in single:
                result[key] = [part for part in single.split(",") if part]
            else:
                result[key] = single
        else:
            result[key] = values
    return result


def _render_payload(
    api_name: str,
    resource_name: str,
    operation: Operation,
    payload: object,
    *,
    output_format: str = "table",
    quiet: bool = False,
) -> None:
    if isinstance(payload, BinaryFile):
        render_binary(payload)
        return
    if operation.verb == "list":
        render_table(payload, output_format=output_format, quiet=quiet)
        return
    if operation.verb == "show":
        render_card(
            payload,
            api_name=api_name,
            resource_name=resource_name,
            output_format=output_format,
            quiet=quiet,
        )
        return
    render_success(
        resource_name,
        operation.verb,
        payload,
        api_name=api_name,
        output_format=output_format,
        quiet=quiet,
    )


def _extract_primary_id(payload: object) -> str | None:
    if isinstance(payload, dict):
        typed_payload = cast("dict[str, Any]", payload)
        for key in ("id", "identifier", "slug"):
            value = typed_payload.get(key)
            if value is not None:
                return str(value)
    return None
