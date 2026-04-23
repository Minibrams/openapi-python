from __future__ import annotations

from my_client import Client


class DummyTransport:
    def request(self, *, method, route, base_url, params, query, headers, body):
        return {"id": "1", "name": "x", "address": "y", "isActive": True}


client = Client(base_url="http://example", transport=DummyTransport())
client.put("/api/v1/users/{id}")(
    params={"id": "1"},
    body={"name": "A", "address": "Addr", "isActive": True},
)
