from dataclasses import dataclass, field
from typing import Literal


def _str_list() -> list[str]:
    return []


def _param_list() -> list["Param"]:
    return []


def _operation_list() -> list["Operation"]:
    return []


def _resource_list() -> list["Resource"]:
    return []


def _relation_list() -> list["Relation"]:
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


@dataclass
class ResourceModel:
    title: str
    version: str
    base_url: str
    resources: list[Resource] = field(default_factory=_resource_list)
    relations: list[Relation] = field(default_factory=_relation_list)
    spec_hash: str = ""
