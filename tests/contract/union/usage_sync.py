from __future__ import annotations

from typing import Any, assert_type

from generated.my_client import Client
from generated.my_client.types import (
    GET_Lookup_ValueParams,
    LookupResult,
)

client = Client(base_url="http://testserver")


int_params: GET_Lookup_ValueParams = {"value": 1}
str_params: GET_Lookup_ValueParams = {"value": "abc"}

int_value: int | str = int_params["value"]
str_value: int | str = str_params["value"]

int_result = client.get("/lookup/{value}")(params=int_params)
assert_type(int_result, LookupResult)
assert_type(int_result["value"], int | str | dict[str, Any])

str_result = client.get("/lookup/{value}")(params=str_params)
assert_type(str_result, LookupResult)
assert_type(str_result["value"], int | str | dict[str, Any])
