from __future__ import annotations

import keyword
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .extensions import GeneratorExtensions
from .model import (
    EnumDef,
    FieldDef,
    GeneratedArtifact,
    NormalizedSpec,
    OperationDef,
    TypeAliasDef,
    TypedDictDef,
)


def _field_annotation(field: FieldDef) -> str:
    """
    Jinja2 filter to format a FieldDef's annotation.
    """
    annotation = repr(field.annotation)
    if not field.required:
        annotation = f"NotRequired[{annotation}]"
    return annotation


_TEMPLATE_DIR = Path(__file__).with_name("templates")
_JINJA_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)
_JINJA_ENV.filters["repr"] = repr
_JINJA_ENV.filters["field_annotation"] = _field_annotation

_IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def _render_template(name: str, **context: object) -> str:
    return _JINJA_ENV.get_template(name).render(**context)


def _indent(text: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join((prefix + line) if line else "" for line in text.splitlines())


def _format_typeddict(defn: TypedDictDef) -> str:
    return _render_template("typeddict.py.j2", defn=defn)


def _format_alias(alias: TypeAliasDef) -> str:
    return _render_template("alias.py.j2", alias=alias)


def _enum_member_name(value: object) -> str:
    text = str(value).upper()
    text = re.sub(r"[^a-zA-Z0-9_]", "_", text).strip("_") or "VALUE"
    text = re.sub(r"_+", "_", text)
    if text[0].isdigit():
        text = f"_{text}"
    if keyword.iskeyword(text.lower()):
        text = f"{text}_"
    return text


def _enum_base(defn: EnumDef) -> str:
    if all(isinstance(value, str) for value in defn.values):
        return "str, Enum"
    if all(
        isinstance(value, int) and not isinstance(value, bool) for value in defn.values
    ):
        return "int, Enum"
    return "Enum"


def _format_enum(defn: EnumDef) -> str:
    members: list[tuple[str, object]] = []
    used: set[str] = set()
    for value in defn.values:
        name = _enum_member_name(value)
        base_name = name
        index = 2
        while name in used:
            name = f"{base_name}_{index}"
            index += 1
        used.add(name)
        members.append((name, value))
    return _render_template(
        "enum.py.j2",
        defn=defn,
        enum_base=_enum_base(defn),
        members=members,
    )


def _annotation_dependencies(annotation: str, names: set[str]) -> set[str]:
    return names.intersection(_IDENTIFIER.findall(annotation))


def _typed_dict_dependencies(defn: TypedDictDef, names: set[str]) -> set[str]:
    dependencies: set[str] = set()
    for field in defn.fields:
        dependencies.update(_annotation_dependencies(field.annotation, names))
    dependencies.discard(defn.name)
    return dependencies


def _alias_dependencies(defn: TypeAliasDef, names: set[str]) -> set[str]:
    dependencies = _annotation_dependencies(defn.annotation, names)
    dependencies.discard(defn.name)
    return dependencies


def _order_aliases(defns: tuple[TypeAliasDef, ...]) -> list[TypeAliasDef]:
    by_name = {item.name: item for item in defns}
    names = set(by_name)
    ordered: list[TypeAliasDef] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(name: str) -> None:
        if name in permanent or name in temporary:
            return
        temporary.add(name)
        for dependency in sorted(_alias_dependencies(by_name[name], names)):
            visit(dependency)
        temporary.remove(name)
        permanent.add(name)
        ordered.append(by_name[name])

    for name in sorted(by_name):
        visit(name)
    return ordered


def _order_typeddicts(defns: tuple[TypedDictDef, ...]) -> list[TypedDictDef]:
    by_name = {item.name: item for item in defns}
    names = set(by_name)
    ordered: list[TypedDictDef] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(name: str) -> None:
        if name in permanent or name in temporary:
            return
        temporary.add(name)
        for dependency in sorted(_typed_dict_dependencies(by_name[name], names)):
            visit(dependency)
        temporary.remove(name)
        permanent.add(name)
        ordered.append(by_name[name])

    for name in sorted(by_name):
        visit(name)
    return ordered


def _call_parameters(op: OperationDef) -> dict[str, str]:
    params = "params: " + op.params_type
    if not op.params_required:
        params += " | None = None"

    query = "query: " + op.query_type
    if not op.query_required:
        query += " | None = None"

    headers = "headers: " + op.headers_type
    if not op.headers_required:
        headers += " | None = None"

    body = "body: object | None = None"
    if op.body_type:
        body = f"body: {op.body_type}"
        if not op.body_required:
            body += " | None = None"

    return {
        "params": params,
        "query": query,
        "headers": headers,
        "body": body,
    }


def _protocol_name(op: OperationDef, *, is_async: bool = False) -> str:
    return f"Async{op.protocol_name}" if is_async else op.protocol_name


def _protocol_block(op: OperationDef, *, is_async: bool = False) -> str:
    return _render_template(
        "protocol.py.j2",
        op=op,
        is_async=is_async,
        protocol_name=_protocol_name(op, is_async=is_async),
        call_parameters=_call_parameters(op),
    )


def _method_overload_line(op: OperationDef, *, is_async: bool = False) -> str:
    return _render_template(
        "method_overload.py.j2",
        op=op,
        protocol_name=_protocol_name(op, is_async=is_async),
    )


def _method_dispatch_line(op: OperationDef, *, is_async: bool = False) -> str:
    return _render_template(
        "method_dispatch.py.j2",
        op=op,
        is_async=is_async,
    )


def _fallback_method_block(
    method: str, overloads: list[str], dispatch: list[str], *, is_async: bool = False
) -> str:
    return _render_template(
        "method_block.py.j2",
        method=method,
        overloads="\n".join(overloads),
        dispatch_block="\n\n        ".join(dispatch),
        callable_return="Awaitable[Any]" if is_async else "object",
        call_return="Any" if is_async else "object",
        is_async=is_async,
    )


def _render_types(spec: NormalizedSpec) -> str:
    aliases = (*_route_aliases(spec), *_order_aliases(spec.aliases))
    blocks = (
        [_format_enum(item) for item in spec.enums]
        + [_format_alias(alias) for alias in aliases]
        + [_format_typeddict(item) for item in _order_typeddicts(spec.typed_dicts)]
    )
    return _render_template(
        "types.py.j2",
        type_blocks="\n".join(blocks).strip() + "\n",
    )


def _literal_annotation(values: set[str]) -> str:
    return f"Literal[{', '.join(repr(value) for value in sorted(values))}]"


def _route_aliases(spec: NormalizedSpec) -> tuple[TypeAliasDef, ...]:
    routes_by_method: dict[str, set[str]] = {}
    for op in spec.operations:
        routes_by_method.setdefault(op.method.upper(), set()).add(op.route_literal)

    aliases = [
        TypeAliasDef(
            name=f"{method}_RouteLiteral", annotation=_literal_annotation(routes)
        )
        for method, routes in sorted(routes_by_method.items())
    ]

    if aliases:
        aliases.append(
            TypeAliasDef(
                name="RouteLiteral",
                annotation=" | ".join(alias.name for alias in aliases),
            )
        )
    else:
        aliases.append(TypeAliasDef(name="RouteLiteral", annotation="str"))
    return tuple(aliases)


def _render_transport(spec: NormalizedSpec, *, transport_mode: str) -> str:
    return _render_template(
        "transport.py.j2",
        typing_imports=(
            "TYPE_CHECKING, Protocol" if transport_mode == "default" else "Protocol"
        ),
        include_default_transport=transport_mode == "default",
    )


def _render_client(spec: NormalizedSpec, *, transport_mode: str) -> str:
    protocols: list[str] = []
    async_protocols: list[str] = []
    method_overloads: dict[str, list[str]] = {}
    async_method_overloads: dict[str, list[str]] = {}
    method_dispatch: dict[str, list[str]] = {}
    async_method_dispatch: dict[str, list[str]] = {}
    for op in spec.operations:
        protocols.append(_protocol_block(op))
        async_protocols.append(_protocol_block(op, is_async=True))
        method_overloads.setdefault(op.method, []).append(_method_overload_line(op))
        async_method_overloads.setdefault(op.method, []).append(
            _method_overload_line(op, is_async=True)
        )
        method_dispatch.setdefault(op.method, []).append(_method_dispatch_line(op))
        async_method_dispatch.setdefault(op.method, []).append(
            _method_dispatch_line(op, is_async=True)
        )

    method_blocks: list[str] = []
    for method in sorted(method_overloads):
        method_blocks.append(
            _fallback_method_block(
                method,
                method_overloads[method],
                method_dispatch.get(method, []),
            )
        )
    async_method_blocks: list[str] = []
    for method in sorted(async_method_overloads):
        async_method_blocks.append(
            _fallback_method_block(
                method,
                async_method_overloads[method],
                async_method_dispatch.get(method, []),
                is_async=True,
            )
        )

    if transport_mode == "default":
        transport_imports = (
            "from .transport import AsyncTransport, DefaultAsyncTransport, "
            "DefaultTransport, Transport"
        )
        sync_transport_type = "Transport | None = None"
        sync_transport_assignment = "transport or DefaultTransport()"
        async_transport_type = "AsyncTransport | None = None"
        async_transport_assignment = "transport or DefaultAsyncTransport()"
    else:
        transport_imports = "from .transport import AsyncTransport, Transport"
        sync_transport_type = "Transport"
        sync_transport_assignment = "transport"
        async_transport_type = "AsyncTransport"
        async_transport_assignment = "transport"

    return _render_template(
        "client.py.j2",
        transport_imports=transport_imports,
        sync_transport_type=sync_transport_type,
        sync_transport_assignment=sync_transport_assignment,
        async_transport_type=async_transport_type,
        async_transport_assignment=async_transport_assignment,
        protocol_blocks="\n".join(protocols).strip() + "\n",
        async_protocol_blocks="\n".join(async_protocols).strip() + "\n",
        method_blocks=_indent("\n".join(method_blocks).strip() + "\n"),
        async_method_blocks=_indent("\n".join(async_method_blocks).strip() + "\n"),
    )


def render_package(
    spec: NormalizedSpec,
    extensions: GeneratorExtensions | None = None,
    *,
    transport_mode: str = "default",
) -> list[GeneratedArtifact]:
    context = {
        "types": _render_types(spec),
        "transport": _render_transport(spec, transport_mode=transport_mode),
        "client": _render_client(spec, transport_mode=transport_mode),
    }

    if extensions:
        for hook in extensions.render_context_hooks:
            context = hook(spec, context)

    init_content = _render_template(
        "init.py.j2", include_default_transport=transport_mode == "default"
    )

    return [
        GeneratedArtifact(
            relative_path=f"{spec.package_name}/__init__.py", content=init_content
        ),
        GeneratedArtifact(
            relative_path=f"{spec.package_name}/types.py", content=context["types"]
        ),
        GeneratedArtifact(
            relative_path=f"{spec.package_name}/transport.py",
            content=context["transport"],
        ),
        GeneratedArtifact(
            relative_path=f"{spec.package_name}/client.py", content=context["client"]
        ),
        GeneratedArtifact(relative_path=f"{spec.package_name}/py.typed", content="\n"),
    ]
