from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    deleted = await async_client.delete("/items/{item_id}")(params={"item_id": 1})
    assert_type(deleted, None)

    cancelled = await async_client.post("/jobs/{job_id}/cancel")(params={"job_id": 1})
    assert_type(cancelled, None)
