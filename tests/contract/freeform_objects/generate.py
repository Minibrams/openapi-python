from __future__ import annotations

import importlib
import json
from pathlib import Path

from app import app
from fastapi import FastAPI

from openapi_python.generator import GenerationRequest, generate_client


def main() -> None:
    output_dir = Path(__file__).parent / "generated"
    generate_client(
        GenerationRequest(
            output_dir=output_dir,
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )

    source = (output_dir / "my_client" / "types.py").read_text()
    assert "class TaskExecutionDtoLogItem(TypedDict):" not in source
    assert "log: list[dict[str, Any]]" in source
    assert "metadata: dict[str, Any]" in source

    generated_types = importlib.import_module("generated.my_client.types")
    api_b = FastAPI()

    def get_task_execution() -> object:
        return {}

    api_b.get(
        "/task-executions/{task_id}",
        response_model=generated_types.TaskExecutionDto,
    )(get_task_execution)

    schema = api_b.openapi()["components"]["schemas"]["TaskExecutionDto"]
    log_items = schema["properties"]["log"]["items"]
    metadata = schema["properties"]["metadata"]
    assert log_items["type"] == "object"
    assert log_items["additionalProperties"] is True
    assert metadata["type"] == "object"
    assert metadata["additionalProperties"] is True


if __name__ == "__main__":
    main()
