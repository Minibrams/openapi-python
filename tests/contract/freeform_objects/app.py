from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class TaskExecutionDto(BaseModel):
    id: int
    log: list[dict[str, Any]]
    metadata: dict[str, object]


@app.get("/task-executions/{task_id}", response_model=TaskExecutionDto)
def get_task_execution(task_id: int) -> TaskExecutionDto:
    return TaskExecutionDto(
        id=task_id,
        log=[{"message": "started", "attempt": 1}],
        metadata={"trigger": "manual", "dry_run": False},
    )
