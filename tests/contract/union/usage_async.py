from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import (
    GET_Lookup_ValueParams,
    LookupResult,
    LookupResultValueVariant,
)

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    int_params: GET_Lookup_ValueParams = {"value": 1}
    str_params: GET_Lookup_ValueParams = {"value": "abc"}

    assert_type(int_params["value"], int | str)
    assert_type(str_params["value"], int | str)

    int_result = await async_client.get("/lookup/{value}")(params=int_params)
    assert_type(int_result, LookupResult)
    assert_type(int_result["value"], int | str | LookupResultValueVariant)

    str_result = await async_client.get("/lookup/{value}")(params=str_params)
    assert_type(str_result, LookupResult)
    assert_type(str_result["value"], int | str | LookupResultValueVariant)
