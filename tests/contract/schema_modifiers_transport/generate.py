from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from openapi_python.generator import GenerationRequest, generate_client

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Schema modifiers and transport", "version": "1.0.0"},
    "paths": {
        "/edge": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Edge"}
                            }
                        }
                    }
                }
            }
        },
        "/files/{name}": {
            "post": {
                "parameters": [
                    {
                        "name": "name",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "tag",
                        "in": "query",
                        "schema": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    {
                        "name": "enabled",
                        "in": "query",
                        "schema": {"type": "boolean"},
                    },
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                    },
                                },
                                "required": ["description", "file"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"ok": {"type": "boolean"}},
                                    "required": ["ok"],
                                }
                            }
                        }
                    }
                },
            }
        },
        "/plain": {
            "get": {
                "responses": {
                    "200": {"content": {"text/plain": {"schema": {"type": "string"}}}}
                }
            }
        },
    },
    "components": {
        "schemas": {
            "NamedThing": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
            "Edge": {
                "type": "object",
                "properties": {
                    "maybe_status": {
                        "type": "string",
                        "enum": ["ok", "failed"],
                        "nullable": True,
                    },
                    "inline_union": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "kind": {"const": "small"},
                                    "count": {"type": "integer"},
                                },
                                "required": ["kind", "count"],
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "kind": {"const": "large"},
                                    "name": {"type": "string"},
                                },
                                "required": ["kind", "name"],
                            },
                        ],
                        "nullable": True,
                    },
                    "const_nullable": {"const": "fixed", "nullable": True},
                    "ref_nullable": {
                        "$ref": "#/components/schemas/NamedThing",
                        "nullable": True,
                    },
                },
                "required": [
                    "maybe_status",
                    "inline_union",
                    "const_nullable",
                    "ref_nullable",
                ],
            },
        }
    },
}


class _Response:
    def __init__(
        self,
        *,
        content: bytes,
        headers: dict[str, str],
        json_body: object = None,
        text: str = "",
    ) -> None:
        self.content = content
        self.headers = headers
        self._json_body = json_body
        self.text = text

    def raise_for_status(self) -> None:
        pass

    def json(self) -> object:
        return self._json_body


class _HttpClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> _Response:
        self.requests.append(kwargs)
        if str(kwargs["url"]).endswith("/plain"):
            return _Response(
                content=b"ready",
                headers={"content-type": "text/plain; charset=utf-8"},
                text="ready",
            )
        return _Response(
            content=b'{"ok":true}',
            headers={"content-type": "application/json"},
            json_body={"ok": True},
        )


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=Path(__file__).parent / "generated",
            spec_json=json.dumps(SPEC),
            overwrite=True,
        )
    )

    from generated.my_client import Client, DefaultTransport

    http_client = _HttpClient()
    client = Client(
        base_url="http://testserver",
        transport=DefaultTransport(client=cast(Any, http_client)),
    )

    uploaded = client.post("/files/{name}")(
        params={"name": "a/b c"},
        query={"tag": ["one", "two"], "enabled": True},
        body={"description": "avatar", "file": b"content"},
    )
    assert uploaded == {"ok": True}

    request = http_client.requests[-1]
    assert request["url"] == "http://testserver/files/a%2Fb%20c"
    assert request["params"] == [
        ("tag", "one"),
        ("tag", "two"),
        ("enabled", "True"),
    ]
    assert request["data"] == {"description": "avatar"}
    assert request["files"] == {"file": ("file", b"content")}
    assert "json" not in request

    assert client.get("/plain")() == "ready"


if __name__ == "__main__":
    main()
