from __future__ import annotations

from typing import assert_type

from generated.my_client import Client

client = Client(base_url="http://testserver")

deleted = client.delete("/items/{item_id}")(params={"item_id": 1})
assert_type(deleted, None)

cancelled = client.post("/jobs/{job_id}/cancel")(params={"job_id": 1})
assert_type(cancelled, None)
