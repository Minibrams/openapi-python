from __future__ import annotations

import keyword
import re
from pathlib import Path
from string import Template

from .extensions import GeneratorExtensions
from .model import (
    EnumDef,
    GeneratedArtifact,
    NormalizedSpec,
    OperationDef,
    TypeAliasDef,
    TypedDictDef,
)

_TEMPLATE_DIR = Path(__file__).with_name("templates")


def _load_template(name: str) -> Template:
    return Template((_TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def _indent(text: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join((prefix + line) if line else "" for line in text.splitlines())


def _format_typeddict(defn: TypedDictDef) -> str:
    if not defn.fields:
        return f"{defn.name} = TypedDict({defn.name!r}, {{}})\n"

    lines = [f"{defn.name} = TypedDict(", f"    {defn.name!r},", "    {"]
    for field in defn.fields:
        annotation = field.annotation
        if not field.required:
            annotation = f"NotRequired[{annotation}]"
        lines.append(f"        {field.name!r}: {annotation},")
    lines.extend(["    },", ")"])
    return "\n".join(lines) + "\n"


def _format_alias(alias: TypeAliasDef) -> str:
    return f"{alias.name}: TypeAlias = {alias.annotation}\n"


def _enum_member_name(value: object) -> str:
    text = str(value).upper()
    text = re.sub(r"[^a-zA-Z0-9_]", "_", text).strip("_") or "VALUE"
    text = re.sub(r"_+", "_", text)
    if text[0].isdigit():
        text = f"_{text}"
    if keyword.iskeyword(text.lower()):
        text = f"{text}_"
    return text


def _format_enum(defn: EnumDef) -> str:
    lines = [f"class {defn.name}(str, Enum):"]
    used: set[str] = set()
    for value in defn.values:
        name = _enum_member_name(value)
        base_name = name
        index = 2
        while name in used:
            name = f"{base_name}_{index}"
            index += 1
        used.add(name)
        lines.append(f"    {name} = {value!r}")
    return "\n".join(lines) + "\n"


def _typed_dict_dependencies(defn: TypedDictDef, names: set[str]) -> set[str]:
    dependencies: set[str] = set()
    for field in defn.fields:
        dependencies.update(
            name
            for name in names
            if name != defn.name
            and re.search(rf"\b{re.escape(name)}\b", field.annotation)
        )
    return dependencies


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


def _call_signature(op: OperationDef, *, is_async: bool = False) -> str:
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

    prefix = "async def" if is_async else "def"
    signature = (
        f"{prefix} __call__(self, *, "
        f"{params}, "
        f"{query}, "
        f"{headers}, "
        f"{body}"
        f") -> {op.response_type}: ..."
    )

    return signature


def _protocol_block(op: OperationDef, *, is_async: bool = False) -> str:
    protocol_name = f"Async{op.protocol_name}" if is_async else op.protocol_name
    return "\n".join(
        [
            f"class {protocol_name}(Protocol):",
            f"    {_call_signature(op, is_async=is_async)}",
            "",
        ]
    )


def _method_overload_line(op: OperationDef, *, is_async: bool = False) -> str:
    protocol_name = f"Async{op.protocol_name}" if is_async else op.protocol_name
    return (
        "@overload\n"
        f"def {op.method}(self, route: Literal[{op.route_literal!r}]) -> {protocol_name}: ..."
    )


def _method_dispatch_line(op: OperationDef, *, is_async: bool = False) -> str:
    call_prefix = "async " if is_async else ""
    request_prefix = "await " if is_async else ""
    return (
        f"if route == {op.route_literal!r}:\n"
        f"            {call_prefix}def _call(*, params=None, query=None, headers=None, body=None):\n"
        f"                return {request_prefix}self._transport.request(\n"
        f"                    method={op.method!r},\n"
        f"                    route={op.route_literal!r},\n"
        "                    base_url=self._base_url,\n"
        "                    params=params,\n"
        "                    query=query,\n"
        "                    headers=headers,\n"
        "                    body=body,\n"
        "                )\n"
        "            return _call"
    )


def _fallback_method_block(
    method: str, overloads: list[str], dispatch: list[str], *, is_async: bool = False
) -> str:
    dispatch_block = "\n\n        ".join(dispatch)
    callable_return = "Awaitable[Any]" if is_async else "object"
    call_return = "Any" if is_async else "object"
    call_prefix = "async " if is_async else ""
    request_prefix = "await " if is_async else ""
    return "\n".join(
        [
            "\n".join(overloads),
            f"@overload\ndef {method}(self, route: str) -> Callable[..., {callable_return}]: ...",
            f"def {method}(self, route: str) -> Callable[..., {callable_return}]:",
            f"        {dispatch_block}",
            f"        {call_prefix}def _call(*, params: dict[str, object] | None = None, query: dict[str, object] | None = None, headers: dict[str, object] | None = None, body: object | None = None) -> {call_return}:",
            f"            return {request_prefix}self._transport.request(",
            f"                method={method!r},",
            "                route=route,",
            "                base_url=self._base_url,",
            "                params=params,",
            "                query=query,",
            "                headers=headers,",
            "                body=body,",
            "            )",
            "        return _call",
            "",
        ]
    )


def _render_types(spec: NormalizedSpec) -> str:
    blocks = (
        [_format_enum(item) for item in spec.enums]
        + [_format_alias(alias) for alias in spec.aliases]
        + [_format_typeddict(item) for item in _order_typeddicts(spec.typed_dicts)]
    )
    return _load_template("types.py.tpl").substitute(
        type_blocks="\n".join(blocks).strip() + "\n"
    )


def _render_transport(spec: NormalizedSpec) -> str:
    routes = "\n".join(f"    {op.route_literal!r}," for op in spec.operations)
    return _load_template("transport.py.tpl").substitute(route_literals=routes)


def _render_client(spec: NormalizedSpec) -> str:
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

    return _load_template("client.py.tpl").substitute(
        protocol_blocks="\n".join(protocols).strip() + "\n",
        async_protocol_blocks="\n".join(async_protocols).strip() + "\n",
        method_blocks=_indent("\n".join(method_blocks).strip() + "\n"),
        async_method_blocks=_indent("\n".join(async_method_blocks).strip() + "\n"),
    )


def render_package(
    spec: NormalizedSpec, extensions: GeneratorExtensions | None = None
) -> list[GeneratedArtifact]:
    context = {
        "types": _render_types(spec),
        "transport": _render_transport(spec),
        "client": _render_client(spec),
    }

    if extensions:
        for hook in extensions.render_context_hooks:
            context = hook(spec, context)

    init_content = (
        "from .client import AsyncClient, Client\n"
        "from .transport import AsyncTransport, DefaultAsyncTransport, DefaultTransport, Transport\n\n"
        "__all__ = [\n"
        "    'AsyncClient',\n"
        "    'AsyncTransport',\n"
        "    'Client',\n"
        "    'DefaultAsyncTransport',\n"
        "    'DefaultTransport',\n"
        "    'Transport',\n"
        "]\n"
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
