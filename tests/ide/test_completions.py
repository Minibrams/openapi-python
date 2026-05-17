from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import pytest

from openapi_python.generator import GenerationRequest, generate_client


class CompletionServer(Protocol):
    def completion_labels(self, source: str) -> set[str]: ...


def _string_schema() -> dict[str, str]:
    return {"type": "string"}


@pytest.fixture(scope="module")
def ide_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("ide-completions")
    (workspace / "pyproject.toml").write_text(
        '[tool.ty.environment]\npython-version = "3.12"\n',
        encoding="utf-8",
    )

    result = generate_client(
        GenerationRequest(
            output_dir=workspace / "generated",
            spec_json=json.dumps(_openapi_spec()),
            overwrite=True,
        )
    )
    assert result.success
    return workspace


def _openapi_spec() -> dict[str, object]:
    ok_response = {
        "description": "OK",
        "content": {"application/json": {"schema": {"type": "object"}}},
    }
    user_response = {
        "description": "OK",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
        },
    }

    return {
        "openapi": "3.1.0",
        "info": {"title": "IDE Completion API", "version": "1.0.0"},
        "paths": {
            "/status": {"get": {"responses": {"200": ok_response}}},
            "/teams/{team_id}/members/{user_id}": {
                "put": {
                    "parameters": [
                        _path_parameter("team_id"),
                        _path_parameter("user_id"),
                    ],
                    "responses": {"200": ok_response},
                }
            },
            "/users": {
                "get": {
                    "parameters": [
                        _query_parameter("tenant", required=True),
                        _query_parameter("page"),
                        _query_parameter("search"),
                        _query_parameter("filter[status]"),
                    ],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "requestBody": _json_body("#/components/schemas/UserCreate"),
                    "responses": {"201": user_response},
                },
            },
            "/users/{user_id}": {
                "parameters": [_path_parameter("user_id")],
                "get": {
                    "parameters": [
                        _query_parameter("include_disabled"),
                        _header_parameter("X-Trace-Id"),
                        _header_parameter("X-Client-Version"),
                    ],
                    "responses": {"200": user_response},
                },
                "patch": {
                    "requestBody": _json_body(
                        "#/components/schemas/UserPatch", required=False
                    ),
                    "responses": {"200": user_response},
                },
                "delete": {"responses": {"204": {"description": "Deleted"}}},
            },
            "/users/{user_id}/posts/{post_id}/comments": {
                "post": {
                    "parameters": [
                        _path_parameter("user_id"),
                        _path_parameter("post_id"),
                    ],
                    "requestBody": _json_body("#/components/schemas/CommentCreate"),
                    "responses": {"200": ok_response},
                }
            },
        },
        "components": {
            "schemas": {
                "Address": {
                    "type": "object",
                    "required": ["street", "city"],
                    "properties": {
                        "street": _string_schema(),
                        "city": _string_schema(),
                        "postal_code": _string_schema(),
                    },
                },
                "CommentCreate": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": _string_schema(),
                        "visibility": _string_schema(),
                    },
                },
                "User": {
                    "type": "object",
                    "required": ["id", "name"],
                    "properties": {
                        "id": {"type": "integer"},
                        "name": _string_schema(),
                    },
                },
                "UserCreate": {
                    "type": "object",
                    "required": ["name", "email", "address"],
                    "properties": {
                        "name": _string_schema(),
                        "email": _string_schema(),
                        "role": {
                            "type": "string",
                            "enum": ["admin", "member", "viewer"],
                        },
                        "address": {"$ref": "#/components/schemas/Address"},
                    },
                },
                "UserPatch": {
                    "type": "object",
                    "properties": {
                        "name": _string_schema(),
                        "email": _string_schema(),
                        "address": {"$ref": "#/components/schemas/Address"},
                    },
                },
            }
        },
    }


def _path_parameter(name: str) -> dict[str, object]:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "schema": _string_schema(),
    }


def _query_parameter(name: str, *, required: bool = False) -> dict[str, object]:
    return {
        "name": name,
        "in": "query",
        "required": required,
        "schema": _string_schema(),
    }


def _header_parameter(name: str) -> dict[str, object]:
    return {
        "name": name,
        "in": "header",
        "schema": _string_schema(),
    }


def _json_body(schema_ref: str, *, required: bool = True) -> dict[str, object]:
    return {
        "required": required,
        "content": {"application/json": {"schema": {"$ref": schema_ref}}},
    }


def test_get_route_completions(ty_server: CompletionServer) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.get('<CURSOR>')
""")

    assert {"/status", "/users", "/users/{user_id}"} <= labels


def test_post_route_completions(ty_server: CompletionServer) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.post('<CURSOR>')
""")

    assert {"/users", "/users/{user_id}/posts/{post_id}/comments"} <= labels


def test_async_put_route_completions(ty_server: CompletionServer) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import AsyncClient

client = AsyncClient(base_url='https://example.test')

client.put('<CURSOR>')
""")

    assert {"/teams/{team_id}/members/{user_id}"} <= labels


def test_route_completions_in_partial_route(ty_server: CompletionServer) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.get('/user<CURSOR>')
""")

    assert {"/users", "/users/{user_id}"} <= labels


def test_path_param_completions_in_incomplete_params_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.get('/users/{user_id}')(params={'<CURSOR>'})
""")

    assert {"user_id"} <= labels


def test_multiple_path_param_completions_in_incomplete_params_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.put('/teams/{team_id}/members/{user_id}')(params={'<CURSOR>'})
""")

    assert {"team_id", "user_id"} <= labels


def test_post_path_param_completions_in_incomplete_params_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.post('/users/{user_id}/posts/{post_id}/comments')(params={'<CURSOR>'})
""")

    assert {"user_id", "post_id"} <= labels


def test_query_completions_in_incomplete_query_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.get('/users')(query={'<CURSOR>'})
""")

    assert {"tenant", "page", "search", "filter[status]"} <= labels


def test_header_completions_in_incomplete_headers_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.get('/users/{user_id}')(headers={'<CURSOR>'})
""")

    assert {"X-Trace-Id", "X-Client-Version"} <= labels


def test_body_completions_in_incomplete_body_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.post('/users')(body={'<CURSOR>'})
""")

    assert {"name", "email", "role", "address"} <= labels


def test_nested_body_completions_in_incomplete_body_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import Client

client = Client(base_url='https://example.test')

client.post('/users')(body={
    'name': 'Ada',
    'email': 'a@example.test',
    'address': {'<CURSOR>'},
})
""")

    assert {"street", "city", "postal_code"} <= labels


def test_async_patch_body_completions_in_incomplete_body_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client import AsyncClient

client = AsyncClient(base_url='https://example.test')

client.patch('/users/{user_id}')(body={'<CURSOR>'})
""")

    assert {"name", "email", "address"} <= labels


def test_query_completions_in_generated_typed_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client.types import GET_UsersQuery

query: GET_UsersQuery = {'<CURSOR>'}
""")

    assert {"tenant", "page", "search", "filter[status]"} <= labels


def test_body_completions_in_generated_typed_dict(
    ty_server: CompletionServer,
) -> None:
    labels = ty_server.completion_labels("""
from generated.my_client.types import UserCreate

body: UserCreate = {'<CURSOR>'}
""")

    assert {"name", "email", "role", "address"} <= labels
