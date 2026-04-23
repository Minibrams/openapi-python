from __future__ import annotations

from pathlib import Path
from string import Template

from .extensions import GeneratorExtensions
from .model import (
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
        return f"class {defn.name}(TypedDict, total=False):\n    pass\n"

    lines = [f"class {defn.name}(TypedDict, total=False):"]
    for field in defn.fields:
        lines.append(f"    {field.name}: {field.annotation}")
    return "\n".join(lines) + "\n"


def _format_alias(alias: TypeAliasDef) -> str:
    return f"{alias.name}: TypeAlias = {alias.annotation}\n"


def _call_signature(op: OperationDef) -> str:
    params = "params: " + op.params_type
    if not op.params_required:
        params += " | None = None"

    body = "body: object | None = None"
    if op.body_type:
        body = f"body: {op.body_type}"
        if not op.body_required:
            body += " | None = None"

    signature = (
        "def __call__(self, *, "
        f"{params}, "
        f"query: {op.query_type} | None = None, "
        f"headers: {op.headers_type} | None = None, "
        f"{body}"
        f") -> {op.response_type}: ..."
    )

    return signature


def _render_types(spec: NormalizedSpec) -> str:
    blocks = [_format_alias(alias) for alias in spec.aliases] + [
        _format_typeddict(item) for item in spec.typed_dicts
    ]
    return _load_template("types.py.tpl").substitute(
        type_blocks="\n".join(blocks).strip() + "\n"
    )


def _render_transport(spec: NormalizedSpec) -> str:
    routes = "\n".join(f"    {op.route_literal!r}," for op in spec.operations)
    return _load_template("transport.py.tpl").substitute(route_literals=routes)


def _render_client(spec: NormalizedSpec) -> str:
    protocols: list[str] = []
    method_overloads: dict[str, list[str]] = {}
    method_dispatch: dict[str, list[str]] = {}
    for op in spec.operations:
        proto_sig = _call_signature(op)
        protocols.append(
            "\n".join(
                [
                    f"class {op.protocol_name}(Protocol):",
                    f"    {proto_sig}",
                    "",
                ]
            )
        )

        method = op.method
        method_overloads.setdefault(method, []).append(
            f"@overload\ndef {method}(self, route: Literal[{op.route_literal!r}]) -> {op.protocol_name}: ..."
        )

        call_line = (
            f"if route == {op.route_literal!r}:\n"
            "            def _call(*, params=None, query=None, headers=None, body=None):\n"
            "                return self._transport.request(\n"
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
        method_dispatch.setdefault(method, []).append(call_line)

    method_blocks: list[str] = []
    for method in sorted(method_overloads):
        overloads = "\n".join(method_overloads[method])
        dispatch = "\n\n        ".join(method_dispatch.get(method, []))
        method_blocks.append(
            "\n".join(
                [
                    overloads,
                    f"@overload\ndef {method}(self, route: str) -> Callable[..., object]: ...",
                    f"def {method}(self, route: str) -> Callable[..., object]:",
                    f"        {dispatch}",
                    "        def _call(*, params: dict[str, object] | None = None, query: dict[str, object] | None = None, headers: dict[str, object] | None = None, body: object | None = None) -> object:",
                    "            return self._transport.request(",
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
        )

    return _load_template("client.py.tpl").substitute(
        protocol_blocks="\n".join(protocols).strip() + "\n",
        method_blocks=_indent("\n".join(method_blocks).strip() + "\n"),
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
        "from .client import Client\n"
        "from .transport import DefaultTransport, Transport\n\n"
        "__all__ = ['Client', 'DefaultTransport', 'Transport']\n"
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
