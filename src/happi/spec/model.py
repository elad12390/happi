from dataclasses import dataclass, field
from typing import Literal


def _str_list() -> list[str]:
    return []


def _param_list() -> list["Param"]:
    return []


def _operation_list() -> list["Operation"]:
    return []


Verb = Literal["list", "show", "create", "update", "delete"]
Confidence = Literal["certain", "high", "medium", "configured"]
RelationType = Literal["belongs-to", "has-many"]


@dataclass
class Param:
    name: str
    location: Literal["path", "query", "body"]
    param_type: str
    required: bool = False
    description: str = ""
    enum_values: list[str] = field(default_factory=_str_list)


@dataclass
class Operation:
    verb: str
    http_method: str
    path: str
    summary: str = ""
    description: str = ""
    args: list[Param] = field(default_factory=_param_list)
    flags: list[Param] = field(default_factory=_param_list)
    is_action: bool = False


@dataclass
class Resource:
    name: str
    operations: list[Operation] = field(default_factory=_operation_list)
    description: str = ""
    parent_param: Param | None = None


@dataclass
class Relation:
    from_resource: str
    to_resource: str
    relation_type: RelationType
    via: str
    confidence: Confidence
