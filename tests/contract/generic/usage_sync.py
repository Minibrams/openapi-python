from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import EnvelopeItem, EnvelopePageItem, Item, PageItem

client = Client(base_url="http://testserver")

items = client.get("/items")()
assert_type(items, PageItem)
assert_type(items["items"], list[Item])
assert_type(items["items"][0]["id"], int)
assert_type(items["items"][0]["name"], str)
assert_type(items["total"], int)

item = client.get("/items/{item_id}")(params={"item_id": 1})
assert_type(item, EnvelopeItem)
assert_type(item["data"], Item)
assert_type(item["data"]["id"], int)
assert_type(item["request_id"], str)

search_result = client.post("/items/search")(
    body={"filters": {"id": 1, "name": "alpha"}, "limit": 10}
)
assert_type(search_result, EnvelopePageItem)
assert_type(search_result["data"], PageItem)
assert_type(search_result["data"]["items"], list[Item])
assert_type(search_result["data"]["items"][0]["name"], str)
assert_type(search_result["request_id"], str)
