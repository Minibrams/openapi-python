from __future__ import annotations

from typing import Any, assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import TaskExecutionDto

client = AsyncClient(base_url="http://testserver")


async def main() -> None:
    result = await client.get("/task-executions/{task_id}")(params={"task_id": 1})
    assert_type(result, TaskExecutionDto)
    assert_type(result["log"], list[dict[str, Any]])
    assert_type(result["metadata"], dict[str, Any])
