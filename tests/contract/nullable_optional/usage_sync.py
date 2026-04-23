from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import NullableRecord

client = Client(base_url="http://testserver")

record = client.get("/records/{record_id}")(params={"record_id": 1})
assert_type(record, NullableRecord)
assert_type(record["id"], int)
assert_type(record["required_nullable"], str | None)
assert_type(record.get("optional_note"), str | None)
assert_type(record.get("optional_count"), int | None)
assert_type(record.get("tags"), list[str] | None)
