from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldDef:
    name: str
    annotation: str
    required: bool


@dataclass(frozen=True)
class TypedDictDef:
    name: str
    fields: tuple[FieldDef, ...]


@dataclass(frozen=True)
class TypeAliasDef:
    name: str
    annotation: str


@dataclass(frozen=True)
class EnumDef:
    name: str
    values: tuple[object, ...]


@dataclass(frozen=True)
class OperationDef:
    method: str
    route_literal: str
    symbol: str
    protocol_name: str
    params_type: str
    params_required: bool
    query_type: str
    query_required: bool
    headers_type: str
    headers_required: bool
    body_type: str | None
    body_required: bool
    response_type: str


@dataclass(frozen=True)
class NormalizedSpec:
    package_name: str
    typed_dicts: tuple[TypedDictDef, ...]
    aliases: tuple[TypeAliasDef, ...]
    enums: tuple[EnumDef, ...]
    operations: tuple[OperationDef, ...]


@dataclass(frozen=True)
class GeneratedArtifact:
    relative_path: str
    content: str


@dataclass
class RenderContext:
    package_name: str
    import_typing: set[str] = field(default_factory=set)
    import_typeddict: bool = False
