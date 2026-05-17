from __future__ import annotations

import json
from pathlib import Path

from openapi_python.generator import GenerationRequest, generate_client

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Type order", "version": "1.0.0"},
    "paths": {
        "/owners": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Owner"}
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Owner": {
                "oneOf": [
                    {"$ref": "#/components/schemas/Person"},
                    {"$ref": "#/components/schemas/Team"},
                ]
            },
            "Person": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "Team": {
                "type": "object",
                "properties": {"slug": {"type": "string"}},
                "required": ["slug"],
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
