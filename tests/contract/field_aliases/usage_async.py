from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import AliasRecord

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    record = await async_client.get("/aliases/{record_id}")(params={"record_id": 1})
    assert_type(record, AliasRecord)
    assert_type(record["requestId"], str)
    assert_type(record["traceId"], str)

    body: AliasRecord = {"requestId": "req_123", "traceId": "trace_123"}
    created = await async_client.post("/aliases")(body=body)
    assert_type(created, AliasRecord)
    assert_type(created["requestId"], str)
    assert_type(created["traceId"], str)
