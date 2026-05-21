from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict, assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import DeploymentConfigRequest, TaskDto, TaskExecutionDto

client = AsyncClient(base_url="http://testserver")


async def main() -> None:
    result = await client.get("/tasks")()
    assert_type(result, list[TaskDto])
    task = result[0]
    assert_type(task["meta"], Mapping[str, Any] | None)
    assert_type(task["payload"], Mapping[str, Any])
    assert_type(task["executions"], list[TaskExecutionDto] | None)
    execution = task["executions"][0] if task["executions"] is not None else None
    assert_type(execution, TaskExecutionDto | None)
    if execution is not None:
        assert_type(execution["log"], list[Mapping[str, Any]])
        assert_type(execution["output"], Mapping[str, Any] | None)
        assert_type(execution["stacktrace"], Mapping[str, Any] | None)


class FortigateSDWANSpokeConfig(TypedDict):
    hostname: str
    serial_number: str


async def create_deployment_config() -> None:
    config: FortigateSDWANSpokeConfig = {
        "hostname": "fw01",
        "serial_number": "FGT123",
    }
    body: DeploymentConfigRequest = {
        "config": config,
        "franck_submission_id": None,
    }
    created = await client.post("/deployment-configs")(body=body)
    assert_type(created, DeploymentConfigRequest)
