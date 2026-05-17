from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import RouteLiteral

client = Client(base_url="http://testserver")

route: RouteLiteral = "/anything"
result = client.get(route)(params={"book_id": "not tied to an operation"})
assert_type(result, object)
