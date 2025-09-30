from __future__ import annotations

import argparse
import json
import keyword
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # YAML optional


# -------------------------
# Helpers & type mappings
# -------------------------

PRIMITIVE_MAP = {
    ("null", None): "None",
    ("integer", None): "int",
    ("integer", "int32"): "int",
    ("integer", "int64"): "int",
    ("number", None): "float",
    ("number", "float"): "float",
    ("number", "double"): "float",
    ("string", None): "str",
    ("string", "byte"): "str",
    ("string", "binary"): "bytes",
    ("boolean", None): "bool",
    ("string", "date"): "date",
    ("string", "date-time"): "datetime",
}

SAFE_NAME_RE = re.compile(r"[^0-9a-zA-Z_]")


def safe_ident(name: str) -> str:
    name = SAFE_NAME_RE.sub("_", name)
    if not name:
        name = "x"
    if name[0].isdigit():
        name = "_" + name
    if keyword.iskeyword(name):
        name = name + "_"
    return name


def class_name_from_ref(ref: str) -> str:
    return safe_ident(ref.split("/")[-1])


def fmt_union(types: list[str]) -> str:
    """Format a PEP 604 union string."""
    seen: set[str] = set()
    ordered: list[str] = []
    has_none = False
    for t in types:
        if t == "None":
            has_none = True
            continue
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    if not ordered and has_none:
        return "None"
    if has_none:
        ordered.append("None")
    return (
        " | ".join(ordered) if len(ordered) > 1 else (ordered[0] if ordered else "Any")
    )


def py_type_from_schema(schema: Dict[str, Any], *, components: Dict[str, Any]) -> str:
    # $ref wins immediately
    if "$ref" in schema:
        return class_name_from_ref(schema["$ref"])

    # Constants / inline enums
    if "enum" in schema:
        vals = schema.get("enum") or []
        lit_items = ", ".join(literal_string(v) for v in vals)
        return f"Literal[{lit_items}]"

    if "const" in schema:
        return f"Literal[{literal_string(schema['const'])}]"

    # anyOf / oneOf -> union of subschemas
    for key in ("anyOf", "oneOf"):
        if key in schema:
            sub_types = [
                py_type_from_schema(s, components=components)
                for s in (schema.get(key) or [])
            ]
            # Handle OpenAPI 3.1 'null' pattern inside subschemas like {"type":"null"}
            sub_types = [
                "None" if t.lower() in {"none", "null"} else t for t in sub_types
            ]
            return fmt_union(sub_types)

    # OpenAPI 3.1: type can be a list, e.g. ["string", "null"]
    t = schema.get("type")
    fmt = schema.get("format")
    if isinstance(t, list):
        mapped: list[str] = []
        for ti in t:
            if ti == "null":
                mapped.append("None")
            elif ti == "array":
                items = schema.get("items") or {}
                mapped.append(
                    f"list[{py_type_from_schema(items, components=components)}]"
                )
            elif ti == "object":
                # Could be further specified, but keep broad
                mapped.append("dict[str, Any]")
            else:
                mapped.append(PRIMITIVE_MAP.get((ti, fmt), "Any"))
        return fmt_union(mapped)

    # Normal scalar/object/array
    if t == "array":
        items = schema.get("items") or {}
        item_t = py_type_from_schema(items, components=components)
        arr_t = f"list[{item_t}]"
        # Nullable arrays (OpenAPI 3.0 nullable: true)
        if schema.get("nullable") is True:
            return fmt_union([arr_t, "None"])
        return arr_t

    if t == "object":
        # (You can expand to TypedDicts later)
        obj_t = "dict[str, Any]"
        if schema.get("nullable") is True:
            return fmt_union([obj_t, "None"])
        return obj_t

    base = PRIMITIVE_MAP.get((t, fmt), "Any")
    if schema.get("nullable") is True and base != "None":
        return fmt_union([base, "None"])
    return base


def literal_string(s: str) -> str:
    return repr(s)


def path_to_symbol(path: str) -> str:
    """
    Map '/api/v1/queues/{queue_name}' -> 'api_v1_queues__queue_name_'
    Used for method names under routes.<verb>.
    """
    cleaned = path.lstrip("/")
    cleaned = cleaned.replace("/", "_").replace("{", "_").replace("}", "_")
    return safe_ident(cleaned)


def path_to_protocol_name(verb: str, path: str) -> str:
    return f"_{verb.upper()}_{path_to_symbol(path)}"


def sanitize_doc(
    summary: Optional[str], description: Optional[str], verb: str, path: str
) -> str:
    """
    Prefer full 'description' (single line normalized), otherwise 'summary', else 'VERB path'.
    """
    text = (
        (description or "").strip()
        or (summary or "").strip()
        or f"{verb.upper()} {path}"
    )
    text = re.sub(r"\s+", " ", text)
    return text.replace('"""', '\\"""')


# -------------------------
# Emit models
# -------------------------


def emit_models(components: Dict[str, Any]) -> str:
    schemas = components.get("schemas") or {}
    lines: List[str] = [
        "from __future__ import annotations",
        "from typing import Any, Optional, List, Dict, Literal",
        "from pydantic import BaseModel, Field",
        "from datetime import date, datetime",
        "from enum import Enum",
        "",
        "# Auto-generated Pydantic models",
        "",
    ]
    for name, schema in schemas.items():
        class_name = safe_ident(name)
        if "enum" in schema:
            enum_vals = schema.get("enum") or []
            typ = (schema.get("type") or "string").lower()
            base = "str" if typ == "string" else "int"
            # Build unique, valid member names
            members: List[str] = []
            seen_members: set[str] = set()
            for v in enum_vals:
                raw = str(v)
                m = raw.upper()
                m = re.sub(r"[^A-Z0-9]+", "_", m).strip("_")
                if not m or m[0].isdigit():
                    m = f"VALUE_{m}" if m else "VALUE"
                # ensure uniqueness
                i, cand = 1, m
                while cand in seen_members:
                    i += 1
                    cand = f"{m}_{i}"
                seen_members.add(cand)
                members.append(f"    {cand} = {literal_string(v)}")

            lines += [
                f"class {class_name}({base}, Enum):",
                *(members or ["    pass"]),
                "",
            ]
            continue

        if "allOf" in schema or "anyOf" in schema or "oneOf" in schema:
            lines += [
                f"class {class_name}(BaseModel):",
                "    __root__: Any",
                "",
            ]
            continue

        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        fields: List[str] = []
        for prop_name, prop_schema in props.items():
            py_name = safe_ident(prop_name)
            ty = py_type_from_schema(prop_schema, components=components)
            if prop_name not in required:
                if "None" not in ty.split(" | "):
                    ty = f"Optional[{ty}]"
                default = " = None"
            else:
                default = ""
            fields.append(f"    {py_name}: {ty}{default}")
        if not fields:
            fields = ["    pass"]
        lines += [f"class {class_name}(BaseModel):"] + fields + [""]

    return "\n".join(lines)


# -------------------------
# Operation helpers
# -------------------------


def choose_2xx_response(op: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    responses = op.get("responses") or {}
    for key in ["200", "201"]:
        if key in responses:
            return responses[key]
    for k, v in responses.items():
        try:
            if 200 <= int(k) < 300:
                return v
        except Exception:
            continue
    return None


def response_model_from_op(op: Dict[str, Any], *, components: Dict[str, Any]) -> str:
    res = choose_2xx_response(op)
    if not res:
        return "None"
    content = (res.get("content") or {}).get("application/json")
    if not content:
        return "None"
    schema = content.get("schema") or {}
    return py_type_from_schema(schema, components=components)


def request_body_model_from_op(
    op: Dict[str, Any], *, components: Dict[str, Any]
) -> Optional[str]:
    rb = op.get("requestBody")
    if not rb:
        return None
    content = (rb.get("content") or {}).get("application/json")
    if not content:
        return None
    schema = content.get("schema") or {}
    return py_type_from_schema(schema, components=components)


def collect_params(
    op: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    path_params: List[Dict[str, Any]] = []
    query_params: List[Dict[str, Any]] = []
    for p in op.get("parameters") or []:
        where = p.get("in")
        if where == "path":
            path_params.append(p)
        elif where == "query":
            query_params.append(p)
    return path_params, query_params


def param_decl_list(
    params: List[Dict[str, Any]], *, components: Dict[str, Any]
) -> List[str]:
    decls: List[str] = []
    for p in params:
        name = safe_ident(p["name"])
        required = bool(p.get("required"))
        schema = p.get("schema") or {}
        ty = py_type_from_schema(schema, components=components)
        if required:
            decls.append(f"{name}: {ty}")
        else:
            decls.append(f"{name}: {ty} | None = None")
    return decls


# -------------------------
# Emit client (Sync + Async, with Protocols, route classes, factories, union overload)
# -------------------------

type Route = Tuple[
    str, str, List[Dict[str, Any]], List[Dict[str, Any]], Optional[str], str, str
]


def emit_client(spec: Dict[str, Any]) -> str:
    components = spec.get("components") or {}
    paths = spec.get("paths") or {}

    verbs = ["get", "post", "put", "patch", "delete"]

    # verb -> list of tuples with all data needed
    # Route tuple: (path, proto_name, path_params, query_params, body_model, ret_model, docstring)

    routes_by_verb: Dict[str, List[Route]] = {v: [] for v in verbs}

    # Pre-collect
    for path, path_item in paths.items():
        for verb in verbs:
            if verb not in path_item:
                continue
            op = path_item[verb]
            proto = path_to_protocol_name(verb, path)
            path_params, query_params = collect_params(op)
            ret_model = response_model_from_op(op, components=components)
            body_model = request_body_model_from_op(op, components=components)
            doc = sanitize_doc(op.get("summary"), op.get("description"), verb, path)
            routes_by_verb[verb].append(
                (path, proto, path_params, query_params, body_model, ret_model, doc)
            )

    lines: List[str] = [
        "from __future__ import annotations",
        "from typing import Any, overload, Literal, Protocol, Awaitable",
        "from pydantic import BaseModel",
        "from .models import *  # noqa: F401,F403",
        "from ..runtime.base_client import BaseClient",
        "from ..runtime.async_base_client import AsyncBaseClient",
        "",
        "# === Route-specific call Protocols (used by factories & route methods) ===",
        "",
    ]

    # 1) Protocols (sync + async)
    for verb in verbs:
        for (
            path,
            proto_name,
            path_params,
            query_params,
            body_model,
            ret_model,
            _doc,
        ) in routes_by_verb[verb]:
            arg_decls = param_decl_list(
                path_params, components=components
            ) + param_decl_list(query_params, components=components)
            if arg_decls:
                kw_only = ", *"
                args_tail = ", " + ", ".join(arg_decls)
            else:
                kw_only = ""
                args_tail = ""
            body_tail = ""
            if body_model:
                if arg_decls:
                    body_tail = f", body: {body_model}"
                else:
                    kw_only = ", *"
                    body_tail = f", body: {body_model}"

            # Sync
            lines += [
                f"class {proto_name}(Protocol):",
                f"    def __call__(self{kw_only}{args_tail}{body_tail}) -> {ret_model}: ...",
                "",
            ]
            # Async
            lines += [
                f"class {proto_name}Async(Protocol):",
                f"    def __call__(self{kw_only}{args_tail}{body_tail}) -> Awaitable[{ret_model}]: ...",
                "",
            ]

    # 2) Route classes (sync)
    for verb in verbs:
        cls_name = f"Routes_{verb.capitalize()}"
        lines += [
            f"class {cls_name}:",
            "    def __init__(self, client: 'Client') -> None:",
            "        self._c = client",
            "",
        ]
        for (
            path,
            _proto_name,
            path_params,
            query_params,
            body_model,
            ret_model,
            doc,
        ) in routes_by_verb[verb]:
            mname = path_to_symbol(path)
            arg_decls = param_decl_list(
                path_params, components=components
            ) + param_decl_list(query_params, components=components)
            kw_only = ", *" if (arg_decls or body_model) else ""
            args_tail = (", " + ", ".join(arg_decls)) if arg_decls else ""
            body_tail = (f", body: {body_model}") if body_model else ""
            sig = f"(self{kw_only}{args_tail}{body_tail}) -> {ret_model}"
            lines += [
                f"    def {mname}{sig}:",
                f'        """{doc}"""',
                "        locals_map = {",
            ]
            for p in path_params + query_params:
                pn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: {pn},")
            if body_model:
                lines.append("            'body': body,")
            lines += ["        }"]
            lines += [
                "        _path_params = {",
            ]
            for p in path_params:
                pn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: locals_map.get('{pn}'),")
            lines += [
                "        }",
                "        _query = {",
            ]
            for p in query_params:
                qn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: locals_map.get('{qn}'),")
            lines += [
                "        }",
                "        _query = {k: v for k, v in _query.items() if v is not None}",
            ]
            if body_model:
                lines += [
                    "        body = locals_map.get('body')",
                    "        _json = body.model_dump(mode='json') if isinstance(body, BaseModel) else body",
                ]
            else:
                lines += ["        _json = None"]
            lines += [
                f"        _resp = self._c._request_json('{verb.upper()}', {literal_string(path)}, path_params=_path_params, query=_query, json_body=_json)",
                "        if _resp.headers.get('content-type','').startswith('application/json'):",
                "            data = _resp.json()",
            ]
            if ret_model != "None":
                lines += [
                    f"            return {ret_model}.model_validate(data) if hasattr({ret_model}, 'model_validate') else data"
                ]
            else:
                lines += ["            return None"]
            lines += [""]

    # 3) Route classes (async)
    for verb in verbs:
        cls_name = f"RoutesAsync_{verb.capitalize()}"
        lines += [
            f"class {cls_name}:",
            "    def __init__(self, client: 'AsyncClient') -> None:",
            "        self._c = client",
            "",
        ]
        for (
            path,
            _proto_name,
            path_params,
            query_params,
            body_model,
            ret_model,
            doc,
        ) in routes_by_verb[verb]:
            mname = path_to_symbol(path)
            arg_decls = param_decl_list(
                path_params, components=components
            ) + param_decl_list(query_params, components=components)
            kw_only = ", *" if (arg_decls or body_model) else ""
            args_tail = (", " + ", ".join(arg_decls)) if arg_decls else ""
            body_tail = (f", body: {body_model}") if body_model else ""
            sig = f"(self{kw_only}{args_tail}{body_tail}) -> {ret_model}"
            lines += [
                f"    async def {mname}{sig}:",
                f'        """{doc}"""',
                "        locals_map = {",
            ]
            for p in path_params + query_params:
                pn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: {pn},")
            if body_model:
                lines.append("            'body': body,")
            lines += ["        }"]
            lines += [
                "        _path_params = {",
            ]
            for p in path_params:
                pn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: locals_map.get('{pn}'),")
            lines += [
                "        }",
                "        _query = {",
            ]
            for p in query_params:
                qn = safe_ident(p["name"])
                lines.append(f"            {repr(p['name'])}: locals_map.get('{qn}'),")
            lines += [
                "        }",
                "        _query = {k: v for k, v in _query.items() if v is not None}",
            ]
            if body_model:
                lines += [
                    "        body = locals_map.get('body')",
                    "        _json = body.model_dump(mode='json') if isinstance(body, BaseModel) else body",
                ]
            else:
                lines += ["        _json = None"]
            lines += [
                f"        _resp = await self._c._request_json('{verb.upper()}', {literal_string(path)}, path_params=_path_params, query=_query, json_body=_json)",
                "        if _resp.headers.get('content-type','').startswith('application/json'):",
                "            data = _resp.json()",
            ]
            if ret_model != "None":
                lines += [
                    f"            return {ret_model}.model_validate(data) if hasattr({ret_model}, 'model_validate') else data"
                ]
            else:
                lines += ["            return None"]
            lines += [""]

    # 4) Routes containers
    lines += [
        "class Routes:",
        "    def __init__(self, client: 'Client') -> None:",
        "        self.get = Routes_Get(client)",
        "        self.post = Routes_Post(client)",
        "        self.put = Routes_Put(client)",
        "        self.patch = Routes_Patch(client)",
        "        self.delete = Routes_Delete(client)",
        "",
        "class RoutesAsync:",
        "    def __init__(self, client: 'AsyncClient') -> None:",
        "        self.get = RoutesAsync_Get(client)",
        "        self.post = RoutesAsync_Post(client)",
        "        self.put = RoutesAsync_Put(client)",
        "        self.patch = RoutesAsync_Patch(client)",
        "        self.delete = RoutesAsync_Delete(client)",
        "",
    ]

    # 5) Client (sync)
    lines += [
        "class Client(BaseClient):",
        "    def __init__(self, *a, **kw) -> None:",
        "        super().__init__(*a, **kw)",
        "        self.routes = Routes(self)",
        "",
    ]

    # Factories: <verb>_route (sync): specific overloads with docstrings, final union overload, then implementation
    for verb in verbs:
        verb_routes = routes_by_verb[verb]
        # Specific overloads with docstrings
        for path, proto_name, *_rest, doc in verb_routes:
            lines.append("    @overload")
            lines.append(
                f"    def {verb}_route(self, path: Literal[{literal_string(path)}]) -> {proto_name}:"
            )
            lines.append(f'        """{doc}"""')
            lines.append("        ...")
        # Final union overload (for IntelliSense)
        if verb_routes:
            seen: set[str] = set()
            uniq_paths = [
                p for (p, *_r) in verb_routes if not (p in seen or seen.add(p))
            ]
            if len(uniq_paths) <= 4:
                union = ", ".join(literal_string(p) for p in uniq_paths)
                lines.append("    @overload")
                lines.append(
                    f"    def {verb}_route(self, path: Literal[{union}]) -> Any: ..."
                )
            else:
                lines.append("    @overload")
                lines.append(f"    def {verb}_route(self, path: " + "Literal[")
                for p in uniq_paths:
                    lines.append(f"            {literal_string(p)},")
                lines.append("        ]) -> Any: ...")
        # Implementation
        if verb_routes:
            lines += [
                f"    def {verb}_route(self, path: str):",
                "        def _caller(**kw):",
                "            locals_map = dict(kw)",
                "            # Generated per-route branches",
            ]
            for (
                path,
                _proto,
                path_params,
                query_params,
                body_model,
                ret_model,
                _doc,
            ) in verb_routes:
                lines.append(f"            if path == {literal_string(path)}:")
                lines.append("                _path_params = {")
                for p in path_params:
                    pn = safe_ident(p["name"])
                    lines.append(
                        f"                    {repr(p['name'])}: locals_map.get('{pn}'),"
                    )
                lines.append("                }")
                lines.append("                _query = {")
                for p in query_params:
                    qn = safe_ident(p["name"])
                    lines.append(
                        f"                    {repr(p['name'])}: locals_map.get('{qn}'),"
                    )
                lines.append("                }")
                lines.append(
                    "                _query = {k: v for k, v in _query.items() if v is not None}"
                )
                if body_model:
                    lines.append("                body = locals_map.get('body')")
                    lines.append(
                        "                _json = body.model_dump(mode='json') if isinstance(body, BaseModel) else body"
                    )
                else:
                    lines.append("                _json = None")
                lines.append(
                    f"                _resp = self._request_json('{verb.upper()}', path, path_params=_path_params, query=_query, json_body=_json)"
                )
                lines.append(
                    "                if _resp.headers.get('content-type','').startswith('application/json'):"
                )
                lines.append("                    data = _resp.json()")
                if ret_model != "None":
                    lines.append(
                        f"                    return {ret_model}.model_validate(data) if hasattr({ret_model}, 'model_validate') else data"
                    )
                else:
                    lines.append("                    return None")
            lines += [
                "            # Fallback generic",
                f"            _resp = self._request_json('{verb.upper()}', path, path_params={{}}, query=locals_map, json_body=locals_map.get('body'))",
                "            if _resp.headers.get('content-type','').startswith('application/json'):",
                "                return _resp.json()",
                "            return None",
                "        return _caller",
                "",
            ]
        else:
            lines += [
                f"    def {verb}_route(self, path: str):",
                "        def _caller(**kw):",
                "            raise NotImplementedError('No routes for this verb in the spec')",
                "        return _caller",
                "",
            ]

    # Dynamic convenience (sync)
    for verb in verbs:
        lines += [
            f"    def {verb}(self, path: str, **kwargs):",
            f'        """Dynamic convenience; for typed UX, prefer self.routes.{verb}.<route>(...) or {verb}_route(Literal[path])."""',
            f"        return self.{verb}_route(path)(**kwargs)",
            "",
        ]

    # 6) AsyncClient
    lines += [
        "class AsyncClient(AsyncBaseClient):",
        "    def __init__(self, *a, **kw) -> None:",
        "        super().__init__(*a, **kw)",
        "        self.routes = RoutesAsync(self)",
        "",
    ]

    # Async factories per verb
    for verb in verbs:
        verb_routes = routes_by_verb[verb]
        # Specific async overloads (docstrings)
        for path, proto_name, *_rest, doc in verb_routes:
            lines.append("    @overload")
            lines.append(
                f"    def {verb}_route(self, path: Literal[{literal_string(path)}]) -> {proto_name}Async:"
            )
            lines.append(f'        """{doc}"""')
            lines.append("        ...")
        # Final union overload (Any)
        if verb_routes:
            seen: set[str] = set()
            uniq_paths = [
                p for (p, *_r) in verb_routes if not (p in seen or seen.add(p))
            ]
            if len(uniq_paths) <= 4:
                union = ", ".join(literal_string(p) for p in uniq_paths)
                lines.append("    @overload")
                lines.append(
                    f"    def {verb}_route(self, path: Literal[{union}]) -> Any: ..."
                )
            else:
                lines.append("    @overload")
                lines.append(f"    def {verb}_route(self, path: " + "Literal[")
                for p in uniq_paths:
                    lines.append(f"            {literal_string(p)},")
                lines.append("        ]) -> Any: ...")
        # Implementation returns async closure
        if verb_routes:
            lines += [
                f"    def {verb}_route(self, path: str):",
                "        async def _caller(**kw):",
                "            locals_map = dict(kw)",
                "            # Generated per-route branches",
            ]
            for (
                path,
                _proto,
                path_params,
                query_params,
                body_model,
                ret_model,
                _doc,
            ) in verb_routes:
                lines.append(f"            if path == {literal_string(path)}:")
                lines.append("                _path_params = {")
                for p in path_params:
                    pn = safe_ident(p["name"])
                    lines.append(
                        f"                    {repr(p['name'])}: locals_map.get('{pn}'),"
                    )
                lines.append("                }")
                lines.append("                _query = {")
                for p in query_params:
                    qn = safe_ident(p["name"])
                    lines.append(
                        f"                    {repr(p['name'])}: locals_map.get('{qn}'),"
                    )
                lines.append("                }")
                lines.append(
                    "                _query = {k: v for k, v in _query.items() if v is not None}"
                )
                if body_model:
                    lines.append("                body = locals_map.get('body')")
                    lines.append(
                        "                _json = body.model_dump(mode='json') if isinstance(body, BaseModel) else body"
                    )
                else:
                    lines.append("                _json = None")
                lines.append(
                    f"                _resp = await self._request_json('{verb.upper()}', path, path_params=_path_params, query=_query, json_body=_json)"
                )
                lines.append(
                    "                if _resp.headers.get('content-type','').startswith('application/json'):"
                )
                lines.append("                    data = _resp.json()")
                if ret_model != "None":
                    lines.append(
                        f"                    return {ret_model}.model_validate(data) if hasattr({ret_model}, 'model_validate') else data"
                    )
                else:
                    lines.append("                    return None")
            lines += [
                "            # Fallback generic",
                f"            _resp = await self._request_json('{verb.upper()}', path, path_params={{}}, query=locals_map, json_body=locals_map.get('body'))",
                "            if _resp.headers.get('content-type','').startswith('application/json'):",
                "                return _resp.json()",
                "            return None",
                "        return _caller",
                "",
            ]
        else:
            lines += [
                f"    def {verb}_route(self, path: str):",
                "        async def _caller(**kw):",
                "            raise NotImplementedError('No routes for this verb in the spec')",
                "        return _caller",
                "",
            ]

    # Dynamic convenience (async)
    for verb in verbs:
        lines += [
            f"    async def {verb}(self, path: str, **kwargs):",
            f'        """Dynamic convenience; for typed UX, prefer self.routes.{verb}.<route>(...) or {verb}_route(Literal[path])."""',
            f"        return await self.{verb}_route(path)(**kwargs)",
            "",
        ]

    return "\n".join(lines)


def emit_init(package_name: str) -> str:
    # Re-export both clients
    return "from .client import Client, AsyncClient\n"


# -------------------------
# Generate files
# -------------------------


def copy_runtime(out_dir: Path) -> None:
    base_here = Path(__file__).resolve().parent / "runtime"
    runtime_dir = out_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "__init__.py").write_text("", encoding="utf-8")
    for fname in ("base_client.py", "async_base_client.py"):
        (runtime_dir / fname).write_text(
            (base_here / fname).read_text(encoding="utf-8"), encoding="utf-8"
        )


def _write_from_spec(spec: Dict[str, Any], out_dir: Path, package_name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "__init__.py").write_text(
        "from .api_client import models", encoding="utf-8"
    )

    # copy runtime (sync + async)
    base_here = Path(__file__).resolve().parent / "runtime"
    runtime_dir = out_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "__init__.py").write_text("", encoding="utf-8")
    for fname in ("base_client.py", "async_base_client.py"):
        (runtime_dir / fname).write_text(
            (base_here / fname).read_text(encoding="utf-8"), encoding="utf-8"
        )

    pkg_dir = out_dir / package_name
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "__init__.py").write_text(
        "from .client import Client, AsyncClient\n", encoding="utf-8"
    )

    components = spec.get("components") or {}
    (pkg_dir / "models.py").write_text(emit_models(components), encoding="utf-8")
    (pkg_dir / "client.py").write_text(emit_client(spec), encoding="utf-8")


def load_spec(spec_path: Path) -> Dict[str, Any]:
    txt = spec_path.read_text(encoding="utf-8")
    if spec_path.suffix.lower() in {".yaml", ".yml"}:
        import yaml  # local import to keep optional

        return yaml.safe_load(txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        import yaml

        return yaml.safe_load(txt)


def generate_from_dict(spec: Dict[str, Any], out_dir: Path, package_name: str) -> None:
    _write_from_spec(spec, out_dir, package_name)


def generate(spec_path: Path, out_dir: Path, package_name: str) -> None:
    spec = load_spec(spec_path)
    _write_from_spec(spec, out_dir, package_name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Path to openapi.json or .yaml/.yml")
    ap.add_argument("--out", required=True, help="Output directory (package root)")
    ap.add_argument(
        "--package", default="api_client", help="Generated package name (module-safe)"
    )
    args = ap.parse_args()

    spec_path = Path(args.spec)
    out_dir = Path(args.out)
    package_name = safe_ident(args.package)

    generate(spec_path, out_dir, package_name)


if __name__ == "__main__":
    main()
