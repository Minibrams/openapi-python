from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import AliasRecord

client = Client(base_url="http://testserver")

record = client.get("/aliases/{record_id}")(params={"record_id": 1})
assert_type(record, AliasRecord)
assert_type(record["requestId"], str)
assert_type(record["traceId"], str)

body: AliasRecord = {"requestId": "req_123", "traceId": "trace_123"}
created = client.post("/aliases")(body=body)
assert_type(created, AliasRecord)
assert_type(created["requestId"], str)
assert_type(created["traceId"], str)
