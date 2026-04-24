from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import CreatedWidget, Widget, WidgetCreate

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    body: WidgetCreate = {"name": "alpha"}
    result = await async_client.post("/widgets")(body=body)
    assert_type(result, Widget | CreatedWidget)
