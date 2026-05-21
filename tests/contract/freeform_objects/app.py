from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class TaskExecutionDto(BaseModel):
    id: int
    task_id: int
    finished_at: datetime | None
    log: list[dict[str, Any]]
    result: int | None
    output: dict | None
    should_retry: bool
    stacktrace: dict | None


class TaskDto(BaseModel):
    id: int
    state: int
    queue_id: int
    n_attempts: int
    meta: dict | None
    payload: dict
    enqueued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    pipeline_execution_id: int | None = None
    pipeline_node_id: int | None = None
    executions: list[TaskExecutionDto] | None = None


class DeploymentConfigRequest(BaseModel):
    config: dict
    franck_submission_id: str | None = None


@app.get("/tasks", response_model=list[TaskDto])
def list_tasks() -> list[TaskDto]:
    execution = TaskExecutionDto(
        id=1,
        task_id=1,
        finished_at=None,
        log=[{"message": "started", "attempt": 1}],
        result=None,
        output={"status": "ok"},
        should_retry=False,
        stacktrace=None,
    )
    return [
        TaskDto(
            id=1,
            state=1,
            queue_id=1,
            n_attempts=1,
            meta=None,
            payload={"operation": "deploy"},
            enqueued_at=datetime(2026, 1, 1),
            started_at=None,
            finished_at=None,
            executions=[execution],
        )
    ]


@app.post("/deployment-configs", response_model=DeploymentConfigRequest)
def create_deployment_config(body: DeploymentConfigRequest) -> DeploymentConfigRequest:
    return body
