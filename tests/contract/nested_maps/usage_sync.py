from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import Item, Shelf, Warehouse

client = Client(base_url="http://testserver")

warehouse = client.get("/warehouses/{warehouse_id}")(params={"warehouse_id": 1})
assert_type(warehouse, Warehouse)
assert_type(warehouse["shelves"], list[Shelf])
assert_type(warehouse["shelves"][0]["items"], list[Item])
assert_type(warehouse["inventory_by_sku"], dict[str, Item])
assert_type(warehouse["inventory_by_sku"]["abc"], Item)
assert_type(warehouse["metadata"], dict[str, str])
assert_type(warehouse["metadata"]["region"], str)
