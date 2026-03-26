from __future__ import annotations

CRUD_VERBS = frozenset({"list", "show", "create", "update", "delete"})


def is_crud_verb(verb: str) -> bool:
    return verb in CRUD_VERBS


def is_action_verb(verb: str) -> bool:
    return verb not in CRUD_VERBS
