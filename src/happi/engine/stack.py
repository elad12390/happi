from __future__ import annotations

import sys
from typing import Any, cast

from happi.log import get_logger

_log = get_logger("engine.stack")

MAX_STACK_SIZE = 20

_stacks: dict[str, list[dict[str, Any]]] = {}


def push(api_name: str, payload: object, *, resource: str, verb: str) -> None:
    if not sys.stdout.isatty():
        return
    stack = _stacks.setdefault(api_name, [])
    entry: dict[str, Any] = {
        "payload": payload,
        "resource": resource,
        "verb": verb,
        "primary_id": _extract_id(payload),
    }
    stack.append(entry)
    if len(stack) > MAX_STACK_SIZE:
        _stacks[api_name] = stack[-MAX_STACK_SIZE:]
    _log.debug("Pushed to stack[%s]: %s %s", api_name, resource, verb)


def resolve(api_name: str, ref: str) -> str:
    if not ref.startswith("_"):
        return ref

    stack = _stacks.get(api_name, [])
    if not stack:
        msg = "No previous result in this session. Run a command first."
        raise StackError(msg)

    if ref == "_":
        return _coerce_to_id(stack[-1])

    if ref.startswith("_."):
        field = ref[2:]
        return _extract_field(stack[-1], field)

    if ref.startswith("_") and ref[1:].isdigit():
        idx = int(ref[1:])
        if idx >= len(stack):
            msg = f"Stack reference _{idx} is out of range. Stack has {len(stack)} entries."
            raise StackError(msg)
        reverse_idx = len(stack) - 1 - idx
        return _coerce_to_id(stack[reverse_idx])

    if "." in ref and ref.split(".")[0].startswith("_"):
        parts = ref.split(".", 1)
        base = parts[0]
        field = parts[1]
        idx = 0 if base == "_" else int(base[1:])
        if idx >= len(stack):
            msg = f"Stack reference _{idx} is out of range. Stack has {len(stack)} entries."
            raise StackError(msg)
        reverse_idx = len(stack) - 1 - idx
        return _extract_field(stack[reverse_idx], field)

    return ref


def resolve_args(api_name: str, args: list[str]) -> list[str]:
    if not sys.stdout.isatty():
        return args
    return [resolve(api_name, arg) for arg in args]


def get_stack(api_name: str) -> list[dict[str, Any]]:
    return list(reversed(_stacks.get(api_name, [])))


class StackError(Exception):
    pass


def _coerce_to_id(entry: dict[str, Any]) -> str:
    payload = entry.get("payload")
    if isinstance(payload, list):
        typed_list = cast("list[object]", payload)
        count = len(typed_list)
        msg = f"Last result is a list of {count} items. Use _[0].id or choose a specific row."
        raise StackError(msg)
    primary_id = entry.get("primary_id")
    if primary_id is not None:
        return str(primary_id)
    msg = "Last result has no identifiable ID field."
    raise StackError(msg)


def _extract_field(entry: dict[str, Any], field: str) -> str:
    payload = entry.get("payload")
    if isinstance(payload, dict):
        typed = cast("dict[str, Any]", payload)
        value = typed.get(field)
        if value is not None:
            return str(value)
        msg = f"Field '{field}' not found in last result."
        raise StackError(msg)
    msg = "Last result is not a dictionary."
    raise StackError(msg)


def _extract_id(payload: object) -> str | None:
    if isinstance(payload, dict):
        typed = cast("dict[str, Any]", payload)
        for key in ("id", "identifier", "slug"):
            value = typed.get(key)
            if value is not None:
                return str(value)
    return None
