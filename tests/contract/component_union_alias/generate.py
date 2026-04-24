from __future__ import annotations

import json
from pathlib import Path

from openapi_python.generator import GenerationRequest, generate_client

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Component union alias", "version": "1.0.0"},
    "paths": {
        "/check": {
            "post": {
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UserFGACheckRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserFGACheckRequest"
                                }
                            }
                        }
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "FGAObjectType": {
                "anyOf": [
                    {"type": "string", "enum": ["user", "sensor", "organization"]},
                    {"type": "string"},
                ]
            },
            "FGARelation": {
                "anyOf": [
                    {"type": "string", "enum": ["owner", "member", "can_read"]},
                    {"type": "string"},
                ]
            },
            "UserFGACheckRequest": {
                "type": "object",
                "properties": {
                    "relation": {"$ref": "#/components/schemas/FGARelation"},
                    "object_type": {"$ref": "#/components/schemas/FGAObjectType"},
                    "object_id": {"type": "string"},
                },
                "required": ["relation", "object_type", "object_id"],
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
