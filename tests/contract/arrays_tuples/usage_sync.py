from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import ArrayShapes, Item

client = Client(base_url="http://testserver")

result = client.get("/array-shapes")()
assert_type(result, ArrayShapes)
assert_type(result["tags"], list[str])
assert_type(result["matrix"], list[list[int]])
assert_type(result["items"], list[Item])
assert_type(result["pair"], tuple[str, int])
