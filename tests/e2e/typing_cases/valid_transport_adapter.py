from __future__ import annotations

from my_client import Client


class GoodAdapter:
    def request(self, *, method, route, base_url, params, query, headers, body):
        return {"id": "1", "name": "x", "address": "y", "isActive": True}


Client(base_url="http://example", transport=GoodAdapter())
