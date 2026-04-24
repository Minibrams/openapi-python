from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import OddNames

client = Client(base_url="http://testserver")

record = client.get("/odd-names")()
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
created = client.post("/odd-names")(body=body)
assert_type(created, OddNames)
assert_type(created["class"], str)
assert_type(created["from"], str)
assert_type(created["user-id"], int)
assert_type(created["123value"], bool)
