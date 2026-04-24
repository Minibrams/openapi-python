from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import OddNames

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    record = await async_client.get("/odd-names")()
    assert_type(record, OddNames)
    assert_type(record["class"], str)
    assert_type(record["from"], str)
    assert_type(record["user-id"], int)
    assert_type(record["123value"], bool)

    body: OddNames = {
        "class": "primary",
        "from": "service",
        "user-id": 123,
        "123value": True,
    }
    created = await async_client.post("/odd-names")(body=body)
    assert_type(created, OddNames)
    assert_type(created["class"], str)
    assert_type(created["from"], str)
    assert_type(created["user-id"], int)
    assert_type(created["123value"], bool)
