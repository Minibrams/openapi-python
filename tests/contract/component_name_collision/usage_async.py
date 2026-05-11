from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import FooBar, FooBar2

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    hyphen = await async_client.get("/hyphen")()
    assert_type(hyphen, FooBar)
    assert_type(hyphen["hyphen"], str)

    underscore = await async_client.get("/underscore")()
    assert_type(underscore, FooBar2)
    assert_type(underscore["underscore"], int)
