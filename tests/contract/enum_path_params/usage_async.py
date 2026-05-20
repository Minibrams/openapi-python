from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import PipelineExecution, PipelineName

client = AsyncClient(base_url="http://testserver")


async def main() -> None:
    result = await client.get("/api/v1/pipelines/{name}/executions/{id}")(
        params={
            "name": PipelineName.DEPLOY_CISCO_ACCESS_SWITCH.value,
            "id": 1,
        }
    )
    assert_type(result, PipelineExecution)
    assert_type(result["name"], PipelineName)
    assert_type(result["id"], int)
