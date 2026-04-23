from __future__ import annotations

import keyword
import re
from collections.abc import Iterable

from .diagnostics import invalid_spec
from .model import FieldDef, NormalizedSpec, OperationDef, TypeAliasDef, TypedDictDef

_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
_METHODS_UPPER = {method.upper() for method in _METHODS}
_PRIMITIVES = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}
_SAFE = re.compile(r"[^a-zA-Z0-9_]")


def _snake(value: str) -> str:
    text = _SAFE.sub("_", value).strip("_") or "x"
    text = re.sub(r"_+", "_", text)
    if text[0].isdigit():
        text = f"_{text}"
    if keyword.iskeyword(text):
        text = f"{text}_"
    return text


def _name_parts(value: str) -> list[str]:
    cleaned = _SAFE.sub(" ", value)
    chunks = [chunk for chunk in cleaned.replace("_", " ").split() if chunk]
    parts: list[str] = []
    for chunk in chunks:
        parts.extend(
            re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+", chunk)
        )
    return parts or ["Generated"]


def _pascal(value: str) -> str:
    pieces = _name_parts(value)
    built: list[str] = []
    for piece in pieces:
        if piece.isupper() and len(piece) > 1:
            built.append(piece)
        elif piece.isdigit():
            built.append(piece)
        else:
            built.append(piece[0].upper() + piece[1:])
    name = "".join(built) or "Generated"
    if name[0].isdigit():
        name = f"T{name}"
    return name


def _type_name_from_hint(hint: str) -> str:
    if "_" in hint and hint.split("_", 1)[0] in _METHODS_UPPER:
        parts = [part for part in hint.split("_") if part]
        built = []
        for part in parts:
            if part in _METHODS_UPPER:
                built.append(part)
            else:
                built.append(_pascal(part))
        return "_".join(built)
    return _pascal(hint)


class _TypeBuilder:
    def __init__(self, components: dict) -> None:
        self.components = components
        self.typed_dicts: dict[str, TypedDictDef] = {}
        self.aliases: dict[str, TypeAliasDef] = {}
        self.aliases_by_signature: dict[tuple[tuple[str, ...], str], str] = {}
        self._processing: set[str] = set()

    def ensure_component(self, name: str) -> str:
        schemas = self.components.get("schemas") or {}
        schema = schemas.get(name)
        if schema is None:
            raise invalid_spec("Unresolved component schema reference", name)
        type_name = _pascal(name)
        if type_name in self.typed_dicts or type_name in self.aliases:
            return type_name
        self._schema_to_type(schema, type_name)
        return type_name

    def _union(self, variants: Iterable[str]) -> str:
        unique: list[str] = []
        for item in variants:
            if item not in unique:
                unique.append(item)
        return " | ".join(unique) if unique else "Any"

    def _schema_to_type(self, schema: dict, hint: str) -> str:
        if not isinstance(schema, dict):
            return "Any"

        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            return self.ensure_component(ref.rsplit("/", 1)[-1])

        if "enum" in schema and isinstance(schema["enum"], list):
            title = str(schema.get("title") or "")
            alias = _type_name_from_hint(hint)
            values_list = [repr(v) for v in schema["enum"]]
            if title:
                key = (tuple(values_list), title)
                existing = self.aliases_by_signature.get(key)
                if existing:
                    return existing
            values = ", ".join(values_list)
            self.aliases.setdefault(
                alias, TypeAliasDef(name=alias, annotation=f"Literal[{values}]")
            )
            if title:
                self.aliases_by_signature[(tuple(values_list), title)] = alias
            return alias

        one_of = schema.get("oneOf") or schema.get("anyOf")
        if isinstance(one_of, list) and one_of:
            return self._union(
                self._schema_to_type(item, f"{hint}Variant") for item in one_of
            )

        schema_type = schema.get("type")
        nullable = bool(schema.get("nullable"))
        if isinstance(schema_type, list):
            mapped = [
                "None" if t == "null" else self._schema_to_type({"type": t}, hint)
                for t in schema_type
            ]
            return self._union(mapped)

        if schema_type == "array":
            item_type = self._schema_to_type(schema.get("items") or {}, f"{hint}Item")
            base = f"list[{item_type}]"
            return f"{base} | None" if nullable else base

        if schema_type == "object" or "properties" in schema:
            name = _type_name_from_hint(hint)
            if name in self._processing:
                return name
            if name in self.typed_dicts:
                return name

            self._processing.add(name)
            props = schema.get("properties") or {}
            required = set(schema.get("required") or [])
            fields: list[FieldDef] = []
            for prop_name, prop_schema in props.items():
                prop_title = str((prop_schema or {}).get("title") or prop_name)
                field_type = self._schema_to_type(
                    prop_schema or {}, f"{name}{_pascal(prop_title)}"
                )
                fields.append(
                    FieldDef(
                        name=_snake(prop_name),
                        annotation=field_type,
                        required=prop_name in required,
                    )
                )

            self.typed_dicts[name] = TypedDictDef(name=name, fields=tuple(fields))
            self._processing.remove(name)
            return f"{name} | None" if nullable else name

        base = _PRIMITIVES.get(str(schema_type), "Any")
        return f"{base} | None" if nullable else base

    def schema_type(self, schema: dict, hint: str) -> str:
        return self._schema_to_type(schema or {}, hint)


def _path_symbol(path: str) -> str:
    return _snake(path.replace("{", "").replace("}", "").replace("/", "_"))


def _route_type_base(method: str, route_literal: str) -> str:
    segments = [segment for segment in route_literal.strip("/").split("/") if segment]
    if segments and segments[0].lower() == "api":
        segments = segments[1:]
    if not segments:
        segments = ["root"]
    normalized = [_pascal(segment.strip("{}")) for segment in segments]
    return f"{method.upper()}_{'_'.join(normalized)}"


def _resolve_parameter(param: dict, components: dict) -> dict | None:
    ref = param.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/parameters/"):
        name = ref.rsplit("/", 1)[-1]
        candidate = (components.get("parameters") or {}).get(name)
        if isinstance(candidate, dict):
            return candidate
        return None
    return param


def _merge_parameters(path_item: dict, operation: dict, components: dict) -> list[dict]:
    params = []
    for group in (path_item.get("parameters") or [], operation.get("parameters") or []):
        if not isinstance(group, list):
            continue
        for origin in group:
            if not isinstance(origin, dict):
                continue
            resolved = _resolve_parameter(origin, components)
            if isinstance(resolved, dict):
                params.append(resolved)
    return params


def normalize_openapi(document: dict, package_name: str) -> NormalizedSpec:
    components = document.get("components") or {}
    builder = _TypeBuilder(components)

    # Pre-register all component schemas so aliases and object names are stable.
    for schema_name in sorted((components.get("schemas") or {}).keys()):
        builder.ensure_component(schema_name)

    operations: list[OperationDef] = []
    for route_literal in sorted((document.get("paths") or {}).keys()):
        path_item = document["paths"].get(route_literal) or {}
        if not isinstance(path_item, dict):
            continue

        for method in _METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            symbol = _path_symbol(route_literal)
            op_base = _route_type_base(method, route_literal)
            protocol_name = f"_{method.upper()}_{_pascal(symbol)}"

            params = _merge_parameters(path_item, operation, components)
            path_props: dict[str, dict] = {}
            query_props: dict[str, dict] = {}
            header_props: dict[str, dict] = {}
            path_required: list[str] = []
            query_required: list[str] = []
            header_required: list[str] = []
            for param in params:
                location = param.get("in")
                name = str(param.get("name") or "")
                if not name:
                    continue
                schema = param.get("schema") or {}
                if location == "path":
                    path_props[name] = schema
                    if param.get("required", True):
                        path_required.append(name)
                elif location == "query":
                    query_props[name] = schema
                    if param.get("required", False):
                        query_required.append(name)
                elif location == "header":
                    header_props[name] = schema
                    if param.get("required", False):
                        header_required.append(name)

            if path_props:
                params_type = builder.schema_type(
                    {
                        "type": "object",
                        "properties": path_props,
                        "required": path_required,
                    },
                    f"{op_base}Params",
                )
            else:
                params_type = "dict[str, Any]"

            if query_props:
                query_type = builder.schema_type(
                    {
                        "type": "object",
                        "properties": query_props,
                        "required": query_required,
                    },
                    f"{op_base}Query",
                )
            else:
                query_type = "dict[str, Any]"

            if header_props:
                headers_type = builder.schema_type(
                    {
                        "type": "object",
                        "properties": header_props,
                        "required": header_required,
                    },
                    f"{op_base}Headers",
                )
            else:
                headers_type = "dict[str, Any]"

            request_body = operation.get("requestBody") or {}
            body_schema = None
            if isinstance(request_body, dict):
                content = request_body.get("content") or {}
                json_content = content.get("application/json") or {}
                body_schema = json_content.get("schema")

            body_type = None
            body_required = False
            if isinstance(body_schema, dict):
                body_type = builder.schema_type(body_schema, f"{op_base}Body")
                body_required = bool(request_body.get("required", False))

            responses = operation.get("responses") or {}
            response_schema = None
            for code in sorted(responses.keys()):
                if code.startswith("2"):
                    content = (responses.get(code) or {}).get("content") or {}
                    json_content = content.get("application/json") or {}
                    response_schema = json_content.get("schema")
                    if response_schema:
                        break

            response_type = "None"
            if isinstance(response_schema, dict):
                response_type = builder.schema_type(
                    response_schema, f"{op_base}Response"
                )

            operations.append(
                OperationDef(
                    method=method,
                    route_literal=route_literal,
                    symbol=symbol,
                    protocol_name=protocol_name,
                    params_type=params_type,
                    params_required=bool(path_required),
                    query_type=query_type,
                    headers_type=headers_type,
                    body_type=body_type,
                    body_required=body_required,
                    response_type=response_type,
                )
            )

    if not operations:
        raise invalid_spec("OpenAPI document contains no supported operations")

    typed_dicts = tuple(
        sorted(builder.typed_dicts.values(), key=lambda item: item.name)
    )
    aliases = tuple(sorted(builder.aliases.values(), key=lambda item: item.name))
    operations_tuple = tuple(
        sorted(operations, key=lambda item: (item.method, item.route_literal))
    )
    return NormalizedSpec(
        package_name=package_name,
        typed_dicts=typed_dicts,
        aliases=aliases,
        operations=operations_tuple,
    )
