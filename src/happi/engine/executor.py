from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from happi.display.basic import (
    extract_primary_id,
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


@dataclass
class ExecutionContext:
    api_name: str
    base_url: str
    resource_name: str
    operation: Operation
    positional: list[str]
    extras: list[str]
    command_text: str
    auth: dict[str, str] | None = None


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
    ctx = ExecutionContext(
        api_name=api_name,
        base_url=base_url,
        resource_name=resource_name,
        operation=operation,
        positional=positional,
        extras=extras,
        command_text=command_text,
        auth=auth,
    )
    return _run(ctx)


def _run(ctx: ExecutionContext) -> int:
    output_format, quiet, yes, raw_body, filtered_extras = _extract_global_flags(ctx.extras)
    effective_format = output_format or ("table" if sys.stdout.isatty() else "json")

    resolved_positional = resolve_args(ctx.api_name, ctx.positional)
    resolved_extras = resolve_args(ctx.api_name, filtered_extras)
    identifier = resolved_positional[0] if resolved_positional else ""

    if is_destructive(ctx.operation.verb) and not render_confirm(
        ctx.resource_name, ctx.operation.verb, identifier or "?", yes=yes
    ):
        return 1

    try:
        payload = _dispatch(ctx, resolved_positional, resolved_extras, raw_body)
        if payload is not None:
            push(ctx.api_name, payload, resource=ctx.resource_name, verb=ctx.operation.verb)
        _render_payload(
            ctx, payload, output_format=effective_format, quiet=quiet, identifier=identifier
        )
        _record_outcome(ctx, success=True, primary_id=extract_primary_id(payload))
        return 0
    except APIError as e:
        render_error(
            f"{ctx.operation.verb.title()} failed ({e.status_code})",
            e.body,
            api_name=ctx.api_name,
            resource_name=ctx.resource_name,
            verb=ctx.operation.verb,
            status_code=e.status_code,
        )
        _record_outcome(ctx, success=False, primary_id=None)
        return 1
    except Exception as e:
        _log.debug("Unexpected error in %s: %s", ctx.operation.verb, e, exc_info=True)
        render_error(f"{ctx.operation.verb.title()} failed", str(e))
        _record_outcome(ctx, success=False, primary_id=None)
        return 1


def _dispatch(
    ctx: ExecutionContext,
    resolved_positional: list[str],
    resolved_extras: list[str],
    raw_body: str | None,
) -> object:
    _log.info("Executing %s %s %s", ctx.api_name, ctx.resource_name, ctx.operation.verb)
    _log.debug("Positional args: %s", resolved_positional)
    _log.debug("Extra args: %s", resolved_extras)
    path = _resolve_path(ctx.operation, resolved_positional)
    query, body = _build_inputs(ctx.operation, resolved_extras)
    explicit_body = _resolve_body(raw_body, body)
    _log.debug("Resolved path: %s", path)
    _log.debug("Query: %s", query)
    _log.debug("Body: %s", explicit_body)

    if _is_multipart_operation(ctx.operation.content_type):
        files, text_fields = _split_multipart_fields(explicit_body)
        return send_request(
            base_url=ctx.base_url,
            method=ctx.operation.http_method,
            path=path,
            query=query if query else None,
            body=text_fields,
            files=files if files else None,
            auth=ctx.auth,
        )

    return send_request(
        base_url=ctx.base_url,
        method=ctx.operation.http_method,
        path=path,
        query=query if query else None,
        body=explicit_body,
        auth=ctx.auth,
    )


def _record_outcome(ctx: ExecutionContext, *, success: bool, primary_id: str | None) -> None:
    add_history_entry(
        api_name=ctx.api_name,
        command=ctx.command_text,
        success=success,
        exit_code=0 if success else 1,
        resource=ctx.resource_name,
        verb=ctx.operation.verb,
        primary_id=primary_id,
        summary=ctx.operation.summary or ctx.operation.description or ctx.operation.path,
    )


_DESTRUCTIVE_VERBS = frozenset({"delete", "remove", "purge", "destroy", "revoke", "cancel"})


def _render_payload(
    ctx: ExecutionContext,
    payload: object,
    *,
    output_format: str = "table",
    quiet: bool = False,
    identifier: str = "",
) -> None:
    if payload is None or (isinstance(payload, str) and not payload.strip()):
        success_payload: dict[str, object] = {
            "ok": True,
            "resource": ctx.resource_name,
            "action": ctx.operation.verb,
        }
        if identifier:
            success_payload["id"] = identifier
        render_success(
            ctx.resource_name,
            ctx.operation.verb,
            success_payload,
            api_name=ctx.api_name,
            output_format=output_format,
            quiet=quiet,
        )
        return
    if isinstance(payload, BinaryFile):
        render_binary(payload)
        return
    if ctx.operation.verb == "list":
        render_table(payload, output_format=output_format, quiet=quiet)
        return
    if ctx.operation.verb == "show":
        render_card(
            payload,
            api_name=ctx.api_name,
            resource_name=ctx.resource_name,
            output_format=output_format,
            quiet=quiet,
        )
        return
    render_success(
        ctx.resource_name,
        ctx.operation.verb,
        payload,
        api_name=ctx.api_name,
        output_format=output_format,
        quiet=quiet,
    )


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


def _is_multipart_operation(content_type: str) -> bool:
    lowered = content_type.lower()
    return "multipart" in lowered or "octet-stream" in lowered


def _split_multipart_fields(
    body: object,
) -> tuple[dict[str, tuple[str, bytes, str]], dict[str, str] | None]:
    if not isinstance(body, dict):
        return {}, None

    files: dict[str, tuple[str, bytes, str]] = {}
    text_fields: dict[str, str] = {}
    typed_body = cast("dict[object, object]", body)
    for key, value in typed_body.items():
        field_name = str(key)
        string_value = str(value)
        if string_value.startswith("@"):
            file_path = Path(string_value[1:])
            if not file_path.exists() or not file_path.is_file():
                raise ValueError(f"File not found: {file_path}")
            files[field_name] = (
                file_path.name,
                file_path.read_bytes(),
                _guess_mime(file_path.name),
            )
        else:
            text_fields[field_name] = string_value

    return files, (text_fields if text_fields else None)


def _guess_mime(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".mp4": "video/mp4",
        ".pdf": "application/pdf",
    }
    return mapping.get(ext, "application/octet-stream")
