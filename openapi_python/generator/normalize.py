from __future__ import annotations

import keyword
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from ..utils import safe_get
from .diagnostics import invalid_spec
from .model import (
    EnumDef,
    FieldDef,
    NormalizedSpec,
    OperationDef,
    TypeAliasDef,
    TypedDictDef,
)

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
    """
    Converts a string to a safe snake_case identifier.
    """
    text = _SAFE.sub("_", value).strip("_") or "x"
    text = re.sub(r"_+", "_", text)
    if text[0].isdigit():
        text = f"_{text}"
    if keyword.iskeyword(text):
        text = f"{text}_"
    return text


def _pascal(value: str) -> str:
    """Converts a string to a safe PascalCase identifier."""
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


def _name_parts(value: str) -> list[str]:
    """
    Splits a string into parts suitable for identifier construction.
    Non-alphanumeric characters are treated as separators. Consecutive uppercase letters are kept together.
    """
    cleaned = _SAFE.sub(" ", value)
    chunks = [chunk for chunk in cleaned.replace("_", " ").split() if chunk]
    parts: list[str] = []
    for chunk in chunks:
        # A part is either a sequence of uppercase letters followed by lowercase letters or digits (e.g. "HTTPServer2"),
        parts.extend(
            re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+", chunk)
        )
    return parts or ["Generated"]


def _type_name_from_hint(hint: str) -> str:
    """
    Converts a hint string to a suitable type name.
    If the hint contains an HTTP method followed by
    an underscore, that method is preserved in uppercase
    and the rest of the hint is converted to PascalCase.
    """
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


@dataclass(frozen=True)
class _TypeState:
    components: dict
    component_type_names: dict[str, str] = field(default_factory=dict)
    typed_dicts: dict[str, TypedDictDef] = field(default_factory=dict)
    aliases: dict[str, TypeAliasDef] = field(default_factory=dict)
    enums: dict[str, EnumDef] = field(default_factory=dict)
    aliases_by_signature: dict[tuple[tuple[str, ...], str], str] = field(
        default_factory=dict
    )
    processing: frozenset[str] = frozenset()


def _is_registered_type_name(state: _TypeState, name: str) -> bool:
    return name in state.typed_dicts or name in state.aliases or name in state.enums


def _is_used_type_name(state: _TypeState, name: str) -> bool:
    return name in state.component_type_names.values() or _is_registered_type_name(
        state, name
    )


def _is_unique_type_name(state: _TypeState, name: str) -> str:
    if not _is_used_type_name(state, name):
        return name

    index = 2
    while _is_used_type_name(state, f"{name}{index}"):
        index += 1
    return f"{name}{index}"


def _with_component_type_name(
    state: _TypeState, component_name: str, type_name: str
) -> _TypeState:
    return _TypeState(
        components=state.components,
        component_type_names={
            **state.component_type_names,
            component_name: type_name,
        },
        typed_dicts=state.typed_dicts,
        aliases=state.aliases,
        enums=state.enums,
        aliases_by_signature=state.aliases_by_signature,
        processing=state.processing,
    )


def _with_enum(state: _TypeState, enum: EnumDef) -> _TypeState:
    return _TypeState(
        components=state.components,
        component_type_names=state.component_type_names,
        typed_dicts=state.typed_dicts,
        aliases=state.aliases,
        enums={**state.enums, enum.name: enum},
        aliases_by_signature=state.aliases_by_signature,
        processing=state.processing,
    )


def _with_alias(
    state: _TypeState,
    alias: TypeAliasDef,
    signature: tuple[tuple[str, ...], str] | None = None,
) -> _TypeState:
    aliases = state.aliases
    if alias.name not in aliases:
        aliases = {**aliases, alias.name: alias}

    aliases_by_signature = state.aliases_by_signature
    if signature is not None:
        aliases_by_signature = {**aliases_by_signature, signature: alias.name}

    return _TypeState(
        components=state.components,
        component_type_names=state.component_type_names,
        typed_dicts=state.typed_dicts,
        aliases=aliases,
        enums=state.enums,
        aliases_by_signature=aliases_by_signature,
        processing=state.processing,
    )


def _with_typeddict(state: _TypeState, typed_dict: TypedDictDef) -> _TypeState:
    return _TypeState(
        components=state.components,
        component_type_names=state.component_type_names,
        typed_dicts={**state.typed_dicts, typed_dict.name: typed_dict},
        aliases=state.aliases,
        enums=state.enums,
        aliases_by_signature=state.aliases_by_signature,
        processing=state.processing,
    )


def _with_processing(state: _TypeState, name: str) -> _TypeState:
    return _TypeState(
        components=state.components,
        component_type_names=state.component_type_names,
        typed_dicts=state.typed_dicts,
        aliases=state.aliases,
        enums=state.enums,
        aliases_by_signature=state.aliases_by_signature,
        processing=state.processing | {name},
    )


def _without_processing(state: _TypeState, name: str) -> _TypeState:
    return _TypeState(
        components=state.components,
        component_type_names=state.component_type_names,
        typed_dicts=state.typed_dicts,
        aliases=state.aliases,
        enums=state.enums,
        aliases_by_signature=state.aliases_by_signature,
        processing=state.processing - {name},
    )


def _union(variants: Iterable[str]) -> str:
    unique: list[str] = []
    for item in variants:
        if item not in unique:
            unique.append(item)
    return " | ".join(unique) if unique else "Any"


def _ensure_component(state: _TypeState, name: str) -> tuple[str, _TypeState]:
    """
    Ensures that a component schema is registered as a type.
    """
    existing = state.component_type_names.get(name)
    if existing is not None:
        return existing, state

    schema = safe_get(state.components, "schemas", name, type=dict)
    if schema is None:
        raise invalid_spec("Unresolved component schema reference", name)

    type_name = _is_unique_type_name(state, _pascal(name))

    state = _with_component_type_name(state, name, type_name)
    _, state = _schema_to_type(state, schema, type_name, component_name=name)
    return type_name, state


def _nullable(annotation: str, nullable: bool) -> str:
    return f"{annotation} | None" if nullable else annotation


def _schema_enum_to_type(
    state: _TypeState,
    schema: dict,
    hint: str,
    component_name: str | None,
) -> tuple[str, _TypeState]:
    values = schema["enum"]
    if component_name is not None:
        # Component-level enums are rendered as actual reusable Enum classes
        enum = EnumDef(name=hint, values=tuple(values))
        return enum.name, _with_enum(state, enum)

    # Inline enums are just rendered as literals
    title = str(schema.get("title") or "")
    alias_name = _type_name_from_hint(hint)
    values_list = [repr(v) for v in values]
    signature = (tuple(values_list), title) if title else None
    if signature is not None:
        existing = state.aliases_by_signature.get(signature)
        if existing:
            return existing, state

    literal_values = ", ".join(values_list)
    alias = TypeAliasDef(name=alias_name, annotation=f"Literal[{literal_values}]")
    return alias_name, _with_alias(state, alias, signature)


def _schema_union_to_type(
    state: _TypeState, schemas: list, hint: str
) -> tuple[str, _TypeState]:
    variants: list[str] = []
    for item in schemas:
        item_type, state = _schema_to_type(state, item, f"{hint}Variant")
        variants.append(item_type)
    return _union(variants), state


def _schema_type_list_to_type(
    state: _TypeState, schema_types: list, hint: str
) -> tuple[str, _TypeState]:
    mapped: list[str] = []
    for schema_type in schema_types:
        if schema_type == "null":
            mapped.append("None")
            continue
        item_type, state = _schema_to_type(state, {"type": schema_type}, hint)
        mapped.append(item_type)
    return _union(mapped), state


def _schema_array_to_type(
    state: _TypeState, schema: dict, hint: str
) -> tuple[str, _TypeState]:
    nullable = bool(schema.get("nullable"))
    prefix_items = safe_get(schema, "prefixItems", type=list)
    if prefix_items is not None:
        item_types: list[str] = []
        for item in prefix_items:
            item_type, state = _schema_to_type(state, item, f"{hint}Item")
            item_types.append(item_type)
        return _nullable(f"tuple[{', '.join(item_types)}]", nullable), state

    item_schema = safe_get(schema, "items", type=dict) or {}
    item_type, state = _schema_to_type(state, item_schema, f"{hint}Item")
    return _nullable(f"list[{item_type}]", nullable), state


def _schema_map_to_type(
    state: _TypeState, schema: dict, hint: str
) -> tuple[str, _TypeState]:
    nullable = bool(schema.get("nullable"))
    additional_properties = schema["additionalProperties"]
    value_type, state = _schema_to_type(state, additional_properties, f"{hint}Value")
    return _nullable(f"dict[str, {value_type}]", nullable), state


def _schema_object_to_type(
    state: _TypeState, schema: dict, hint: str
) -> tuple[str, _TypeState]:
    nullable = bool(schema.get("nullable"))
    name = _type_name_from_hint(hint)
    if name in state.processing:
        return name, state
    if name in state.typed_dicts:
        return name, state

    state = _with_processing(state, name)
    props = safe_get(schema, "properties", type=dict) or {}
    required = set(safe_get(schema, "required", type=list) or [])
    fields: list[FieldDef] = []
    for prop_name, prop_schema in props.items():
        prop_title = str(safe_get(prop_schema, "title") or prop_name)
        prop_schema = safe_get(props, prop_name, type=dict) or {}
        field_type, state = _schema_to_type(
            state, prop_schema, f"{name}{_pascal(prop_title)}"
        )
        fields.append(
            FieldDef(
                name=prop_name,
                annotation=field_type,
                required=prop_name in required,
            )
        )

    state = _without_processing(state, name)
    state = _with_typeddict(state, TypedDictDef(name=name, fields=tuple(fields)))
    return _nullable(name, nullable), state


def _schema_to_type(
    state: _TypeState,
    schema: dict,
    hint: str,
    *,
    component_name: str | None = None,
) -> tuple[str, _TypeState]:
    """
    Takes a JSON schema object and returns the corresponding Python
    type annotation along with an updated state containing any new
    type definitions.
    """
    if not schema:
        return "Any", state

    schema_type = schema.get("type")
    nullable = bool(schema.get("nullable"))
    if schema_type == "null":
        return "None", state

    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        component = ref.rsplit("/", 1)[-1]
        return _ensure_component(state, component)

    if "const" in schema:
        return f"Literal[{schema['const']!r}]", state

    if schema_type == "string" and schema.get("format") == "binary":
        return "bytes", state

    if "enum" in schema and isinstance(schema["enum"], list):
        return _schema_enum_to_type(state, schema, hint, component_name)

    one_of = safe_get(schema, "oneOf", type=list) or safe_get(
        schema, "anyOf", type=list
    )
    if one_of:
        return _schema_union_to_type(state, one_of, hint)

    if isinstance(schema_type, list):
        return _schema_type_list_to_type(state, schema_type, hint)

    if schema_type == "array":
        return _schema_array_to_type(state, schema, hint)

    additional_properties = safe_get(schema, "additionalProperties", type=dict)
    if (
        schema_type == "object"
        and "properties" not in schema
        and additional_properties is not None
    ):
        return _schema_map_to_type(state, schema, hint)

    if schema_type == "object" or "properties" in schema:
        return _schema_object_to_type(state, schema, hint)

    base = _PRIMITIVES.get(str(schema_type), "Any")
    return _nullable(base, nullable), state


def _schema_type(state: _TypeState, schema: dict, hint: str) -> tuple[str, _TypeState]:
    return _schema_to_type(state, schema or {}, hint)


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
        candidate = safe_get(components, "parameters", name, type=dict)
        if candidate is not None:
            return candidate
        return None
    return param


def _merge_parameters(path_item: dict, operation: dict, components: dict) -> list[dict]:
    params = []
    for group in (
        safe_get(path_item, "parameters", type=list) or [],
        safe_get(operation, "parameters", type=list) or [],
    ):
        if not isinstance(group, list):
            continue
        for origin in group:
            if not isinstance(origin, dict):
                continue
            resolved = _resolve_parameter(origin, components)
            if isinstance(resolved, dict):
                params.append(resolved)
    return params


@dataclass(frozen=True)
class _ParameterBucket:
    props: dict[str, dict] = field(default_factory=dict)
    required: tuple[str, ...] = ()


def _collect_parameter_buckets(
    params: list[dict],
) -> tuple[_ParameterBucket, _ParameterBucket, _ParameterBucket]:
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
        schema = safe_get(param, "schema", type=dict) or {}
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
    return (
        _ParameterBucket(path_props, tuple(path_required)),
        _ParameterBucket(query_props, tuple(query_required)),
        _ParameterBucket(header_props, tuple(header_required)),
    )


def _bucket_type(
    state: _TypeState,
    bucket: _ParameterBucket,
    hint: str,
    default: str = "dict[str, Any]",
) -> tuple[str, _TypeState]:
    if not bucket.props:
        return default, state
    return _schema_type(
        state,
        {
            "type": "object",
            "properties": bucket.props,
            "required": bucket.required,
        },
        hint,
    )


def _request_body_type(
    state: _TypeState,
    operation: dict,
    hint: str,
) -> tuple[str | None, bool, _TypeState]:
    """
    Determines the type of the request body for an operation, if any.
    Returns a tuple of (body_type, required, updated_state).
    The body_type is a string representing the Python type annotation for the request body.
    The required flag indicates whether the request body is required.
    The updated_state is the new _TypeState after processing the request body schema.
    """
    request_body = safe_get(operation, "requestBody", type=dict)
    if request_body is None:
        return None, False, state

    for content_type in ("application/json", "multipart/form-data"):
        schema = safe_get(request_body, "content", content_type, "schema", type=dict)
        if schema is not None:
            body_type, state = _schema_type(state, schema, hint)
            return body_type, bool(request_body.get("required", False)), state

    return None, False, state


def _response_type(
    state: _TypeState, operation: dict, hint: str
) -> tuple[str, _TypeState]:
    responses = safe_get(operation, "responses", type=dict) or {}
    response_types: list[str] = []

    for code in sorted(responses.keys()):
        if not code.startswith("2"):
            # Only consider 2xx responses for the main response type
            continue

        schema = safe_get(
            responses, code, "content", "application/json", "schema", type=dict
        )
        if schema is not None:
            if not schema:
                response_types.append("None")
            else:
                response_type, state = _schema_type(state, schema, hint)
                response_types.append(response_type)
        else:
            response_types.append("None")
    return _union(response_types), state


def normalize_openapi(document: dict, package_name: str) -> NormalizedSpec:
    """
    Normalizes an OpenAPI document into a NormalizedSpec for code generation.
    """
    components = safe_get(document, "components", type=dict) or {}
    state = _TypeState(components=components)

    # Pre-register all component schemas so aliases and object names are stable.
    schemas = safe_get(components, "schemas", type=dict) or {}
    for schema_name in sorted(schemas.keys()):
        _, state = _ensure_component(state, schema_name)

    operations: list[OperationDef] = []
    paths = safe_get(document, "paths", type=dict) or {}
    for route_literal in sorted(paths.keys()):
        path_item = safe_get(paths, route_literal, type=dict)
        if path_item is None:
            continue

        for method in _METHODS:
            operation = safe_get(path_item, method, type=dict)
            if operation is None:
                continue

            symbol = _path_symbol(route_literal)
            op_base = _route_type_base(method, route_literal)
            protocol_name = f"_{method.upper()}_{_pascal(symbol)}"

            params = _merge_parameters(path_item, operation, components)
            path_bucket, query_bucket, header_bucket = _collect_parameter_buckets(
                params
            )

            params_type, state = _bucket_type(state, path_bucket, f"{op_base}Params")
            query_type, state = _bucket_type(state, query_bucket, f"{op_base}Query")
            headers_type, state = _bucket_type(
                state, header_bucket, f"{op_base}Headers"
            )

            body_type, body_required, state = _request_body_type(
                state, operation, f"{op_base}Body"
            )
            response_type, state = _response_type(
                state, operation, f"{op_base}Response"
            )

            operations.append(
                OperationDef(
                    method=method,
                    route_literal=route_literal,
                    symbol=symbol,
                    protocol_name=protocol_name,
                    params_type=params_type,
                    params_required=bool(path_bucket.required),
                    query_type=query_type,
                    query_required=bool(query_bucket.required),
                    headers_type=headers_type,
                    headers_required=bool(header_bucket.required),
                    body_type=body_type,
                    body_required=body_required,
                    response_type=response_type,
                )
            )

    if not operations:
        raise invalid_spec("OpenAPI document contains no supported operations")

    typed_dicts = tuple(sorted(state.typed_dicts.values(), key=lambda item: item.name))
    aliases = tuple(sorted(state.aliases.values(), key=lambda item: item.name))
    enums = tuple(sorted(state.enums.values(), key=lambda item: item.name))
    operations_tuple = tuple(
        sorted(operations, key=lambda item: (item.method, item.route_literal))
    )
    return NormalizedSpec(
        package_name=package_name,
        typed_dicts=typed_dicts,
        aliases=aliases,
        enums=enums,
        operations=operations_tuple,
    )
