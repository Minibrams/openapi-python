from __future__ import annotations

import importlib
import json
from pathlib import Path

from app import app
from fastapi import FastAPI

from openapi_python.generator import GenerationRequest, generate_client


def _strip_additional_properties(schema: dict) -> None:
    match schema:
        case dict():
            if schema.get("additionalProperties") is True:
                schema.pop("additionalProperties")
            for value in schema.values():
                _strip_additional_properties(value)
        case list():
            for item in schema:
                _strip_additional_properties(item)


def main() -> None:
    output_dir = Path(__file__).parent / "generated"
    spec = app.openapi()
    _strip_additional_properties(spec)
    generate_client(
        GenerationRequest(
            output_dir=output_dir,
            spec_json=json.dumps(spec),
            overwrite=True,
        )
    )

    source = (output_dir / "my_client" / "types.py").read_text()
    assert "class TaskExecutionDtoLogItem(TypedDict):" not in source
    assert "class TaskExecutionDtoOutputVariant(TypedDict):" not in source
    assert "class TaskExecutionDtoStacktraceVariant(TypedDict):" not in source
    assert "class TaskDtoMetaVariant(TypedDict):" not in source
    assert "class TaskDtoPayload(TypedDict):" not in source
    assert "log: list[dict[str, Any]]" in source
    assert "output: dict[str, Any] | None" in source
    assert "stacktrace: dict[str, Any] | None" in source
    assert "meta: dict[str, Any] | None" in source
    assert "payload: dict[str, Any]" in source
    assert "executions: NotRequired[list[TaskExecutionDto] | None]" in source

    generated_types = importlib.import_module("generated.my_client.types")
    api_b = FastAPI()

    def list_tasks() -> object:
        return []

    api_b.get("/tasks", response_model=list[generated_types.TaskDto])(list_tasks)

    schemas = api_b.openapi()["components"]["schemas"]
    task_execution = schemas["TaskExecutionDto"]
    task = schemas["TaskDto"]
    log_items = task_execution["properties"]["log"]["items"]
    output = task_execution["properties"]["output"]["anyOf"][0]
    stacktrace = task_execution["properties"]["stacktrace"]["anyOf"][0]
    meta = task["properties"]["meta"]["anyOf"][0]
    payload = task["properties"]["payload"]
    assert log_items["type"] == "object"
    assert log_items["additionalProperties"] is True
    assert output["type"] == "object"
    assert output["additionalProperties"] is True
    assert stacktrace["type"] == "object"
    assert stacktrace["additionalProperties"] is True
    assert meta["type"] == "object"
    assert meta["additionalProperties"] is True
    assert payload["type"] == "object"
    assert payload["additionalProperties"] is True


if __name__ == "__main__":
    main()
