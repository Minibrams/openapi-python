from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(frozen=True)
class AnyAnnotation:
    pass


@dataclass(frozen=True)
class DictAnnotation:
    key: TypeAnnotation
    value: TypeAnnotation


@dataclass(frozen=True)
class ListAnnotation:
    item: TypeAnnotation


@dataclass(frozen=True)
class MappingAnnotation:
    key: TypeAnnotation
    value: TypeAnnotation


@dataclass(frozen=True)
class LiteralAnnotation:
    values: tuple[object, ...]


@dataclass(frozen=True)
class NamedAnnotation:
    name: str


@dataclass(frozen=True)
class TupleAnnotation:
    items: tuple[TypeAnnotation, ...]


@dataclass(frozen=True)
class UnionAnnotation:
    items: tuple[TypeAnnotation, ...]


TypeAnnotation: TypeAlias = (
    AnyAnnotation
    | DictAnnotation
    | ListAnnotation
    | MappingAnnotation
    | LiteralAnnotation
    | NamedAnnotation
    | TupleAnnotation
    | UnionAnnotation
)


@dataclass(frozen=True)
class FieldDef:
    name: str
    annotation: TypeAnnotation
    required: bool
    description: str | None = None


@dataclass(frozen=True)
class TypedDictDef:
    name: str
    fields: tuple[FieldDef, ...]
    description: str | None = None


@dataclass(frozen=True)
class TypeAliasDef:
    name: str
    annotation: TypeAnnotation


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
    params_type: TypeAnnotation
    params_required: bool
    query_type: TypeAnnotation
    query_required: bool
    headers_type: TypeAnnotation
    headers_required: bool
    request_media_type: str | None
    body_type: TypeAnnotation | None
    body_required: bool
    response_media_type: str | None
    response_type: TypeAnnotation


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
