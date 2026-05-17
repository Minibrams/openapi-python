from __future__ import annotations

import json
from pathlib import Path

from openapi_python.generator import GenerationRequest, generate_client

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Protocol Flags", "version": "1.0.0"},
    "paths": {
        "/books/{book_id}": {
            "get": {
                "parameters": [
                    {
                        "name": "book_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Book"}
                            }
                        },
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Book": {
                "type": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                },
            }
        }
    },
}


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=Path(__file__).parent / "generated",
            spec_json=json.dumps(SPEC),
            overwrite=True,
            generate_requests=False,
        )
    )


if __name__ == "__main__":
    main()
