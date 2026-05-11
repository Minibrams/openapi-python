from __future__ import annotations

import json
from pathlib import Path

from openapi_python.generator import GenerationRequest, generate_client

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Component name collision", "version": "1.0.0"},
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


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=Path(__file__).parent / "generated",
            spec_json=json.dumps(SPEC),
            overwrite=True,
        )
    )


if __name__ == "__main__":
    main()
