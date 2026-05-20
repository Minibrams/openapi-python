from __future__ import annotations

from typing import Any, assert_type

from generated.my_client import Client
from generated.my_client.types import TaskDto, TaskExecutionDto

client = Client(base_url="http://testserver")

result = client.get("/tasks")()
assert_type(result, list[TaskDto])
task = result[0]
assert_type(task["meta"], dict[str, Any] | None)
assert_type(task["payload"], dict[str, Any])
assert_type(task["executions"], list[TaskExecutionDto] | None)
execution = task["executions"][0] if task["executions"] is not None else None
assert_type(execution, TaskExecutionDto | None)
if execution is not None:
    assert_type(execution["log"], list[dict[str, Any]])
    assert_type(execution["output"], dict[str, Any] | None)
    assert_type(execution["stacktrace"], dict[str, Any] | None)
