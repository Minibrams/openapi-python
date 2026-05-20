from __future__ import annotations

from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class PipelineName(str, Enum):
    create_sdwan = "create-sdwan"
    test_pipeline = "test-pipeline"
    deploy_sdwan_spoke = "deploy-sdwan-spoke"
    deploy_sdwan_customer_hub = "deploy-sdwan-customer-hub"
    deploy_cisco_access_switch = "deploy-cisco-access-switch"


class PipelineExecution(BaseModel):
    name: PipelineName
    id: int


@app.get("/api/v1/pipelines/{name}/executions/{id}", response_model=PipelineExecution)
def get_pipeline_execution(name: PipelineName, id: int) -> PipelineExecution:
    return PipelineExecution(name=name, id=id)
