from __future__ import annotations

from openapi_python.generator.normalize import normalize_openapi


def test_component_names_get_unique_type_names_when_pascal_case_collides() -> None:
    document = {
        "openapi": "3.1.0",
        "paths": {
            "/hyphen": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/foo-bar"}
                                }
                            }
                        }
                    }
                }
            },
            "/underscore": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/foo_bar"}
                                }
                            }
                        }
                    }
                }
            },
        },
        "components": {
            "schemas": {
                "foo-bar": {
                    "type": "object",
                    "properties": {"hyphen": {"type": "string"}},
                    "required": ["hyphen"],
                },
                "foo_bar": {
                    "type": "object",
                    "properties": {"underscore": {"type": "integer"}},
                    "required": ["underscore"],
                },
            }
        },
    }

    normalized = normalize_openapi(document, "client")

    typed_dicts = {item.name: item for item in normalized.typed_dicts}
    assert set(typed_dicts) == {"FooBar", "FooBar2"}
    assert typed_dicts["FooBar"].fields[0].name == "hyphen"
    assert typed_dicts["FooBar2"].fields[0].name == "underscore"

    response_types = {
        operation.route_literal: operation.response_type
        for operation in normalized.operations
    }
    assert response_types == {
        "/hyphen": "FooBar",
        "/underscore": "FooBar2",
    }
